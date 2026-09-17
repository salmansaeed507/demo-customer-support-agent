from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_db, require_user_id
from ..ids import new_id
from ..models import Ticket
from ..schemas import TicketCreate, TicketOut, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _next_ticket_id(db: Session) -> str:
    tickets = db.scalars(select(Ticket.id)).all()
    nums = []
    for ticket_id in tickets:
        digits = "".join(ch for ch in ticket_id if ch.isdigit())
        if digits:
            nums.append(int(digits))
    next_num = (max(nums) + 1) if nums else 1001
    return f"TCK-{next_num}"


def _get_ticket(db: Session, ticket_id: str, user_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.user_id != user_id:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> list[Ticket]:
    return list(
        db.scalars(
            select(Ticket).where(Ticket.user_id == user_id).order_by(Ticket.id.desc())
        ).all()
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Ticket:
    return _get_ticket(db, ticket_id, user_id)


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    body: TicketCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Ticket:
    ticket_id = body.id or _next_ticket_id(db)
    if db.get(Ticket, ticket_id) is not None:
        raise HTTPException(status_code=409, detail="Ticket id already exists")
    ticket = Ticket(
        id=ticket_id,
        user_id=user_id,
        customer=body.customer,
        summary=body.summary,
        conversation_id=body.conversation_id or new_id("conv"),
        priority=body.priority,
        status=body.status,
        created=body.created or datetime.now(timezone.utc),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: str,
    body: TicketUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Ticket:
    ticket = _get_ticket(db, ticket_id, user_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Response:
    ticket = _get_ticket(db, ticket_id, user_id)
    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
