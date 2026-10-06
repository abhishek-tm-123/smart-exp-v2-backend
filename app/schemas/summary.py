from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CategorySummary(BaseModel):
    category: str
    total: Decimal


class SpendingSummary(BaseModel):
    from_date: date
    to_date: date
    total_expenses: Decimal
    total_income: Decimal
    net: Decimal
    by_category: list[CategorySummary]
