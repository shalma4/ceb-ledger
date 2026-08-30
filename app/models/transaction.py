from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Index
import enum
from app.db.session import Base


class TransactionSource(str, enum.Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reference = Column(String(64), index=True, nullable=False)
    account_id = Column(String(64), index=True, nullable=False)
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    transaction_date = Column(Date, nullable=False)
    source = Column(String(16), nullable=False)
    status = Column(String(16), default=TransactionStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_tx_source_status", "source", "status"),
        Index("idx_tx_ref_source", "reference", "source"),
    )
