from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai import generate_finance_reply

router = APIRouter(prefix="/chat", tags=["Jarvis"])


@router.post("/", response_model=ChatResponse)
async def chat(data: ChatRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ChatResponse:
    try:
        reply, actions = await generate_finance_reply(db, current_user.id, data.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Gemini service is unavailable") from exc
    return ChatResponse(reply=reply, model="gemini", actions=actions)
