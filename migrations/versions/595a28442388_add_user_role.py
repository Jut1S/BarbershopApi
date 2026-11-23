"""add user role

Revision ID: 595a28442388
Revises: b727e4378c69
Create Date: 2026-11-21 18:10:25.125797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '595a28442388'
down_revision: Union[str, Sequence[str], None] = 'b727e4378c69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    userrole = sa.Enum("client", "admin", name="userrole")
    userrole.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum("client", "admin", name="userrole", create_type=False),
            server_default="client",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
