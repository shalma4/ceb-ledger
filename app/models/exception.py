from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
import enum
from app.db.session import Base


class ExceptionType(str, enum.Enum):
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    MISSING_EXTERNAL_TRANSACTION = "MISSING_EXTERNAL_TRANSACTION"
    MISSING_INTERNAL_TRANSACTION = "MISSING_INTERNAL_TRANSACTION"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    INVALID_STATEMENT_RECORD = "INVALID_STATEMENT_RECORD"


class ExceptionStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class ExceptionPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    exception_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(16), default=ExceptionStatus.OPEN.value, nullable=False)
    priority = Column(String(16), default=ExceptionPriority.HIGH.value, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
