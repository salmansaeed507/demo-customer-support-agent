"""Convert user_id from serial/identity to plain integer if needed.

Revision ID: 005
Revises: 004
Create Date: 2026-09-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
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
        columns = {col["name"]: col for col in inspector.get_columns(table)}
        if "user_id" not in columns:
            continue

        # Drop serial/identity default so values come from the gateway header.
        op.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN user_id DROP DEFAULT"))
        op.execute(sa.text(f"DROP SEQUENCE IF EXISTS {table}_user_id_seq CASCADE"))

        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        index_name = f"ix_{table}_user_id"
        if index_name not in indexes:
            op.create_index(index_name, table, ["user_id"], unique=False)


def downgrade() -> None:
    # Irreversible: serial defaults are not restored.
    pass
