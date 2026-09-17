"""Add user_id integer to all CSA domain tables.

Revision ID: 004
Revises: 003
Create Date: 2026-09-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    "csa_products",
    "csa_tickets",
    "csa_orders",
    "csa_order_items",
    "csa_knowledge_docs",
    "csa_chat_threads",
    "csa_chat_messages",
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    for table in TABLES:
        if table not in tables:
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "user_id" not in columns:
            op.add_column(
                table,
                sa.Column(
                    "user_id",
                    sa.Integer(),
                    nullable=False,
                    server_default="1",
                ),
            )
            op.alter_column(table, "user_id", server_default=None)
            op.create_index(f"ix_{table}_user_id", table, ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    for table in TABLES:
        if table not in tables:
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "user_id" in columns:
            op.drop_index(f"ix_{table}_user_id", table_name=table)
            op.drop_column(table, "user_id")
