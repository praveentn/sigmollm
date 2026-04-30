import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.database import get_db
from db.models import ApiKey

_bearer = HTTPBearer()


# ── API key helpers ──────────────────────────────────────────────────────────

def generate_key() -> str:
    return f"sk-{secrets.token_hex(24)}"


def hash_key(raw: str) -> str:
    return hashlib.sha256(f"{raw}{settings.secret_key}".encode()).hexdigest()


async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    key_hash = hash_key(credentials.credentials)
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key


# ── Admin JWT helpers ────────────────────────────────────────────────────────

def create_admin_token() -> str:
    payload = {
        "sub": "admin",
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_admin_token(token: str) -> bool:
    try:
        jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return True
    except Exception:
        return False


def require_admin(
    request: Request,
    x_admin_key: str | None = Header(default=None),
) -> None:
    if x_admin_key and x_admin_key == settings.admin_api_key:
        return
    token = request.cookies.get(settings.cookie_name)
    if token and verify_admin_token(token):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin access required",
    )
