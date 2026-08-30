from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.db.session import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(128), unique=True, index=True, nullable=False)
    endpoint = Column(String(128), nullable=False)
    response_code = Column(Integer, nullable=False)
    response_body = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
