import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from common import s3 as s3_storage

from ..config import settings
from ..dependencies import get_db, require_user_id
from ..ids import new_id
from ..models import Product
from ..schemas import ProductCreate, ProductOut, ProductUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


def _get_product(db: Session, product_id: str, user_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.user_id != user_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _promote_image_url_if_staging(image_url: str) -> str:
    key = image_url.strip()
    if not key or not s3_storage.is_staging_key(settings, key):
        return image_url
    s3_storage.require_s3_configured(settings)
    return s3_storage.promote_object(settings, key)


def _delete_attached_image(image_url: str) -> None:
    """Best-effort delete of a managed S3 object; skips external URLs / empty."""
    key = (image_url or "").strip()
    if not key or not s3_storage.is_managed_object_key(settings, key):
        return
    if not s3_storage.s3_configured(settings):
        return
    try:
        s3_storage.delete_object(settings, key)
    except Exception:
        logger.exception("Failed to delete product image from S3 key=%s", key)


@router.get("", response_model=list[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> list[Product]:
    return list(
        db.scalars(
            select(Product).where(Product.user_id == user_id).order_by(Product.name)
        ).all()
    )


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Product:
    return _get_product(db, product_id, user_id)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Product:
    product_id = body.id or new_id("p")
    if db.get(Product, product_id) is not None:
        raise HTTPException(status_code=409, detail="Product id already exists")
    product = Product(
        id=product_id,
        user_id=user_id,
        name=body.name,
        price=body.price,
        category=body.category,
        description=body.description,
        stock=body.stock,
        image_url=_promote_image_url_if_staging(body.image_url),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Product:
    product = _get_product(db, product_id, user_id)
    previous_image = product.image_url or ""
    updates = body.model_dump(exclude_unset=True)
    if "image_url" in updates and isinstance(updates["image_url"], str):
        updates["image_url"] = _promote_image_url_if_staging(updates["image_url"])
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)

    if "image_url" in updates:
        new_image = product.image_url or ""
        if previous_image and previous_image != new_image:
            _delete_attached_image(previous_image)

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Response:
    product = _get_product(db, product_id, user_id)
    image_url = product.image_url or ""
    db.delete(product)
    db.commit()
    _delete_attached_image(image_url)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
