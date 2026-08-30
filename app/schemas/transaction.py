from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.transaction import TransactionSource, TransactionStatus


class TransactionBase(BaseModel):
    reference: str = Field(..., min_length=3, max_length=64, json_schema_extra={"example": "CEB-TRX-10001"})
    account_id: str = Field(..., min_length=3, max_length=64, json_schema_extra={"example": "SETTLEMENT-001"})
    amount: Decimal = Field(..., gt=0, decimal_places=2, json_schema_extra={"example": "2500000.00"})
    currency: str = Field(default="EUR", min_length=3, max_length=3, json_schema_extra={"example": "EUR"})
    transaction_date: Union[date, datetime, str] = Field(..., json_schema_extra={"example": "2026-08-29"})
    source: TransactionSource = Field(..., json_schema_extra={"example": TransactionSource.INTERNAL})

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.upper() != "EUR":
            raise ValueError("Only EUR currency is currently supported by CEB-Ledger")
        return v.upper()

    @field_validator("transaction_date", mode="before")
    @classmethod
    def normalize_transaction_date(cls, v: Union[str, date, datetime]) -> date:
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            clean_str = v.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(clean_str)
                return dt.date()
            except ValueError:
                raise ValueError(f"Invalid date format: '{v}'. Expected ISO format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")
        raise ValueError("Invalid date type")


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: int
    status: TransactionStatus
    transaction_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
