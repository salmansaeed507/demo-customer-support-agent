from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_db, require_user_id
from ..ids import new_id
from ..models import Order, OrderItem, Product
from ..schemas import (
    CheckoutRequest,
    OrderCreate,
    OrderItemCreate,
    OrderOut,
    OrderStatusOut,
    OrderUpdate,
)

router = APIRouter(tags=["orders"])


def _next_order_id(db: Session) -> str:
    order_ids = db.scalars(select(Order.id)).all()
    nums = []
    for order_id in order_ids:
        if order_id.isdigit():
            nums.append(int(order_id))
    return str((max(nums) + 1) if nums else 48001)


def _get_order(db: Session, order_id: str, user_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _order_items_from_body(
    order_id: str,
    user_id: int,
    items: list[OrderItemCreate],
) -> list[OrderItem]:
    return [
        OrderItem(
            id=item.id or new_id("oi"),
            user_id=user_id,
            order_id=order_id,
            product_id=item.product_id,
            name=item.name,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        for item in items
    ]


def _create_order_row(db: Session, body: OrderCreate, user_id: int) -> Order:
    order_id = body.id or _next_order_id(db)
    if db.get(Order, order_id) is not None:
        raise HTTPException(status_code=409, detail="Order id already exists")
    order = Order(
        id=order_id,
        user_id=user_id,
        customer=body.customer,
        email=body.email,
        phone=body.phone,
        shipping_address=body.shipping_address,
        total=body.total,
        status=body.status,
        shipping_method=body.shipping_method,
        carrier=body.carrier,
        tracking_number=body.tracking_number,
        payment_method=body.payment_method,
        placed_at=body.placed_at or date.today(),
        items=_order_items_from_body(order_id, user_id, body.items),
    )
    db.add(order)
    return order


@router.get("/orders", response_model=list[OrderOut])
def list_orders(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> list[Order]:
    return list(
        db.scalars(
            select(Order).where(Order.user_id == user_id).order_by(Order.id.desc())
        ).all()
    )


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Order:
    return _get_order(db, order_id, user_id)


@router.get("/orders/{order_id}/status", response_model=OrderStatusOut)
def get_order_status(
    order_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Order:
    return _get_order(db, order_id, user_id)


@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    body: OrderCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Order:
    order = _create_order_row(db, body, user_id)
    db.commit()
    db.refresh(order)
    return order


@router.patch("/orders/{order_id}", response_model=OrderOut)
def update_order(
    order_id: str,
    body: OrderUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Order:
    order = _get_order(db, order_id, user_id)
    data = body.model_dump(exclude_unset=True)
    items = data.pop("items", None)
    for field, value in data.items():
        setattr(order, field, value)
    if items is not None:
        order.items = _order_items_from_body(
            order.id,
            user_id,
            [OrderItemCreate.model_validate(item) for item in items],
        )
    db.commit()
    db.refresh(order)
    return order


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Response:
    order = _get_order(db, order_id, user_id)
    db.delete(order)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/checkout", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def checkout(
    body: CheckoutRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
) -> Order:
    if not body.items:
        raise HTTPException(status_code=400, detail="Checkout requires at least one item")

    line_items: list[OrderItemCreate] = []
    total = 0.0
    products: list[tuple[Product, int]] = []

    for line in body.items:
        product = db.get(Product, line.product_id)
        if product is None or product.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {line.product_id}",
            )
        if product.stock < line.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}",
            )
        products.append((product, line.quantity))
        total += product.price * line.quantity
        line_items.append(
            OrderItemCreate(
                product_id=product.id,
                name=product.name,
                quantity=line.quantity,
                unit_price=product.price,
            )
        )

    for product, quantity in products:
        product.stock -= quantity

    order = _create_order_row(
        db,
        OrderCreate(
            customer=body.customer,
            email=body.email,
            phone=body.phone,
            shipping_address=body.shipping_address,
            items=line_items,
            total=round(total, 2),
            status="processing",
            shipping_method=body.shipping_method,
            carrier="—",
            tracking_number="Pending",
            payment_method=body.payment_method,
            placed_at=date.today(),
        ),
        user_id,
    )
    db.commit()
    db.refresh(order)
    return order
