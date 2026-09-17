from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from common.db import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


class Product(Base):
    __tablename__ = "csa_products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    stock: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str] = mapped_column(String(1024), default="")


class Ticket(Base):
    __tablename__ = "csa_tickets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    conversation_id: Mapped[str] = mapped_column(String(64), default="")
    priority: Mapped[str] = mapped_column(String(32), default="medium")
    status: Mapped[str] = mapped_column(String(32), default="open")
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Order(Base):
    __tablename__ = "csa_orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    shipping_address: Mapped[str] = mapped_column(Text, default="")
    total: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="processing")
    shipping_method: Mapped[str] = mapped_column(String(64), default="Standard")
    carrier: Mapped[str] = mapped_column(String(64), default="—")
    tracking_number: Mapped[str] = mapped_column(String(128), default="Pending")
    payment_method: Mapped[str] = mapped_column(String(128), default="")
    placed_at: Mapped[date] = mapped_column(Date)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OrderItem(Base):
    __tablename__ = "csa_order_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("csa_orders.id", ondelete="CASCADE"))
    product_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("csa_products.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)

    order: Mapped["Order"] = relationship(back_populates="items")


class KnowledgeDoc(Base):
    __tablename__ = "csa_knowledge_docs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(64), default="PDF")
    size_kb: Mapped[int] = mapped_column(Integer, default=0)
    indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[date] = mapped_column(Date)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding_status: Mapped[str] = mapped_column(String(32), default="pending")
    collection: Mapped[str] = mapped_column(String(128), default="support")
    tags: Mapped[list] = mapped_column(JsonType, default=list)


class ChatThread(Base):
    __tablename__ = "csa_chat_threads"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "csa_chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    thread_id: Mapped[str] = mapped_column(ForeignKey("csa_chat_threads.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    trace: Mapped[list | None] = mapped_column(JsonType, nullable=True)
    citations: Mapped[list | None] = mapped_column(JsonType, nullable=True)

    thread: Mapped["ChatThread"] = relationship(back_populates="messages")
