from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_db, require_user_id
from ..seed import purge_user_data, seed_database

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/seed")
def seed_current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> dict[str, str]:
    seed_database(db, user_id)
    return {"status": "ok"}


@router.delete("/data")
def purge_current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> dict[str, str]:
    purge_user_data(db, user_id)
    return {"status": "ok"}
