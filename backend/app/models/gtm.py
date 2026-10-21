from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class GTMOfferStack(Base, IDMixin, TimestampMixin):
    __tablename__ = "gtm_offer_stacks"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    lines: Mapped[list["GTMOfferLine"]] = relationship(back_populates="stack", cascade="all, delete-orphan")


class GTMOfferLine(Base, IDMixin, TimestampMixin):
    __tablename__ = "gtm_offer_lines"

    stack_id: Mapped[int] = mapped_column(ForeignKey("gtm_offer_stacks.id"), nullable=False, index=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    has_pain_point: Mapped[bool] = mapped_column(nullable=False, default=False)
    pain_point: Mapped[str] = mapped_column(Text, nullable=False, default="")
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")

    stack: Mapped["GTMOfferStack"] = relationship(back_populates="lines")


class GTMProofAsset(Base, IDMixin, TimestampMixin):
    __tablename__ = "gtm_proof_assets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    claims: Mapped[list["GTMProofClaim"]] = relationship(back_populates="asset", cascade="all, delete-orphan")


class GTMProofClaim(Base, IDMixin, TimestampMixin):
    __tablename__ = "gtm_proof_claims"

    asset_id: Mapped[int] = mapped_column(ForeignKey("gtm_proof_assets.id"), nullable=False, index=True)
    claim_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    has_source: Mapped[bool] = mapped_column(nullable=False, default=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="")
    has_permission: Mapped[bool] = mapped_column(nullable=False, default=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")

    asset: Mapped["GTMProofAsset"] = relationship(back_populates="claims")