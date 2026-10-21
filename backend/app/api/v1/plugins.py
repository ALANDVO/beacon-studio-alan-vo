from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.api.deps import get_current_user, require_role
from app.models.plugin import Plugin
from app.models.audit import AuditRun, AuditFinding
from app.models.context import ContextPack as ContextPackModel, ContextSection
from app.models.gtm import GTMOfferStack, GTMOfferLine, GTMProofAsset, GTMProofClaim
from app.services.audit import audit_skill
from app.services.context import generate_context_pack, DEFAULT_QUESTIONS
from app.services.gtm import score_offer_stack, score_proof_asset
from pydantic import BaseModel, field_validator
from typing import Optional
import json
from pathlib import Path

router = APIRouter()


class PluginBase(BaseModel):
    name: str
    description: str
    harness: str
    category: str
    tags: list[str]
    install_command: str
    author: str
    stars: int = 0

    @field_validator("harness")
    @classmethod
    def validate_harness(cls, v: str) -> str:
        valid = ["claude-code", "codex", "cursor", "opencode", "copilot", "antigravity", "pi"]
        if v.lower() not in valid:
            raise ValueError(f"Invalid harness. Must be one of: {valid}")
        return v.lower()


class PluginCreate(PluginBase):
    pass


class PluginUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    harness: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    install_command: Optional[str] = None
    author: Optional[str] = None
    stars: Optional[int] = None


