from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class AuditRun(Base, IDMixin, TimestampMixin):
    __tablename__ = "audit_runs"

    path: Mapped[str] = mapped_column(String(500), nullable=False)
    total_skills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_findings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_severity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medium_severity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_severity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    info_severity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    findings: Mapped[list["AuditFinding"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class AuditFinding(Base, IDMixin, TimestampMixin):
    __tablename__ = "audit_findings"

    run_id: Mapped[int] = mapped_column(ForeignKey("audit_runs.id"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    run: Mapped["AuditRun"] = relationship(back_populates="findings")

    __table_args__ = (
        Index("ix_findings_run_severity", "run_id", "severity"),
        Index("ix_findings_code", "code"),
    )