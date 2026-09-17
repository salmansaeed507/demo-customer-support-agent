"""ShopPilot domain tables (greenfield).

Revision ID: 001
Revises:
Create Date: 2026-09-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS csa_tickets CASCADE")

    op.create_table(
        "csa_products",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=1024), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "csa_tickets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("customer", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "csa_orders",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("customer", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=False),
        sa.Column("shipping_address", sa.Text(), nullable=False),
        sa.Column("total", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("shipping_method", sa.String(length=64), nullable=False),
        sa.Column("carrier", sa.String(length=64), nullable=False),
        sa.Column("tracking_number", sa.String(length=128), nullable=False),
        sa.Column("payment_method", sa.String(length=128), nullable=False),
        sa.Column("placed_at", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "csa_order_items",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("product_id", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["csa_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["csa_products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "csa_knowledge_docs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("size_kb", sa.Integer(), nullable=False),
        sa.Column("indexed", sa.Boolean(), nullable=False),
        sa.Column("uploaded_at", sa.Date(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedding_status", sa.String(length=32), nullable=False),
        sa.Column("collection", sa.String(length=128), nullable=False),
        sa.Column("tags", json_type, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "csa_chat_threads",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "csa_chat_messages",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("thread_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trace", json_type, nullable=True),
        sa.Column("citations", json_type, nullable=True),
        sa.ForeignKeyConstraint(
            ["thread_id"],
            ["csa_chat_threads.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("csa_chat_messages")
    op.drop_table("csa_chat_threads")
    op.drop_table("csa_knowledge_docs")
    op.drop_table("csa_order_items")
    op.drop_table("csa_orders")
    op.drop_table("csa_tickets")
    op.drop_table("csa_products")
