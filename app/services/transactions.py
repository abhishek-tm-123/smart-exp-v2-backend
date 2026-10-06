from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.schemas.transactions import TransactionCreate, TransactionUpdate


async def list_transactions(db: AsyncSession, user_id: int, transaction_type: Optional[str] = None, category: Optional[str] = None, from_date: Optional[date] = None, to_date: Optional[date] = None) -> list[Transaction]:
    query = select(Transaction).where(Transaction.user_id == user_id)
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    if category:
        query = query.where(Transaction.category == category)
    if from_date:
        query = query.where(Transaction.transaction_date >= from_date)
    if to_date:
        query = query.where(Transaction.transaction_date <= to_date)
    query = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_transaction(db: AsyncSession, user_id: int, transaction_id: int) -> Optional[Transaction]:
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id))
    return result.scalar_one_or_none()


async def create_transaction(db: AsyncSession, user_id: int, data: TransactionCreate) -> Transaction:
    transaction = Transaction(user_id=user_id, **data.model_dump())
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


async def update_transaction(db: AsyncSession, transaction: Transaction, data: TransactionUpdate) -> Transaction:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(transaction, field, value)
    await db.commit()
    await db.refresh(transaction)
    return transaction


async def delete_transaction(db: AsyncSession, transaction: Transaction) -> None:
    await db.delete(transaction)
    await db.commit()
