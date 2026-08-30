from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.reconciliation import MatchType


class ReconciliationSummaryResponse(BaseModel):
    batch_id: str
    total_processed: int
    matched_count: int
    unmatched_count: int
    exceptions_created: int
    executed_at: datetime


class ReconciliationResultResponse(BaseModel):
    id: int
    internal_transaction_id: Optional[int]
    external_transaction_id: Optional[int]
    match_type: MatchType
    difference_amount: Decimal
    reason: Optional[str]
    reconciled_at: datetime

    model_config = ConfigDict(from_attributes=True)
