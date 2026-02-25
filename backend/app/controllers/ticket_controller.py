"""
Ticket controller – thin route handlers only.

No business logic lives here.  Each handler:
  1. Receives validated input (Pydantic).
  2. Delegates to the service layer.
  3. Returns the response.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import TicketListResponse, TicketRequest, TicketResponse
from app.services.ticket_service import analyze_and_save, list_tickets

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/analyze", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketRequest,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """Analyze a support ticket and persist it."""
    return await analyze_and_save(payload, db)


@router.get("", response_model=TicketListResponse, status_code=status.HTTP_200_OK)
async def get_tickets(
    db: AsyncSession = Depends(get_db),
) -> TicketListResponse:
    """List all analyzed tickets, newest first."""
    return await list_tickets(db)
