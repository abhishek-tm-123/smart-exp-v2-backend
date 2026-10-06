import asyncio
import json
import re
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.budget import Budget
from app.schemas.budgets import BudgetCreate
from app.schemas.transactions import TransactionCreate
from app.services.finance import budget_status, create_budget, spending_summary
from app.services.transactions import create_transaction


class FinanceIntent(BaseModel):
    action: Literal["conversation", "add_expense", "get_spending_summary", "set_budget", "get_budget_status"]
    reply: str = ""
    amount: float | None = None
    category: str | None = None
    merchant: str | None = None
    notes: str | None = None
    transaction_date: str | None = None
    from_date: str | None = None
    to_date: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    as_of: str | None = None


def _transaction_result(transaction) -> dict:
    return {"id": transaction.id, "amount": str(transaction.amount), "category": transaction.category, "merchant": transaction.merchant, "transaction_date": transaction.transaction_date.isoformat()}


def _budget_result(budget) -> dict:
    return {"id": budget.id, "amount": str(budget.amount), "category": budget.category, "period_start": budget.period_start.isoformat(), "period_end": budget.period_end.isoformat()}


def _format_tool_reply(name: str, result: dict) -> str:
    if "error" in result:
        return f"I could not complete that request: {result['error']}"
    if name == "add_expense":
        item = result["transaction"]
        merchant = f" at {item['merchant']}" if item.get("merchant") else ""
        return f"Done. I added an expense of {item['amount']} under {item['category']}{merchant} for {item['transaction_date']}."
    if name == "get_spending_summary":
        categories = ", ".join(f"{item['category']}: {item['total']}" for item in result["by_category"][:5]) or "no expense categories"
        return f"From {result['from_date']} to {result['to_date']}, your expenses were {result['total_expenses']}, income was {result['total_income']}, and net was {result['net']}. Top categories: {categories}."
    if name == "set_budget":
        item = result["budget"]
        return f"Done. I set a {item['category']} budget of {item['amount']} from {item['period_start']} to {item['period_end']}."
    if name == "get_budget_status":
        if not result["budgets"]:
            return f"You have no active budgets on {result['as_of']}."
        items = "; ".join(f"{item['budget']['category']}: spent {item['spent']} of {item['budget']['amount']}, remaining {item['remaining']}" for item in result["budgets"])
        return f"Budget status for {result['as_of']}: {items}."
    return "The finance action completed."


async def _run_tool(db: AsyncSession, user_id: int, name: str, arguments: dict) -> dict:
    try:
        if name == "add_expense":
            transaction = await create_transaction(db, user_id, TransactionCreate.model_validate({**arguments, "transaction_type": "expense"}))
            return {"saved": True, "transaction": _transaction_result(transaction)}
        if name == "get_spending_summary":
            from_date, to_date = date.fromisoformat(arguments["from_date"]), date.fromisoformat(arguments["to_date"])
            if from_date > to_date:
                raise ValueError("from_date must be before to_date")
            return (await spending_summary(db, user_id, from_date, to_date)).model_dump(mode="json")
        if name == "set_budget":
            budget = await create_budget(db, user_id, BudgetCreate.model_validate(arguments))
            return {"saved": True, "budget": _budget_result(budget)}
        if name == "get_budget_status":
            day = date.fromisoformat(arguments["as_of"]) if arguments.get("as_of") else date.today()
            rows = await db.execute(select(Budget).where(Budget.user_id == user_id, Budget.period_start <= day, Budget.period_end >= day))
            budgets = []
            for budget in rows.scalars().all():
                item = await budget_status(db, user_id, budget)
                budgets.append({"budget": _budget_result(budget), "spent": str(item["spent"]), "remaining": str(item["remaining"]), "percentage_used": str(item["percentage_used"])})
            return {"as_of": day.isoformat(), "budgets": budgets}
        return {"error": f"Unknown action: {name}"}
    except Exception as exc:
        return {"error": str(exc)}


