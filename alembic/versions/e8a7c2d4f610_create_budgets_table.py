"""create budgets table"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e8a7c2d4f610"
down_revision: Union[str, Sequence[str], None] = "c4f2b8a1d901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_budgets_id", "budgets", ["id"], unique=False)
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_index("ix_budgets_id", table_name="budgets")
    op.drop_table("budgets")
