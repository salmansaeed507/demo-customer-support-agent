"""Add file_url to knowledge docs for S3 object keys.

Revision ID: 006
Revises: 005
Create Date: 2026-09-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "csa_knowledge_docs" not in tables:
        return
    columns = {col["name"] for col in inspector.get_columns("csa_knowledge_docs")}
    if "file_url" in columns:
        return
    op.add_column(
        "csa_knowledge_docs",
        sa.Column(
            "file_url",
            sa.String(length=1024),
            nullable=False,
            server_default="",
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "csa_knowledge_docs" not in tables:
        return
    columns = {col["name"] for col in inspector.get_columns("csa_knowledge_docs")}
    if "file_url" not in columns:
        return
    op.drop_column("csa_knowledge_docs", "file_url")