class PluginResponse(PluginBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: list[PluginResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/plugins", response_model=PaginatedResponse)
async def list_plugins(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    search: Optional[str] = None,
    harness: Optional[str] = None,
    category: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    query = select(Plugin)
    count_query = select(func.count(Plugin.id))

    if search:
        search_term = f"%{search}%"
        query = query.where(Plugin.name.ilike(search_term) | Plugin.description.ilike(search_term))
        count_query = count_query.where(Plugin.name.ilike(search_term) | Plugin.description.ilike(search_term))

    if harness:
        query = query.where(Plugin.harness == harness.lower())
        count_query = count_query.where(Plugin.harness == harness.lower())

    if category:
        query = query.where(Plugin.category == category)
        count_query = count_query.where(Plugin.category == category)

    total = await session.scalar(count_query)
    total_pages = (total + page_size - 1) // page_size

    query = query.order_by(Plugin.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    plugins = result.scalars().all()

    return PaginatedResponse(
        items=[PluginResponse.model_validate(p) for p in plugins],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/plugins", response_model=PluginResponse, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    plugin: PluginCreate,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("operator")),
):
    db_plugin = Plugin(
        name=plugin.name,
        description=plugin.description,
        harness=plugin.harness.lower(),
        category=plugin.category,
        tags=json.dumps(plugin.tags),
        install_command=plugin.install_command,
        author=plugin.author,
        stars=plugin.stars,
    )
    session.add(db_plugin)
    await session.flush()
    await session.refresh(db_plugin)
    return PluginResponse.model_validate(db_plugin)


@router.get("/plugins/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    plugin_id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    result = await session.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return PluginResponse.model_validate(plugin)


@router.put("/plugins/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    plugin_id: int,
    plugin: PluginUpdate,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("operator")),
):
    result = await session.execute(select(Plugin).where(Plugin.id == plugin_id))
    db_plugin = result.scalar_one_or_none()
    if not db_plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    update_data = plugin.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"])
    if "harness" in update_data:
        update_data["harness"] = update_data["harness"].lower()

    for key, value in update_data.items():
        setattr(db_plugin, key, value)

    await session.flush()
    await session.refresh(db_plugin)
    return PluginResponse.model_validate(db_plugin)


@router.delete("/plugins/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin(
    plugin_id: int,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("admin")),
):
    result = await session.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    await session.delete(plugin)


class AuditRequest(BaseModel):
    path: str


class AuditFindingResponse(BaseModel):
    severity: str
    code: str
    file: str
    line: int
    message: str
    suggested_fix: str
    confidence: float


class AuditResponse(BaseModel):
    skill_name: str
    skill_path: str
    context_cost_estimate: int
    findings: list[AuditFindingResponse]
    missing_files: list[str]
    overlapping_descriptions: list[str]
    vague_descriptions: list[str]


@router.post("/audit/scan", response_model=AuditResponse)
async def scan_skills(
    request: AuditRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("operator")),
):
    skill_dir = Path(request.path)
    if not skill_dir.exists():
        raise HTTPException(status_code=400, detail="Path does not exist")

    # Run audit
    result = audit_skill(skill_dir)

    # Save to database
    audit_run = AuditRun(
        path=str(skill_dir),
        total_skills=1,
        total_findings=len(result.findings),
        high_severity=len([f for f in result.findings if f.severity == "high"]),
        medium_severity=len([f for f in result.findings if f.severity == "medium"]),
        low_severity=len([f for f in result.findings if f.severity == "low"]),
        info_severity=len([f for f in result.findings if f.severity == "info"]),
        status="completed",
    )
    session.add(audit_run)
    await session.flush()

    for finding in result.findings:
        db_finding = AuditFinding(
            run_id=audit_run.id,
            severity=finding.severity,
            code=finding.code,
            file_path=finding.file,
            line=finding.line,
            message=finding.message,
            suggested_fix=finding.suggested_fix,
            confidence=finding.confidence,
        )
        session.add(db_finding)

    return AuditResponse(
        skill_name=result.skill_name,
        skill_path=result.skill_path,
        context_cost_estimate=result.context_cost_estimate,
        findings=[AuditFindingResponse.model_validate(f) for f in result.findings],
        missing_files=result.missing_files,
        overlapping_descriptions=result.overlapping_descriptions,
        vague_descriptions=result.vague_descriptions,
    )


@router.get("/audit/history", response_model=list[dict])
async def audit_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    query = select(AuditRun).order_by(AuditRun.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    runs = result.scalars().all()

    return [
        {
            "id": r.id,
            "path": r.path,
            "total_skills": r.total_skills,
            "total_findings": r.total_findings,
            "high_severity": r.high_severity,
            "medium_severity": r.medium_severity,
            "low_severity": r.low_severity,
            "info_severity": r.info_severity,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]


class ContextPackRequest(BaseModel):
    answers: dict[str, str]


class ContextSectionResponse(BaseModel):
    title: str
    content: str
    source: str
    is_unknown: bool


class ContextPackResponse(BaseModel):
    name: str
    company_name: str
    description: str
    sections: list[ContextSectionResponse]
    files: list[str]


@router.post("/context/generate", response_model=ContextPackResponse)
async def generate_context(
    request: ContextPackRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("operator")),
):
    pack = generate_context_pack(request.answers)

    # Save to database
    db_pack = ContextPackModel(
        name=pack.name,
        company_name=pack.company_name,
        description=pack.description,
        status="completed",
        generated_files=json.dumps([]),
    )
    session.add(db_pack)
    await session.flush()

    for i, section in enumerate(pack.sections):
        db_section = ContextSection(
            pack_id=db_pack.id,
            title=section.title,
            content=section.content,
            source=section.source,
            is_unknown=section.is_unknown,
            order=i,
        )
        session.add(db_section)

    # Write files
    output_dir = Path("context_packs") / str(db_pack.id)
    files = pack.to_files(output_dir)

    db_pack.generated_files = json.dumps(files)
    await session.flush()

    return ContextPackResponse(
        name=pack.name,
        company_name=pack.company_name,
        description=pack.description,
        sections=[ContextSectionResponse.model_validate(s) for s in pack.sections],
        files=files,
    )


@router.get("/context/questions", response_model=list[dict])
async def get_context_questions(
    user=Depends(get_current_user),
):
    return DEFAULT_QUESTIONS


class OfferStackRequest(BaseModel):
    content: str


class OfferStackResponse(BaseModel):
    overall_score: float
    lines: list[dict]


@router.post("/gtm/score-offer", response_model=OfferStackResponse)
async def score_offer(
    request: OfferStackRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("operator")),
):
    result = score_offer_stack(request.content)

    # Save
    db_stack = GTMOfferStack(
        name=f"Offer Stack {len(request.content)} chars",
        raw_content=request.content,
        overall_score=result.overall_score,
        status="completed",
    )
    session.add(db_stack)
    await session.flush()

    for line in result.lines:
        db_line = GTMOfferLine(
            stack_id=db_stack.id,
            line_number=line.line_number,
            content=line.content,
            has_pain_point=line.has_pain_point,
            pain_point=line.pain_point,
            score=line.score,
            reasoning=line.reasoning,
        )
        session.add(db_line)

    return OfferStackResponse(
        overall_score=result.overall_score,
        lines=[line.__dict__ for line in result.lines],
    )


class ProofAssetRequest(BaseModel):
    content: str


class ProofAssetResponse(BaseModel):
    overall_score: float
    claims: list[dict]


@router.post("/gtm/score-proof", response_model=ProofAssetResponse)
async def score_proof(
    request: ProofAssetRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_role("operator")),
):
    result = score_proof_asset(request.content)

    # Save
    db_asset = GTMProofAsset(
        name=f"Proof Asset {len(request.content)} chars",
        raw_content=request.content,
        overall_score=result.overall_score,
        status="completed",
    )
    session.add(db_asset)
    await session.flush()

    for claim in result.claims:
        db_claim = GTMProofClaim(
            asset_id=db_asset.id,
            claim_number=claim.claim_number,
            content=claim.content,
            has_source=claim.has_source,
            source=claim.source,
            has_permission=claim.has_permission,
            score=claim.score,
            reasoning=claim.reasoning,
        )
        session.add(db_claim)

    return ProofAssetResponse(
        overall_score=result.overall_score,
        claims=[claim.__dict__ for claim in result.claims],
    )


class MCPToolRequest(BaseModel):
    query: str
    max_results: int = 10


class MCPToolResponse(BaseModel):
    tools: list[dict]


@router.post("/gtm/pick-tools", response_model=MCPToolResponse)
async def pick_gtm_tools(
    request: MCPToolRequest,
    user=Depends(require_role("operator")),
):
    # This would call the MCP server at https://thegtmdirectory.com/api/mcp
    # For now, return a mock response
    return MCPToolResponse(
        tools=[
            {
                "name": "GTM Tool 1",
                "description": "A tool for GTM workflows",
                "category": "analysis",
                "source": "thegtmdirectory.com",
            }
        ]
    )