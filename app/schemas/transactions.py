from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    transaction_type: Literal["expense", "income"] = "expense"
    category: str = Field(..., min_length=1, max_length=100)
    merchant: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=2000)
    transaction_date: date = Field(default_factory=date.today)


class TransactionUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    transaction_type: Literal["expense", "income"] | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    merchant: str | None = Field(default=None, max_length=150)
    notes: str | None = Field(default=None, max_length=2000)
    transaction_date: date | None = None


class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    transaction_type: str
    category: str
    merchant: str | None
    notes: str | None
    transaction_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
