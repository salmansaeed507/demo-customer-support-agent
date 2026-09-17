from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_db, require_user_id
from ..ids import new_id
from ..models import Product
from ..schemas import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def _get_product(db: Session, product_id: str, user_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.user_id != user_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


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
        image_url=body.image_url,
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
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Response:
    product = _get_product(db, product_id, user_id)
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
