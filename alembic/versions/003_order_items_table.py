"""Move order items into csa_order_items table.

Revision ID: 003
Revises: 002
Create Date: 2026-09-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    order_columns = {col["name"] for col in inspector.get_columns("csa_orders")}

    if "csa_order_items" not in tables:
        op.create_table(
            "csa_order_items",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("order_id", sa.String(length=64), nullable=False),
            sa.Column("product_id", sa.String(length=64), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(["order_id"], ["csa_orders.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["product_id"], ["csa_products.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "items" in order_columns:
        op.drop_column("csa_orders", "items")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    order_columns = {col["name"] for col in inspector.get_columns("csa_orders")}

    if "items" not in order_columns:
        op.add_column(
            "csa_orders",
            sa.Column(
                "items",
                sa.Text(),
                nullable=False,
                server_default="",
            ),
        )
        op.alter_column("csa_orders", "items", server_default=None)

    if "csa_order_items" in tables:
        op.drop_table("csa_order_items")
