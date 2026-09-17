"""Seed data aligned with frontend ShopPilot mocks."""

from datetime import date, datetime, timedelta, timezone

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

SEED_PRODUCTS = [
    {
        "id": "p-1001",
        "name": "Aurora Wireless Headphones",
        "price": 129.99,
        "category": "Audio",
        "description": (
            "Over-ear headphones with active noise canceling, 30-hour battery, "
            "and USB-C charging."
        ),
        "stock": 24,
        "image_url": (
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e"
            "?auto=format&fit=crop&w=800&q=80"
        ),
    },
    {
        "id": "p-1002",
        "name": "Nimbus Desk Lamp",
        "price": 49.0,
        "category": "Home",
        "description": (
            "Adjustable color temperature and brightness with memory presets. "
            "USB-powered."
        ),
        "stock": 18,
        "image_url": (
            "https://images.unsplash.com/photo-1507473885765-e6ed057f782c"
            "?auto=format&fit=crop&w=800&q=80"
        ),
    },
    {
        "id": "p-1003",
        "name": "TrailForge Backpack",
        "price": 89.0,
        "category": "Bags",
        "description": (
            "Water-resistant 20L backpack with laptop sleeve and hidden "
            "passport pocket."
        ),
        "stock": 41,
        "image_url": (
            "https://images.unsplash.com/photo-1553062407-98eeb64c6a62"
            "?auto=format&fit=crop&w=800&q=80"
        ),
    },
    {
        "id": "p-1004",
        "name": "FrostBottle Steel",
        "price": 32.0,
        "category": "Drinkware",
        "description": (
            "24oz double-wall bottle keeps drinks cold for 24 hours or hot for 12."
        ),
        "stock": 60,
        "image_url": (
            "https://images.unsplash.com/photo-1602143407151-7111542de6e8"
            "?auto=format&fit=crop&w=800&q=80"
        ),
    },
    {
        "id": "p-1005",
        "name": "Pulse Wireless Mouse",
        "price": 39.99,
        "category": "Accessories",
        "description": (
            "Quiet-click mouse with multi-device pairing and rechargeable battery."
        ),
        "stock": 33,
        "image_url": (
            "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46"
            "?auto=format&fit=crop&w=800&q=80"
        ),
    },
    {
        "id": "p-1006",
        "name": "SoftCotton Tee Pack",
        "price": 45.0,
        "category": "Apparel",
        "description": (
            "Soft unisex tees in charcoal, cream, and navy. Pre-shrunk fabric."
        ),
        "stock": 12,
        "image_url": (
            "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab"
            "?auto=format&fit=crop&w=800&q=80"
        ),
    },
]

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
        "total": 178.99,
        "status": "out_for_delivery",
        "shipping_method": "Express",
        "carrier": "UPS",
        "tracking_number": "1Z999AA10123456784",
        "payment_method": "Visa ···· 4242",
        "placed_at": date(2026, 9, 1),
        "items": [
            {
                "id": "oi-48291-1",
                "product_id": "p-1001",
                "name": "Aurora Wireless Headphones",
                "quantity": 1,
                "unit_price": 129.99,
            },
            {
                "id": "oi-48291-2",
                "product_id": "p-1006",
                "name": "SoftCotton Tee Pack",
                "quantity": 1,
                "unit_price": 45.0,
            },
        ],
    },
    {
        "id": "48288",
        "customer": "Sam Chen",
        "email": "sam.chen@example.com",
        "phone": "+1 (415) 555-0198",
        "shipping_address": "90 Mission St, San Francisco, CA 94105",
        "total": 89.0,
        "status": "delivered",
        "shipping_method": "Standard",
        "carrier": "USPS",
        "tracking_number": "9400111899223344556677",
        "payment_method": "Mastercard ···· 4444",
        "placed_at": date(2026, 8, 28),
        "items": [
            {
                "id": "oi-48288-1",
                "product_id": "p-1003",
                "name": "TrailForge Backpack",
                "quantity": 1,
                "unit_price": 89.0,
            },
        ],
    },
    {
        "id": "48275",
        "customer": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "phone": "+1 (206) 555-0177",
        "shipping_address": "1201 Pine St, Seattle, WA 98101",
        "total": 49.0,
        "status": "processing",
        "shipping_method": "Standard",
        "carrier": "—",
        "tracking_number": "Pending",
        "payment_method": "PayPal",
        "placed_at": date(2026, 9, 2),
        "items": [
            {
                "id": "oi-48275-1",
                "product_id": "p-1002",
                "name": "Nimbus Desk Lamp",
                "quantity": 1,
                "unit_price": 49.0,
            },
        ],
    },
    {
        "id": "48260",
        "customer": "Alex Rivera",
        "email": "alex@example.com",
        "phone": "+1 (512) 555-0101",
        "shipping_address": "123 Market St, Austin, TX 78701",
        "total": 129.99,
        "status": "refunded",
        "shipping_method": "Standard",
        "carrier": "FedEx",
        "tracking_number": "794612345678",
        "payment_method": "Visa ···· 1881",
        "placed_at": date(2026, 8, 20),
        "items": [
            {
                "id": "oi-48260-1",
                "product_id": "p-1001",
                "name": "Aurora Wireless Headphones",
                "quantity": 1,
                "unit_price": 129.99,
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
    """Insert frontend-aligned demo rows for a single user when they have none."""
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
