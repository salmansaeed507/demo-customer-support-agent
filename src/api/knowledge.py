from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_db, require_user_id
from ..ids import new_id
from ..models import KnowledgeDoc
from ..schemas import (
    KnowledgeDocCreate,
    KnowledgeDocOut,
    KnowledgeDocUpdate,
)

router = APIRouter(prefix="/knowledge-docs", tags=["knowledge"])


def _estimate_chunks(size_kb: int) -> int:
    return max(4, round(size_kb / 4))


def _sync_indexed_flags(doc: KnowledgeDoc) -> None:
    doc.indexed = doc.embedding_status == "ready"


def _get_doc(db: Session, doc_id: str, user_id: int) -> KnowledgeDoc:
    doc = db.get(KnowledgeDoc, doc_id)
    if doc is None or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return doc


@router.get("", response_model=list[KnowledgeDocOut])
def list_docs(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> list[KnowledgeDoc]:
    return list(
        db.scalars(
            select(KnowledgeDoc)
            .where(KnowledgeDoc.user_id == user_id)
            .order_by(KnowledgeDoc.name)
        ).all()
    )


@router.get("/{doc_id}", response_model=KnowledgeDocOut)
def get_doc(
    doc_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> KnowledgeDoc:
    return _get_doc(db, doc_id, user_id)


@router.post("", response_model=KnowledgeDocOut, status_code=status.HTTP_201_CREATED)
def create_doc(
    body: KnowledgeDocCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> KnowledgeDoc:
    doc_id = body.id or new_id("doc")
    if db.get(KnowledgeDoc, doc_id) is not None:
        raise HTTPException(status_code=409, detail="Document id already exists")

    status_value = body.embedding_status
    if body.indexed is True:
        status_value = "ready"
    elif body.indexed is False and status_value == "ready":
        status_value = "pending"

    indexed = status_value == "ready"
    chunk_count = body.chunk_count
    if chunk_count is None:
        chunk_count = _estimate_chunks(body.size_kb) if indexed else 0

    last_indexed_at = body.last_indexed_at
    if last_indexed_at is None and indexed:
        last_indexed_at = datetime.now(timezone.utc)

    doc = KnowledgeDoc(
        id=doc_id,
        user_id=user_id,
        name=body.name,
        type=body.type,
        size_kb=body.size_kb,
        indexed=indexed,
        uploaded_at=body.uploaded_at or date.today(),
        chunk_count=chunk_count,
        last_indexed_at=last_indexed_at,
        embedding_status=status_value,
        collection=body.collection.strip() or "support",
        tags=list(body.tags),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.patch("/{doc_id}", response_model=KnowledgeDocOut)
def update_doc(
    doc_id: str,
    body: KnowledgeDocUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> KnowledgeDoc:
    doc = _get_doc(db, doc_id, user_id)

    data = body.model_dump(exclude_unset=True)
    if "embedding_status" in data:
        doc.embedding_status = data.pop("embedding_status")
        doc.indexed = doc.embedding_status == "ready"
    if "indexed" in data:
        indexed = data.pop("indexed")
        doc.indexed = indexed
        if indexed and doc.embedding_status != "ready":
            doc.embedding_status = "ready"
        elif not indexed and doc.embedding_status == "ready":
            doc.embedding_status = "pending"

    for field, value in data.items():
        if field == "collection" and isinstance(value, str):
            value = value.strip() or "support"
        setattr(doc, field, value)

    _sync_indexed_flags(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doc(
    doc_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Response:
    doc = _get_doc(db, doc_id, user_id)
    db.delete(doc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{doc_id}/reindex", response_model=KnowledgeDocOut)
def reindex_doc(
    doc_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> KnowledgeDoc:
    """Stub reindex: mark ready with updated chunk count (matches admin UI end-state)."""
    doc = _get_doc(db, doc_id, user_id)

    chunks = (
        doc.chunk_count + 1
        if doc.chunk_count > 0
        else _estimate_chunks(doc.size_kb)
    )
    doc.embedding_status = "ready"
    doc.indexed = True
    doc.chunk_count = chunks
    doc.last_indexed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(doc)
    return doc
