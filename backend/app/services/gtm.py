from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class OfferLineResult:
    line_number: int
    content: str
    has_pain_point: bool
    pain_point: str
    score: float
    reasoning: str


@dataclass
class OfferStackResult:
    overall_score: float
    lines: list[OfferLineResult]


def score_offer_stack(content: str) -> OfferStackResult:
    """Score an offer stack - each line must have a pain point behind it."""
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    results = []

    pain_keywords = [
        "pain", "problem", "struggle", "frustrat", "difficult", "hard", "slow",
        "waste", "inefficient", "manual", "error", "fail", "broken", "missing",
        "lack", "need", "want", "require", "challenge", "issue", "bottleneck",
        "overwhelm", "burnout", "costly", "expensive", "time-consuming",
    ]

    for i, line in enumerate(lines):
        has_pain = False
        pain_point = ""
        reasoning = ""
        score = 0.0

        line_lower = line.lower()
        for kw in pain_keywords:
            if kw in line_lower:
                has_pain = True
                pain_point = kw
                break

        if has_pain:
            score = 0.8
            reasoning = f"Found pain indicator: '{pain_point}'"
        else:
            score = 0.1
            reasoning = "No clear pain point detected in this line"

        results.append(OfferLineResult(
            line_number=i + 1,
            content=line,
            has_pain_point=has_pain,
            pain_point=pain_point,
            score=score,
            reasoning=reasoning,
        ))

    overall = sum(r.score for r in results) / len(results) if results else 0.0
    return OfferStackResult(overall_score=overall, lines=results)


@dataclass
class ProofClaimResult:
    claim_number: int
    content: str
    has_source: bool
    source: str
    has_permission: bool
    score: float
    reasoning: str


@dataclass
class ProofAssetResult:
    overall_score: float
    claims: list[ProofClaimResult]


def score_proof_asset(content: str) -> ProofAssetResult:
    """Score proof assets - each claim must have source and permission."""
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    results = []

    source_patterns = [
        r"(source:|ref:|reference:|according to|citation:|\[[\d\]]+)",
        r"(https?://|doi:|arxiv:|isbn:)",
        r"(customer|client|user).*said|reported|shared|told",
        r"(case study|testimonial|review|survey|study).*shows",
    ]

    permission_keywords = [
        "permission", "authorized", "approved", "consent", "allowed",
        "public", "published", "anonymized", "aggregated",
    ]

    for i, line in enumerate(lines):
        has_source = False
        source = ""
        has_permission = False
        reasoning = ""
        score = 0.0

        line_lower = line.lower()

        for pattern in source_patterns:
            if re.search(pattern, line_lower):
                has_source = True
                source = "detected via pattern"
                break

        for kw in permission_keywords:
            if kw in line_lower:
                has_permission = True
                break

        if has_source and has_permission:
            score = 0.9
            reasoning = "Has both source attribution and permission indicator"
        elif has_source:
            score = 0.5
            reasoning = "Has source attribution but no clear permission indicator"
        elif has_permission:
            score = 0.3
            reasoning = "Has permission indicator but no clear source"
        else:
            score = 0.1
            reasoning = "No source attribution or permission indicator detected"

        results.append(ProofClaimResult(
            claim_number=i + 1,
            content=line,
            has_source=has_source,
            source=source,
            has_permission=has_permission,
            score=score,
            reasoning=reasoning,
        ))

    overall = sum(r.score for r in results) / len(results) if results else 0.0
    return ProofAssetResult(overall_score=overall, claims=results)