from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BudgetCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    period_start: date
    period_end: date

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_start > self.period_end:
            raise ValueError("period_start must be before period_end")
        return self


class BudgetResponse(BaseModel):
    id: int
    category: str
    amount: Decimal
    period_start: date
    period_end: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BudgetStatus(BudgetResponse):
    spent: Decimal
    remaining: Decimal
    percentage_used: Decimal
