from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class SkillFinding:
    severity: str  # "high", "medium", "low", "info"
    code: str
    file: str
    line: int
    message: str
    suggested_fix: str
    confidence: float


@dataclass
class SkillAuditResult:
    skill_name: str
    skill_path: str
    context_cost_estimate: int  # approximate tokens
    findings: list[SkillFinding]
    missing_files: list[str]
    overlapping_descriptions: list[str]
    vague_descriptions: list[str]


def parse_skill_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from SKILL.md."""
    if not content.startswith("---"):
        return {}
    try:
        _, fm, _ = content.split("---", 2)
        return yaml.safe_load(fm) or {}
    except Exception:
        return {}


def estimate_context_cost(frontmatter: dict, body: str) -> int:
    """Estimate token cost for skill context."""
    base = 500
    if frontmatter.get("description"):
        base += len(frontmatter["description"]) // 4
    if frontmatter.get("allowed-tools"):
        base += len(frontmatter["allowed-tools"].split()) * 50
    body_tokens = len(body) // 4
    return base + body_tokens


def check_missing_files(skill_path: Path, frontmatter: dict) -> list[str]:
    """Check for referenced files that don't exist."""
    missing = []
    scripts = frontmatter.get("scripts", [])
    for script in scripts:
        script_path = skill_path / script
        if not script_path.exists():
            missing.append(str(script_path))
    return missing


def audit_skill(skill_dir: Path) -> SkillAuditResult:
    """Audit a single skill directory."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return SkillAuditResult(
            skill_name=skill_dir.name,
            skill_path=str(skill_dir),
            context_cost_estimate=0,
            findings=[],
            missing_files=[str(skill_md)],
            overlapping_descriptions=[],
            vague_descriptions=[],
        )

    content = skill_md.read_text(encoding="utf-8")
    frontmatter = parse_skill_frontmatter(content)
    body = content.split("---", 2)[-1] if content.startswith("---") else content

    context_cost = estimate_context_cost(frontmatter, body)
    missing = check_missing_files(skill_dir, frontmatter)

    findings: list[SkillFinding] = []
    vague: list[str] = []
    overlapping: list[str] = []

    desc = frontmatter.get("description", "")
    if not desc or len(desc) < 50:
        vague.append("Description too short or missing (< 50 chars)")

    allowed = frontmatter.get("allowed-tools", "")
    if not allowed:
        findings.append(SkillFinding(
            severity="medium",
            code="SKILL-001",
            file=str(skill_md),
            line=1,
            message="No allowed-tools specified; skill may request unlimited tools",
            suggested_fix="Add allowed-tools frontmatter with space-delimited tool names",
            confidence=0.8,
        ))

    return SkillAuditResult(
        skill_name=frontmatter.get("name", skill_dir.name),
        skill_path=str(skill_dir),
        context_cost_estimate=context_cost,
        findings=findings,
        missing_files=missing,
        overlapping_descriptions=overlapping,
        vague_descriptions=vague,
    )