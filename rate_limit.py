from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ApiKey, UsageLog


async def check_rate_limit(api_key: ApiKey, db: AsyncSession) -> None:
    now = datetime.utcnow()

    rpm_result = await db.execute(
        select(func.count(UsageLog.id)).where(
            UsageLog.api_key_id == api_key.id,
            UsageLog.created_at >= now - timedelta(minutes=1),
        )
    )
    if rpm_result.scalar() >= api_key.rpm_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {api_key.rpm_limit} req/min",
            headers={"Retry-After": "60"},
        )

    rpd_result = await db.execute(
        select(func.count(UsageLog.id)).where(
            UsageLog.api_key_id == api_key.id,
            UsageLog.created_at >= now - timedelta(days=1),
        )
    )
    if rpd_result.scalar() >= api_key.rpd_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily rate limit exceeded: {api_key.rpd_limit} req/day",
            headers={"Retry-After": "86400"},
        )
