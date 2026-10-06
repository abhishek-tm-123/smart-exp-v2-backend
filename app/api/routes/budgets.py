from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.budget import Budget
from app.models.user import User
from app.schemas.budgets import BudgetCreate, BudgetResponse, BudgetStatus
from app.services.finance import budget_status, create_budget

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_endpoint(data: BudgetCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> BudgetResponse:
    return await create_budget(db, current_user.id, data)


@router.get("/", response_model=list[BudgetResponse])
async def list_budgets(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[BudgetResponse]:
    result = await db.execute(select(Budget).where(Budget.user_id == current_user.id).order_by(Budget.period_start.desc(), Budget.id.desc()))
    return list(result.scalars().all())


@router.get("/status", response_model=list[BudgetStatus])
async def get_budget_status(as_of: date | None = Query(default=None), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[BudgetStatus]:
    day = as_of or date.today()
    result = await db.execute(select(Budget).where(Budget.user_id == current_user.id, Budget.period_start <= day, Budget.period_end >= day).order_by(Budget.category))
    statuses = [await budget_status(db, current_user.id, budget) for budget in result.scalars().all()]
    return [BudgetStatus.model_validate({**item["budget"].__dict__, **{k: item[k] for k in ("spent", "remaining", "percentage_used")}}) for item in statuses]
