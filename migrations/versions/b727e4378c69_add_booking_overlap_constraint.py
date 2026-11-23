"""add booking overlap constraint

Revision ID: b727e4378c69
Revises: 8d265075d752
Create Date: 2026-11-19 09:24:23.018870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b727e4378c69'
down_revision: Union[str, Sequence[str], None] = '8d265075d752'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            barber_id WITH =,
            tstzrange(starts_at, ends_at) WITH &&
        ) WHERE (status = 'confirmed')
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT no_overlapping_bookings")
