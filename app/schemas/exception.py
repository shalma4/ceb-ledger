from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.exception import ExceptionType, ExceptionStatus, ExceptionPriority


class ExceptionRecordResponse(BaseModel):
    id: int
    transaction_id: Optional[int]
    exception_type: ExceptionType
    description: str
    status: ExceptionStatus
    priority: ExceptionPriority
    resolution_notes: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ExceptionResolveRequest(BaseModel):
    resolution_notes: str = Field(
        ..., 
        min_length=5, 
        json_schema_extra={"example": "Adjusted via manual settlement entry #9021"}
    )
