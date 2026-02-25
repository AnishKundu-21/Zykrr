"""Pydantic request/response schemas."""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator


class TicketRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=300, description="Ticket subject / title")
    description: str = Field(..., min_length=1, max_length=5000, description="Ticket body text")

    @field_validator("subject", "description", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class TicketResponse(BaseModel):
    id: int
    subject: str
    description: str
    category: str
    priority: str
    urgency: bool
    confidence: float
    keywords: List[str]
    custom_flags: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int
