from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..agent import run_agent_turn
from ..dependencies import get_db, require_user_id
from ..ids import new_id
from ..models import ChatMessage, ChatThread
from ..schemas import (
    AgentTurnRequest,
    AgentTurnResponse,
    ChatMessageOut,
    TicketOut,
)

router = APIRouter(prefix="/agent", tags=["agent"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_thread(db: Session, thread_id: str | None, user_id: int) -> ChatThread:
    if thread_id:
        thread = db.get(ChatThread, thread_id)
        if thread is None or thread.user_id != user_id:
            raise HTTPException(status_code=404, detail="Chat thread not found")
        return thread

    now = _now()
    thread = ChatThread(
        id=new_id("thr"),
        user_id=user_id,
        title="New chat",
        created_at=now,
        updated_at=now,
    )
    db.add(thread)
    db.flush()
    return thread


@router.post("/turn", response_model=AgentTurnResponse, status_code=status.HTTP_201_CREATED)
def agent_turn(
    body: AgentTurnRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> AgentTurnResponse:
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    thread = _ensure_thread(db, body.thread_id, user_id)
    user_at = _now()
    user_msg = ChatMessage(
        id=new_id("msg"),
        user_id=user_id,
        thread_id=thread.id,
        role="user",
        text=text,
        created_at=user_at,
    )
    db.add(user_msg)

    if thread.title == "New chat":
        thread.title = text[:42] + ("…" if len(text) > 42 else "")
    thread.updated_at = user_at

    result = run_agent_turn(db, text, thread.id, user_id)

    assistant_at = _now()
    assistant_msg = ChatMessage(
        id=new_id("msg"),
        user_id=user_id,
        thread_id=thread.id,
        role="assistant",
        text=result.text,
        created_at=assistant_at,
        trace=result.trace,
        citations=result.citations,
    )
    db.add(assistant_msg)
    thread.updated_at = assistant_at
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)
    if result.ticket is not None:
        db.refresh(result.ticket)

    return AgentTurnResponse(
        thread_id=thread.id,
        user_message=ChatMessageOut.model_validate(user_msg),
        assistant_message=ChatMessageOut.model_validate(assistant_msg),
        ticket=TicketOut.model_validate(result.ticket) if result.ticket else None,
    )
