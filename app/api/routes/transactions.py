from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.schemas.batch import BatchIngestResponse
from app.models.transaction import TransactionSource
from app.services.transaction_service import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_in: TransactionCreate, 
    db: Session = Depends(get_db)
):
    return transaction_service.create_transaction(db=db, tx_in=tx_in)


@router.post("/batch", response_model=BatchIngestResponse, status_code=status.HTTP_200_OK)
def ingest_batch_transactions(
    records: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    return transaction_service.ingest_batch(db=db, records=records)


@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    source: Optional[TransactionSource] = Query(None, description="Filter by INTERNAL or EXTERNAL"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return transaction_service.list_transactions(db=db, source=source, skip=skip, limit=limit)


@router.get("/{tx_id}", response_model=TransactionResponse)
def get_transaction(
    tx_id: int, 
    db: Session = Depends(get_db)
):
    tx = transaction_service.get_transaction_by_id(db=db, tx_id=tx_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Transaction with ID {tx_id} not found."
        )
    return tx
