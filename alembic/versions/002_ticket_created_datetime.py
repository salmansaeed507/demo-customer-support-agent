"""Rename csa_tickets.created_ago to created (timestamptz).

Revision ID: 002
Revises: 001
Create Date: 2026-09-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {col["name"] for col in sa.inspect(bind).get_columns("csa_tickets")}

    if "created_ago" in columns:
        op.drop_column("csa_tickets", "created_ago")

    if "created" not in columns:
        op.add_column(
            "csa_tickets",
            sa.Column(
                "created",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.alter_column("csa_tickets", "created", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    columns = {col["name"] for col in sa.inspect(bind).get_columns("csa_tickets")}

    if "created" in columns:
        op.drop_column("csa_tickets", "created")

    if "created_ago" not in columns:
        op.add_column(
            "csa_tickets",
            sa.Column(
                "created_ago",
                sa.String(length=64),
                nullable=False,
                server_default="just now",
            ),
        )
        op.alter_column("csa_tickets", "created_ago", server_default=None)
