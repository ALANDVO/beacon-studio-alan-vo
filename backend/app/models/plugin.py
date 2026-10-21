from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class Plugin(Base, IDMixin, TimestampMixin):
    __tablename__ = "plugins"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    harness: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array
    install_command: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_plugins_harness_category", "harness", "category"),
        Index("ix_plugins_search", "name", "description"),
    )

    def tags_list(self) -> list[str]:
        import json
        try:
            return json.loads(self.tags)
        except Exception:
            return []

    def set_tags(self, tags: list[str]) -> None:
        import json
        self.tags = json.dumps(tags)