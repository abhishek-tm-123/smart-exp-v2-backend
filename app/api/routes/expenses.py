from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transactions import TransactionCreate, TransactionResponse, TransactionUpdate
from app.services.transactions import create_transaction, delete_transaction, get_transaction, list_transactions, update_transaction
from app.schemas.summary import SpendingSummary
from app.services.finance import spending_summary

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/summary", response_model=SpendingSummary)
async def get_spending_summary(from_date: date, to_date: date, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> SpendingSummary:
    if from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")
    return await spending_summary(db, current_user.id, from_date, to_date)


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction_endpoint(data: TransactionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> TransactionResponse:
    return await create_transaction(db, current_user.id, data)


@router.get("/", response_model=list[TransactionResponse])
async def get_transactions(transaction_type: Literal["expense", "income"] | None = Query(default=None), category: str | None = Query(default=None, max_length=100), from_date: date | None = Query(default=None), to_date: date | None = Query(default=None), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[TransactionResponse]:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")
    return await list_transactions(db, current_user.id, transaction_type, category, from_date, to_date)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_endpoint(transaction_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> TransactionResponse:
    transaction = await get_transaction(db, current_user.id, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction_endpoint(transaction_id: int, data: TransactionUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> TransactionResponse:
    transaction = await get_transaction(db, current_user.id, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return await update_transaction(db, transaction, data)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction_endpoint(transaction_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> Response:
    transaction = await get_transaction(db, current_user.id, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await delete_transaction(db, transaction)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