def _expense_category(description: str) -> str:
    food_terms = {"biriyani", "biryani", "food", "dinner", "lunch", "breakfast", "restaurant", "groceries"}
    return "Food" if any(term in description.lower() for term in food_terms) else "Other"


async def _fast_reply(db: AsyncSession, user_id: int, message: str) -> tuple[str, list[str]] | None:
    text = message.strip().lower()
    if text in {"hi", "hello", "hey", "hello jarvis", "hi jarvis"}:
        return "Hello! I can add expenses, show spending summaries, and check your budgets. What would you like to do?", []
    if text in {"show my expenses", "show expenses", "my expenses"}:
        return "Tell me a period such as 'last 7 days' or 'this month'.", []
    days_match = re.fullmatch(r"last\s+(\d{1,3})\s+days?", text)
    if days_match:
        days = int(days_match.group(1))
        if days < 1:
            return "Please provide at least one day.", []
        to_date = date.today()
        result = (await spending_summary(db, user_id, to_date - timedelta(days=days - 1), to_date)).model_dump(mode="json")
        return _format_tool_reply("get_spending_summary", result), ["get_spending_summary"]
    expense_match = re.fullmatch(r"(?:i\s+)?(?:spent|spend|paid)\s+(?:₹|rs\.?|inr\s*)?(\d+(?:\.\d{1,2})?)\s+(?:for|on|at)\s+(.+?)(?:\s+today)?", text)
    if expense_match:
        amount, description = expense_match.groups()
        transaction = await create_transaction(db, user_id, TransactionCreate(amount=amount, transaction_type="expense", category=_expense_category(description), merchant=description.title()))
        return _format_tool_reply("add_expense", {"saved": True, "transaction": _transaction_result(transaction)}), ["add_expense"]
    return None


def _intent_arguments(intent: FinanceIntent) -> dict:
    fields = intent.model_dump(exclude_none=True)
    fields.pop("action", None)
    fields.pop("reply", None)
    return fields


async def generate_finance_reply(db: AsyncSession, user_id: int, message: str) -> tuple[str, list[str]]:
    fast_reply = await _fast_reply(db, user_id, message)
    if fast_reply:
        return fast_reply
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = (
        "Classify the user's finance message into exactly one action. Today is " + date.today().isoformat() + ". "
        "Choose conversation for greetings, general questions, or when required action details are missing; place the answer or follow-up question in reply. "
        "For add_expense, provide amount, category, and any known merchant, notes, and transaction_date. "
        "For get_spending_summary, provide from_date and to_date in ISO YYYY-MM-DD. "
        "For set_budget, provide category, amount, period_start, and period_end in ISO YYYY-MM-DD. "
        "For get_budget_status, as_of is optional. Never invent financial results.\n\nUser: " + message
    )

    models_to_try = [settings.GEMINI_MODEL, "gemini-3.1-flash-lite", "gemini-flash-latest"]
    # Deduplicate while preserving order
    unique_models = list(dict.fromkeys(models_to_try))

    response_text = None
    for model_name in unique_models:
        for attempt in range(2):
            try:
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=FinanceIntent,
                    ),
                )
                response_text = response.text
                break
            except Exception as exc:
                print(f"========== GEMINI ERROR ({model_name}, Attempt {attempt + 1}) ==========")
                print(f"{type(exc)}: {exc}")
                print("==============================================================")
                await asyncio.sleep(1)
        if response_text:
            break

    if not response_text:
        return "I'm sorry, but my AI service is currently experiencing high demand or rate limits. Please try again in a moment.", []

    try:
        intent = FinanceIntent.model_validate_json(response_text)
    except Exception:
        return "I received an invalid response from the AI service. Please try again.", []

    if intent.action == "conversation":
        return intent.reply or "How can I help with your finances?", []
    result = await _run_tool(db, user_id, intent.action, _intent_arguments(intent))
    return _format_tool_reply(intent.action, result), [intent.action]
