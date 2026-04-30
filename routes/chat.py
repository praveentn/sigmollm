from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import ollama_client
from auth import get_api_key
from config import settings
from db.database import get_db
from db.models import ApiKey, UsageLog
from rate_limit import check_rate_limit

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    model: str | None = None
    options: dict | None = None


@router.post("/chat")
async def chat(
    req: ChatRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(api_key, db)

    model = req.model or settings.default_model
    messages = [m.model_dump() for m in req.messages]

    success = True
    latency_ms = 0
    result: dict = {}
    error: str = ""

    try:
        result = await ollama_client.chat(model, messages, req.options)
        latency_ms = result.get("latency_ms", 0)
    except Exception as e:
        success = False
        error = str(e)

    log = UsageLog(
        api_key_id=api_key.id,
        endpoint="/api/chat",
        model=model,
        prompt_tokens=result.get("prompt_eval_count", 0),
        completion_tokens=result.get("eval_count", 0),
        latency_ms=latency_ms,
        success=success,
    )
    db.add(log)
    await db.commit()

    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail=error)

    pt = result.get("prompt_eval_count", 0)
    ct = result.get("eval_count", 0)
    return {
        "model": model,
        "message": result.get("message", {}),
        "done": result.get("done", True),
        "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct},
        "latency_ms": latency_ms,
    }
