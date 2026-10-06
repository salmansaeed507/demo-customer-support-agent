"""Seed data for customer-support-agent demos."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .models import (
    ChatMessage,
    ChatThread,
    KnowledgeDoc,
    Order,
    OrderItem,
    Product,
    Ticket,
)

_SEED_NOW = datetime.now(timezone.utc)

# Default catalog: https://kolzsticks.github.io/Free-Ecommerce-Products-Api/main/products.json
_DEFAULT_PRODUCTS_PATH = Path(__file__).resolve().parent / "data" / "products.json"
_DEFAULT_STOCK = 25


def _load_seed_products(path: Path = _DEFAULT_PRODUCTS_PATH) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    products: list[dict] = []
    for row in rows:
        products.append(
            {
                "id": str(row["id"]),
                "name": row["name"],
                "price": round(float(row["priceCents"]) / 100.0, 2),
                "category": row.get("category") or "General",
                "description": row.get("description") or "",
                "stock": _DEFAULT_STOCK,
                "image_url": row.get("image") or "",
            }
        )
    return products


SEED_PRODUCTS = _load_seed_products()

SEED_TICKETS = [
    {
        "id": "TCK-1042",
        "customer": "Sara Khan",
        "summary": "Order #48291 delayed — refund not received after 7 days",
        "conversation_id": "conv-110",
        "priority": "high",
        "status": "open",
        "created": _SEED_NOW - timedelta(minutes=10),
    },
    {
        "id": "TCK-1040",
        "customer": "Sam Chen",
        "summary": "Duplicate charge on order #48288 — needs billing review",
        "conversation_id": "conv-103",
        "priority": "high",
        "status": "open",
        "created": _SEED_NOW - timedelta(hours=1),
    },
    {
        "id": "TCK-1039",
        "customer": "Ali Raza",
        "summary": "Wants invoice copy for corporate expense report",
        "conversation_id": "conv-099",
        "priority": "low",
        "status": "resolved",
        "created": _SEED_NOW - timedelta(hours=3),
    },
    {
        "id": "TCK-1035",
        "customer": "Morgan Blake",
        "summary": "Damaged LED lamp on arrival — replacement requested",
        "conversation_id": "conv-098",
        "priority": "medium",
        "status": "pending",
        "created": _SEED_NOW - timedelta(days=1),
    },
    {
        "id": "TCK-1031",
        "customer": "Alex Rivera",
        "summary": "Asked for human help after shipping delay (AI escalated)",
        "conversation_id": "conv-101",
        "priority": "medium",
        "status": "resolved",
        "created": _SEED_NOW - timedelta(days=2),
    },
]

SEED_ORDERS = [
    {
        "id": "48291",
        "customer": "Sara Khan",
        "email": "sara.khan@example.com",
        "phone": "+1 (512) 555-0142",
        "shipping_address": "482 Oak Ave, Apt 4B, Austin, TX 78702",
        "total": 97.99,
        "status": "out_for_delivery",
        "shipping_method": "Express",
        "carrier": "UPS",
        "tracking_number": "1Z999AA10123456784",
        "payment_method": "Visa ···· 4242",
        "placed_at": date(2026, 9, 1),
        "items": [
            {
                "id": "oi-48291-1",
                "product_id": "11",
                "name": "Wireless Bluetooth Headphones",
                "quantity": 1,
                "unit_price": 79.99,
            },
            {
                "id": "oi-48291-2",
                "product_id": "28",
                "name": "Graphic Print T-Shirt",
                "quantity": 1,
                "unit_price": 18.0,
            },
        ],
    },
    {
        "id": "48288",
        "customer": "Sam Chen",
        "email": "sam.chen@example.com",
        "phone": "+1 (415) 555-0198",
        "shipping_address": "90 Mission St, San Francisco, CA 94105",
        "total": 60.0,
        "status": "delivered",
        "shipping_method": "Standard",
        "carrier": "USPS",
        "tracking_number": "9400111899223344556677",
        "payment_method": "Mastercard ···· 4444",
        "placed_at": date(2026, 8, 28),
        "items": [
            {
                "id": "oi-48288-1",
                "product_id": "24",
                "name": "Leather Tote Bag",
                "quantity": 1,
                "unit_price": 60.0,
            },
        ],
    },
    {
        "id": "48275",
        "customer": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "phone": "+1 (206) 555-0177",
        "shipping_address": "1201 Pine St, Seattle, WA 98101",
        "total": 50.0,
        "status": "processing",
        "shipping_method": "Standard",
        "carrier": "—",
        "tracking_number": "Pending",
        "payment_method": "PayPal",
        "placed_at": date(2026, 9, 2),
        "items": [
            {
                "id": "oi-48275-1",
                "product_id": "37",
                "name": "Contemporary Table Lamp",
                "quantity": 1,
                "unit_price": 50.0,
            },
        ],
    },
    {
        "id": "48260",
        "customer": "Alex Rivera",
        "email": "alex@example.com",
        "phone": "+1 (512) 555-0101",
        "shipping_address": "123 Market St, Austin, TX 78701",
        "total": 79.99,
        "status": "refunded",
        "shipping_method": "Standard",
        "carrier": "FedEx",
        "tracking_number": "794612345678",
        "payment_method": "Visa ···· 1881",
        "placed_at": date(2026, 8, 20),
        "items": [
            {
                "id": "oi-48260-1",
                "product_id": "11",
                "name": "Wireless Bluetooth Headphones",
                "quantity": 1,
                "unit_price": 79.99,
            },
        ],
    },
]

SEED_DOCS = [
    {
        "id": "doc-1",
        "name": "shipping-policy.pdf",
        "type": "PDF",
        "size_kb": 240,
        "indexed": True,
        "uploaded_at": date(2026, 8, 20),
        "chunk_count": 48,
        "last_indexed_at": datetime(2026, 9, 2, 14, 10, tzinfo=timezone.utc),
        "embedding_status": "ready",
        "collection": "policies",
        "tags": ["shipping", "fulfillment"],
    },
    {
        "id": "doc-2",
        "name": "returns-and-refunds.md",
        "type": "Markdown",
        "size_kb": 18,
        "indexed": True,
        "uploaded_at": date(2026, 8, 22),
        "chunk_count": 22,
        "last_indexed_at": datetime(2026, 9, 8, 9, 42, tzinfo=timezone.utc),
        "embedding_status": "ready",
        "collection": "policies",
        "tags": ["returns", "refunds"],
    },
    {
        "id": "doc-3",
        "name": "product-faq.docx",
        "type": "Word",
        "size_kb": 96,
        "indexed": False,
        "uploaded_at": date(2026, 9, 1),
        "chunk_count": 0,
        "last_indexed_at": None,
        "embedding_status": "pending",
        "collection": "catalog",
        "tags": ["faq", "products"],
    },
    {
        "id": "doc-4",
        "name": "warranty-guide.pdf",
        "type": "PDF",
        "size_kb": 64,
        "indexed": True,
        "uploaded_at": date(2026, 9, 1),
        "chunk_count": 31,
        "last_indexed_at": datetime(2026, 9, 1, 18, 5, tzinfo=timezone.utc),
        "embedding_status": "ready",
        "collection": "policies",
        "tags": ["warranty"],
    },
]


def _scoped(user_id: int, entity_id: str) -> str:
    return f"{user_id}-{entity_id}"


def _user_is_empty(db: Session, user_id: int) -> bool:
    count = db.scalar(
        select(func.count()).select_from(Product).where(Product.user_id == user_id)
    )
    return (count or 0) == 0


def seed_database(db: Session, user_id: int) -> None:
    """Insert demo rows for a single user when they have none."""
    if not _user_is_empty(db, user_id):
        return

    db.add_all(
        [
            Product(user_id=user_id, **{**row, "id": _scoped(user_id, row["id"])})
            for row in SEED_PRODUCTS
        ]
    )
    db.add_all(
        [
            Ticket(
                user_id=user_id,
                **{
                    **row,
                    "id": _scoped(user_id, row["id"]),
                    "conversation_id": _scoped(user_id, row["conversation_id"]),
                },
            )
            for row in SEED_TICKETS
        ]
    )
    for row in SEED_ORDERS:
        item_rows = row["items"]
        order_id = _scoped(user_id, row["id"])
        order = Order(
            user_id=user_id,
            **{
                **{k: v for k, v in row.items() if k != "items"},
                "id": order_id,
            },
        )
        order.items = [
            OrderItem(
                user_id=user_id,
                order_id=order_id,
                id=_scoped(user_id, item["id"]),
                product_id=_scoped(user_id, item["product_id"])
                if item.get("product_id")
                else None,
                name=item["name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
            for item in item_rows
        ]
        db.add(order)
    db.add_all(
        [
            KnowledgeDoc(user_id=user_id, **{**row, "id": _scoped(user_id, row["id"])})
            for row in SEED_DOCS
        ]
    )
    now = datetime.now(timezone.utc)
    db.add(
        ChatThread(
            id=_scoped(user_id, "thr-seed"),
            user_id=user_id,
            title="New chat",
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()


def purge_user_data(db: Session, user_id: int) -> None:
    """Delete all CSA domain rows owned by user_id."""
    db.execute(delete(ChatMessage).where(ChatMessage.user_id == user_id))
    db.execute(delete(ChatThread).where(ChatThread.user_id == user_id))
    db.execute(delete(OrderItem).where(OrderItem.user_id == user_id))
    db.execute(delete(Order).where(Order.user_id == user_id))
    db.execute(delete(Ticket).where(Ticket.user_id == user_id))
    db.execute(delete(KnowledgeDoc).where(KnowledgeDoc.user_id == user_id))
    db.execute(delete(Product).where(Product.user_id == user_id))
    db.commit()
