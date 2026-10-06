from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budgets import BudgetCreate
from app.schemas.summary import CategorySummary, SpendingSummary


async def spending_summary(db: AsyncSession, user_id: int, from_date: date, to_date: date) -> SpendingSummary:
    base = [Transaction.user_id == user_id, Transaction.transaction_date >= from_date, Transaction.transaction_date <= to_date]
    totals = await db.execute(
        select(Transaction.transaction_type, func.coalesce(func.sum(Transaction.amount), 0)).where(*base).group_by(Transaction.transaction_type)
    )
    amounts = {kind: Decimal(str(total)) for kind, total in totals.all()}
    categories = await db.execute(
        select(Transaction.category, func.coalesce(func.sum(Transaction.amount), 0)).where(*base, Transaction.transaction_type == "expense").group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc())
    )
    expenses = amounts.get("expense", Decimal("0"))
    income = amounts.get("income", Decimal("0"))
    return SpendingSummary(
        from_date=from_date,
        to_date=to_date,
        total_expenses=expenses,
        total_income=income,
        net=income - expenses,
        by_category=[CategorySummary(category=category, total=Decimal(str(total))) for category, total in categories.all()],
    )


async def create_budget(db: AsyncSession, user_id: int, data: BudgetCreate) -> Budget:
    budget = Budget(user_id=user_id, **data.model_dump())
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


async def budget_status(db: AsyncSession, user_id: int, budget: Budget) -> dict:
    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.category == budget.category,
            Transaction.transaction_date >= budget.period_start,
            Transaction.transaction_date <= budget.period_end,
        )
    )
    spent = Decimal(str(result.scalar_one()))
    remaining = budget.amount - spent
    percentage = (spent / budget.amount * 100) if budget.amount else Decimal("0")
    return {"budget": budget, "spent": spent, "remaining": remaining, "percentage_used": percentage}
