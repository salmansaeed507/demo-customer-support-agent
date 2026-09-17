from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from ..dependencies import get_db, require_user_id
from ..ids import new_id
from ..models import ChatMessage, ChatThread
from ..schemas import (
    ChatMessageCreate,
    ChatMessageOut,
    ChatThreadCreate,
    ChatThreadOut,
    ChatThreadUpdate,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_thread(db: Session, thread_id: str, user_id: int) -> ChatThread:
    thread = db.scalar(
        select(ChatThread)
        .where(ChatThread.id == thread_id, ChatThread.user_id == user_id)
        .options(selectinload(ChatThread.messages))
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="Chat thread not found")
    return thread


def _ensure_welcome_thread(db: Session, user_id: int) -> ChatThread:
    now = _now()
    thread = ChatThread(
        id=new_id("thr"),
        user_id=user_id,
        title="New chat",
        created_at=now,
        updated_at=now,
    )
    db.add(thread)
    return thread


@router.get("/threads", response_model=list[ChatThreadOut])
def list_threads(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> list[ChatThread]:
    return list(
        db.scalars(
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .options(selectinload(ChatThread.messages))
            .order_by(ChatThread.updated_at.desc())
        ).all()
    )


@router.post("/threads", response_model=ChatThreadOut, status_code=status.HTTP_201_CREATED)
def create_thread(
    body: ChatThreadCreate | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> ChatThread:
    payload = body or ChatThreadCreate()
    thread_id = payload.id or new_id("thr")
    if db.get(ChatThread, thread_id) is not None:
        raise HTTPException(status_code=409, detail="Thread id already exists")
    now = _now()
    thread = ChatThread(
        id=thread_id,
        user_id=user_id,
        title=payload.title.strip() or "New chat",
        created_at=now,
        updated_at=now,
    )
    db.add(thread)
    db.commit()
    return _get_thread(db, thread.id, user_id)


@router.get("/threads/{thread_id}", response_model=ChatThreadOut)
def get_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> ChatThread:
    return _get_thread(db, thread_id, user_id)


@router.patch("/threads/{thread_id}", response_model=ChatThreadOut)
def update_thread(
    thread_id: str,
    body: ChatThreadUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> ChatThread:
    thread = _get_thread(db, thread_id, user_id)
    if body.title is not None:
        thread.title = body.title.strip() or thread.title
    thread.updated_at = _now()
    db.commit()
    return _get_thread(db, thread_id, user_id)


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Response:
    thread = db.get(ChatThread, thread_id)
    if thread is None or thread.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chat thread not found")
    db.delete(thread)
    db.flush()
    remaining = db.scalar(
        select(ChatThread.id).where(ChatThread.user_id == user_id).limit(1)
    )
    if remaining is None:
        _ensure_welcome_thread(db, user_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/threads/{thread_id}/clear", response_model=ChatThreadOut)
def clear_thread_messages(
    thread_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> ChatThread:
    thread = _get_thread(db, thread_id, user_id)
    db.execute(
        delete(ChatMessage).where(
            ChatMessage.thread_id == thread_id,
            ChatMessage.user_id == user_id,
        )
    )
    thread.title = "New chat"
    thread.updated_at = _now()
    db.commit()
    return _get_thread(db, thread_id, user_id)


@router.get("/threads/{thread_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    thread_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> list[ChatMessage]:
    thread = _get_thread(db, thread_id, user_id)
    return list(thread.messages)


@router.post(
    "/threads/{thread_id}/messages",
    response_model=ChatMessageOut,
    status_code=status.HTTP_201_CREATED,
)
def append_message(
    thread_id: str,
    body: ChatMessageCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> ChatMessage:
    thread = _get_thread(db, thread_id, user_id)
    message_id = body.id or new_id("msg")
    if db.get(ChatMessage, message_id) is not None:
        raise HTTPException(status_code=409, detail="Message id already exists")

    now = _now()
    message = ChatMessage(
        id=message_id,
        user_id=user_id,
        thread_id=thread_id,
        role=body.role,
        text=body.text,
        created_at=now,
        trace=(
            [step.model_dump(by_alias=True) for step in body.trace]
            if body.trace is not None
            else None
        ),
        citations=(
            [c.model_dump(by_alias=True) for c in body.citations]
            if body.citations is not None
            else None
        ),
    )
    db.add(message)

    if thread.title == "New chat" and body.role == "user":
        trimmed = body.text.strip()
        thread.title = trimmed[:42] + ("…" if len(trimmed) > 42 else "")
    thread.updated_at = now
    db.commit()
    db.refresh(message)
    return message
