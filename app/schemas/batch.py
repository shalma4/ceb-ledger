from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas.transaction import TransactionResponse


class RejectedItem(BaseModel):
    index: int
    raw_record: Dict[str, Any]
    error_reason: str


class BatchIngestResponse(BaseModel):
    total_received: int
    accepted_count: int
    rejected_count: int
    accepted_transactions: List[TransactionResponse]
    rejected_items: List[RejectedItem]
