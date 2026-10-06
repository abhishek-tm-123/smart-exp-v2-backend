"""create transactions table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4f2b8a1d901"
down_revision: Union[str, Sequence[str], None] = "913a6d41c3be"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("merchant", sa.String(length=150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_id", "transactions", ["id"], unique=False)
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"], unique=False)
    op.create_index(
        "ix_transactions_user_date", "transactions", ["user_id", "transaction_date"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_user_date", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_index("ix_transactions_id", table_name="transactions")
    op.drop_table("transactions")
