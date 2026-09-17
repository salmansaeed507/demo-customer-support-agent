from collections.abc import Generator

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from common.db import create_session_factory

from .config import settings

_session_factory = create_session_factory(settings.database_url)


def get_db() -> Generator[Session, None, None]:
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()


def require_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> int:
    if x_user_id is None or not str(x_user_id).strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header",
        )
    try:
        return int(str(x_user_id).strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-Id header",
        ) from exc
