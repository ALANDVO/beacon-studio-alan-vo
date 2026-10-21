from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class ContextPack(Base, IDMixin, TimestampMixin):
    __tablename__ = "context_packs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    generated_files: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array

    sections: Mapped[list["ContextSection"]] = relationship(back_populates="pack", cascade="all, delete-orphan")


class ContextSection(Base, IDMixin, TimestampMixin):
    __tablename__ = "context_sections"

    pack_id: Mapped[int] = mapped_column(ForeignKey("context_packs.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="")  # "interview" | "document" | "inferred"
    is_unknown: Mapped[bool] = mapped_column(nullable=False, default=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    pack: Mapped["ContextPack"] = relationship(back_populates="sections")

    __table_args__ = (
        Index("ix_sections_pack_order", "pack_id", "order"),
    )