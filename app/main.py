from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.api.routes.expenses import router as expense_router
from app.api.routes.budgets import router as budget_router
from app.api.routes.chat import router as chat_router
from app.db.session import engine

app = FastAPI(
    title="SmartExp v2 API",
    version="2.0.0",
    description="Backend API for SmartExp personal finance assistant",
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(expense_router)
app.include_router(budget_router)
app.include_router(chat_router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "SmartExp v2 Backend"}


@app.get("/db-test", tags=["Health"])
async def db_test():
    async with engine.begin() as connection:
        result = await connection.execute(text("SELECT 1"))
        return {"database": result.scalar()}
        return {"database": result.scalar()}
