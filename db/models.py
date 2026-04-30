import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    rpm_limit = Column(Integer, nullable=False)
    rpd_limit = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    usage_logs = relationship("UsageLog", back_populates="api_key")


class UsageLog(Base):
    __tablename__ = "usage_logs"
    __table_args__ = (
        Index("ix_usage_logs_api_key_created", "api_key_id", "created_at"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id = Column(String, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    api_key = relationship("ApiKey", back_populates="usage_logs")
