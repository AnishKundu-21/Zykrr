"""
Ticket service – business logic layer.

Responsibilities:
  - Orchestrate analysis (calls analyzer)
  - Persist tickets to DB
  - Fetch ticket lists
"""
import json

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.analyzer import analyze
from app.models import Ticket
from app.schemas import TicketRequest, TicketResponse, TicketListResponse


def _to_response(ticket: Ticket) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        urgency=ticket.urgency,
        confidence=ticket.confidence,
        keywords=ticket.get_keywords(),
        custom_flags=ticket.get_custom_flags(),
        created_at=ticket.created_at,
    )


async def analyze_and_save(request: TicketRequest, db: AsyncSession) -> TicketResponse:
    """Run analysis pipeline and persist the result."""
    result = analyze(request.subject, request.description)

    ticket = Ticket(
        subject=request.subject,
        description=request.description,
        category=result.category,
        priority=result.priority,
        urgency=result.urgency,
        confidence=result.confidence,
        keywords=json.dumps(result.keywords),
        custom_flags=json.dumps(result.custom_flags),
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return _to_response(ticket)


async def list_tickets(db: AsyncSession) -> TicketListResponse:
    """Return all tickets ordered by newest first."""
    result = await db.execute(select(Ticket).order_by(desc(Ticket.created_at)))
    tickets = result.scalars().all()
    return TicketListResponse(
        tickets=[_to_response(t) for t in tickets],
        total=len(tickets),
    )
