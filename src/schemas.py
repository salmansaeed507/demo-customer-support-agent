from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


OrderStatus = Literal[
    "processing",
    "out_for_delivery",
    "delivered",
    "refunded",
    "cancelled",
]
TicketPriority = Literal["high", "medium", "low"]
TicketStatus = Literal["open", "pending", "resolved"]
EmbeddingStatus = Literal["ready", "pending", "indexing", "failed"]
ChatRole = Literal["assistant", "user"]
TraceStatus = Literal["ok", "miss"]


class ProductCreate(CamelModel):
    name: str
    price: float
    category: str
    description: str = ""
    stock: int = 0
    image_url: str = ""
    id: str | None = None


class ProductUpdate(CamelModel):
    name: str | None = None
    price: float | None = None
    category: str | None = None
    description: str | None = None
    stock: int | None = None
    image_url: str | None = None


class ProductOut(CamelModel):
    id: str
    name: str
    price: float
    category: str
    description: str
    stock: int
    image_url: str


class TicketCreate(CamelModel):
    customer: str
    summary: str
    conversation_id: str | None = None
    priority: TicketPriority = "medium"
    status: TicketStatus = "open"
    created: datetime | None = None
    id: str | None = None


class TicketUpdate(CamelModel):
    customer: str | None = None
    summary: str | None = None
    conversation_id: str | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    created: datetime | None = None


class TicketOut(CamelModel):
    id: str
    customer: str
    summary: str
    conversation_id: str
    priority: TicketPriority
    status: TicketStatus
    created: datetime


class OrderItemCreate(CamelModel):
    product_id: str | None = None
    name: str
    quantity: int = Field(ge=1, default=1)
    unit_price: float = 0.0
    id: str | None = None


class OrderItemOut(CamelModel):
    id: str
    product_id: str | None = None
    name: str
    quantity: int
    unit_price: float


class OrderCreate(CamelModel):
    customer: str
    email: str = ""
    phone: str = ""
    shipping_address: str = ""
    items: list[OrderItemCreate] = Field(default_factory=list)
    total: float = 0.0
    status: OrderStatus = "processing"
    shipping_method: str = "Standard"
    carrier: str = "—"
    tracking_number: str = "Pending"
    payment_method: str = ""
    placed_at: date | None = None
    id: str | None = None


class OrderUpdate(CamelModel):
    customer: str | None = None
    email: str | None = None
    phone: str | None = None
    shipping_address: str | None = None
    items: list[OrderItemCreate] | None = None
    total: float | None = None
    status: OrderStatus | None = None
    shipping_method: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    payment_method: str | None = None
    placed_at: date | None = None


class OrderOut(CamelModel):
    id: str
    customer: str
    email: str
    phone: str
    shipping_address: str
    items: list[OrderItemOut]
    total: float
    status: OrderStatus
    shipping_method: str
    carrier: str
    tracking_number: str
    payment_method: str
    placed_at: date


class OrderStatusOut(CamelModel):
    id: str
    status: OrderStatus
    tracking_number: str
    carrier: str
    shipping_method: str
    placed_at: date
    customer: str
    items: list[OrderItemOut]
    total: float


class CheckoutItem(CamelModel):
    product_id: str
    quantity: int = Field(ge=1)


class CheckoutRequest(CamelModel):
    customer: str
    email: str
    shipping_address: str
    phone: str = ""
    payment_method: str = "Card"
    shipping_method: str = "Standard"
    items: list[CheckoutItem]


class KnowledgeDocCreate(CamelModel):
    name: str
    type: str = "PDF"
    size_kb: int = 0
    embedding_status: EmbeddingStatus = "pending"
    indexed: bool | None = None
    uploaded_at: date | None = None
    chunk_count: int | None = None
    last_indexed_at: datetime | None = None
    collection: str = "support"
    tags: list[str] = Field(default_factory=list)
    file_url: str = ""
    id: str | None = None


class KnowledgeDocUpdate(CamelModel):
    name: str | None = None
    type: str | None = None
    size_kb: int | None = None
    embedding_status: EmbeddingStatus | None = None
    indexed: bool | None = None
    uploaded_at: date | None = None
    chunk_count: int | None = None
    last_indexed_at: datetime | None = None
    collection: str | None = None
    tags: list[str] | None = None
    file_url: str | None = None


class KnowledgeDocOut(CamelModel):
    id: str
    name: str
    type: str
    size_kb: int
    indexed: bool
    uploaded_at: date
    chunk_count: int
    last_indexed_at: datetime | None
    embedding_status: EmbeddingStatus
    collection: str
    tags: list[str]
    file_url: str = ""


class AgentTraceStep(CamelModel):
    tool: str
    input: str | None = None
    output: str
    status: TraceStatus


class RetrievalCitation(CamelModel):
    filename: str
    excerpt: str
    rank: int
    score: float


class ChatMessageCreate(CamelModel):
    role: ChatRole
    text: str
    trace: list[AgentTraceStep] | None = None
    citations: list[RetrievalCitation] | None = None
    id: str | None = None


class ChatMessageOut(CamelModel):
    id: str
    role: ChatRole
    text: str
    created_at: datetime
    trace: list[AgentTraceStep] | None = None
    citations: list[RetrievalCitation] | None = None


class ChatThreadCreate(CamelModel):
    title: str = "New chat"
    id: str | None = None


class ChatThreadUpdate(CamelModel):
    title: str | None = None


class ChatThreadOut(CamelModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageOut] = Field(default_factory=list)


class AgentTurnRequest(CamelModel):
    text: str
    thread_id: str | None = None


class AgentTurnResponse(CamelModel):
    thread_id: str
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut
    ticket: TicketOut | None = None
