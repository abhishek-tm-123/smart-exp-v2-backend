"""add_hashed_password_to_users

Revision ID: 913a6d41c3be
Revises: b0a79eb63c33
Create Date: 2026-10-03 22:15:03.062880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '913a6d41c3be'
down_revision: Union[str, Sequence[str], None] = 'b0a79eb63c33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely:
    1. Add hashed_password as nullable column
    2. Backfill existing rows with placeholder hash
    3. Enforce nullable=False
    """
    op.add_column('users', sa.Column('hashed_password', sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET hashed_password = 'UNUSABLE_PASSWORD_RESET_REQUIRED' WHERE hashed_password IS NULL")
    op.alter_column('users', 'hashed_password', nullable=False)


def downgrade() -> None:
    """Downgrade schema: drop hashed_password column."""
    op.drop_column('users', 'hashed_password')

