from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import ValidationError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.transaction import Transaction, TransactionSource, TransactionStatus
from app.models.exception import ExceptionRecord, ExceptionType, ExceptionPriority
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.schemas.batch import BatchIngestResponse, RejectedItem


class TransactionService:
    @staticmethod
    def create_transaction(db: Session, tx_in: TransactionCreate) -> Transaction:
        existing = db.query(Transaction).filter(
            Transaction.reference == tx_in.reference,
            Transaction.source == tx_in.source.value
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Transaction with reference '{tx_in.reference}' from source '{tx_in.source.value}' already exists."
            )

        db_tx = Transaction(
            reference=tx_in.reference,
            account_id=tx_in.account_id,
            amount=tx_in.amount,
            currency=tx_in.currency,
            transaction_date=tx_in.transaction_date,
            source=tx_in.source.value,
        )
        db.add(db_tx)
        db.commit()
        db.refresh(db_tx)
        return db_tx

    @staticmethod
    def ingest_batch(db: Session, records: List[Dict[str, Any]]) -> BatchIngestResponse:
        accepted_txs: List[Transaction] = []
        rejected_items: List[RejectedItem] = []

        for idx, raw in enumerate(records):
            try:
                # Validate individual record using Pydantic
                tx_in = TransactionCreate(**raw)

                # Check duplicate within this source
                existing = db.query(Transaction).filter(
                    Transaction.reference == tx_in.reference,
                    Transaction.source == tx_in.source.value
                ).first()

                if existing:
                    rejected_items.append(RejectedItem(
                        index=idx,
                        raw_record=raw,
                        error_reason=f"Duplicate reference '{tx_in.reference}' for source '{tx_in.source.value}'."
                    ))
                    continue

                db_tx = Transaction(
                    reference=tx_in.reference,
                    account_id=tx_in.account_id,
                    amount=tx_in.amount,
                    currency=tx_in.currency,
                    transaction_date=tx_in.transaction_date,
                    source=tx_in.source.value,
                )
                db.add(db_tx)
                db.flush()  # assign ID without full commit
                accepted_txs.append(db_tx)

            except (ValidationError, ValueError, TypeError) as err:
                error_msg = str(err)
                rejected_items.append(RejectedItem(
                    index=idx,
                    raw_record=raw,
                    error_reason=error_msg
                ))

                # Create audit exception for bad external statement row
                exc = ExceptionRecord(
                    transaction_id=None,
                    exception_type=ExceptionType.INVALID_STATEMENT_RECORD.value,
                    description=f"Batch row {idx} rejected: {error_msg}",
                    priority=ExceptionPriority.MEDIUM.value
                )
                db.add(exc)

        db.commit()
        for tx in accepted_txs:
            db.refresh(tx)

        return BatchIngestResponse(
            total_received=len(records),
            accepted_count=len(accepted_txs),
            rejected_count=len(rejected_items),
            accepted_transactions=[TransactionResponse.model_validate(tx) for tx in accepted_txs],
            rejected_items=rejected_items
        )

    @staticmethod
    def get_transaction_by_id(db: Session, tx_id: int) -> Optional[Transaction]:
        return db.query(Transaction).filter(Transaction.id == tx_id).first()

    @staticmethod
    def list_transactions(
        db: Session, 
        source: Optional[TransactionSource] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Transaction]:
        query = db.query(Transaction)
        if source:
            query = query.filter(Transaction.source == source.value)
        return query.offset(skip).limit(limit).all()


transaction_service = TransactionService()
