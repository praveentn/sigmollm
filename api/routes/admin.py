from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

import ollama_client
from auth import generate_key, hash_key, require_admin
from config import settings
from db.database import get_db
from db.models import ApiKey, UsageLog

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class CreateKeyRequest(BaseModel):
    name: str
    rpm_limit: int = settings.default_rpm
    rpd_limit: int = settings.default_rpd


class UpdateKeyRequest(BaseModel):
    name: Optional[str] = None
    rpm_limit: Optional[int] = None
    rpd_limit: Optional[int] = None
    is_active: Optional[bool] = None


class PullModelRequest(BaseModel):
    name: str


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(ApiKey.id)))).scalar()
    active = (await db.execute(
        select(func.count(ApiKey.id)).where(ApiKey.is_active == True)
    )).scalar()

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    req_today = (await db.execute(
        select(func.count(UsageLog.id)).where(UsageLog.created_at >= today)
    )).scalar()

    req_total = (await db.execute(select(func.count(UsageLog.id)))).scalar()

    models = await ollama_client.list_models()

    return {
        "total_keys": total,
        "active_keys": active,
        "requests_today": req_today,
        "requests_total": req_total,
        "models": models,
    }


# ── Key management ───────────────────────────────────────────────────────────

@router.get("/keys")
async def list_keys(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ApiKey).order_by(desc(ApiKey.created_at)))
    keys = result.scalars().all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "is_active": k.is_active,
            "rpm_limit": k.rpm_limit,
            "rpd_limit": k.rpd_limit,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


@router.post("/keys", status_code=201)
async def create_key(
    req: CreateKeyRequest,
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    raw = generate_key()
    api_key = ApiKey(
        name=req.name,
        key_prefix=raw[:10],
        key_hash=hash_key(raw),
        rpm_limit=req.rpm_limit,
        rpd_limit=req.rpd_limit,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": raw,  # shown once
        "key_prefix": api_key.key_prefix,
        "rpm_limit": api_key.rpm_limit,
        "rpd_limit": api_key.rpd_limit,
        "created_at": api_key.created_at.isoformat(),
    }


@router.patch("/keys/{key_id}")
async def update_key(
    key_id: str,
    req: UpdateKeyRequest,
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if req.name is not None:
        api_key.name = req.name
    if req.rpm_limit is not None:
        api_key.rpm_limit = req.rpm_limit
    if req.rpd_limit is not None:
        api_key.rpd_limit = req.rpd_limit
    if req.is_active is not None:
        api_key.is_active = req.is_active

    await db.commit()
    return {"message": "Updated"}


@router.delete("/keys/{key_id}")
async def delete_key(
    key_id: str,
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(api_key)
    await db.commit()
    return {"message": "Deleted"}


# ── Usage ────────────────────────────────────────────────────────────────────

@router.get("/usage")
async def get_usage(
    _: None = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    api_key_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    since = datetime.utcnow() - timedelta(days=days)
    q = (
        select(UsageLog, ApiKey.name.label("key_name"))
        .join(ApiKey)
        .where(UsageLog.created_at >= since)
        .order_by(desc(UsageLog.created_at))
        .limit(limit)
        .offset(offset)
    )
    if api_key_id:
        q = q.where(UsageLog.api_key_id == api_key_id)

    rows = (await db.execute(q)).all()
    return [
        {
            "id": r.UsageLog.id,
            "api_key_id": r.UsageLog.api_key_id,
            "key_name": r.key_name,
            "endpoint": r.UsageLog.endpoint,
            "model": r.UsageLog.model,
            "prompt_tokens": r.UsageLog.prompt_tokens,
            "completion_tokens": r.UsageLog.completion_tokens,
            "latency_ms": r.UsageLog.latency_ms,
            "success": r.UsageLog.success,
            "created_at": r.UsageLog.created_at.isoformat(),
        }
        for r in rows
    ]


# ── Model management ─────────────────────────────────────────────────────────

@router.get("/models")
async def admin_list_models(_: None = Depends(require_admin)):
    return {"models": await ollama_client.list_models()}


@router.post("/models/pull")
async def pull_model(req: PullModelRequest, _: None = Depends(require_admin)):
    try:
        await ollama_client.pull_model(req.name)
        return {"message": f"Model '{req.name}' pulled successfully"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/models/{model_name:path}")
async def delete_model(model_name: str, _: None = Depends(require_admin)):
    try:
        await ollama_client.delete_model(model_name)
        return {"message": f"Model '{model_name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
