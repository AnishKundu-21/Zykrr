"""SQLAlchemy ORM model for support tickets."""
import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # JSON-serialised lists stored as text
    keywords: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    custom_flags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Convenience helpers so callers get Python lists, not raw JSON strings
    def get_keywords(self) -> list[str]:
        return json.loads(self.keywords)

    def get_custom_flags(self) -> list[str]:
        return json.loads(self.custom_flags)
