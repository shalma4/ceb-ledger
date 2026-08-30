from typing import Optional
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.reconciliation import ReconciliationSummaryResponse
from app.services.reconciliation_service import reconciliation_service

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.post("/run", response_model=ReconciliationSummaryResponse, status_code=status.HTTP_200_OK)
def run_reconciliation(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    return reconciliation_service.run_reconciliation(db=db, idempotency_key=idempotency_key)
