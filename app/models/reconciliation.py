from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
import enum
from app.db.session import Base


class MatchType(str, enum.Enum):
    EXACT_MATCH = "EXACT_MATCH"
    UNMATCHED = "UNMATCHED"


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    internal_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    external_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    match_type = Column(String(32), nullable=False)
    difference_amount = Column(Numeric(precision=18, scale=2), default=Decimal("0.00"), nullable=False)
    reason = Column(String(255), nullable=True)
    reconciled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
