import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from fastapi import status
from fastapi.encoders import jsonable_encoder

from app.core.money import quantize_amount
from app.models.transaction import Transaction, TransactionSource, TransactionStatus
from app.models.reconciliation import ReconciliationResult, MatchType
from app.models.exception import ExceptionRecord, ExceptionType, ExceptionPriority
from app.models.idempotency import IdempotencyRecord
from app.schemas.reconciliation import ReconciliationSummaryResponse


class ReconciliationService:
    @staticmethod
    def run_reconciliation(
        db: Session, 
        idempotency_key: Optional[str] = None
    ) -> ReconciliationSummaryResponse:
        if idempotency_key:
            existing_record = db.query(IdempotencyRecord).filter(
                IdempotencyRecord.key == idempotency_key
            ).first()
            if existing_record:
                return ReconciliationSummaryResponse(**existing_record.response_body)

        batch_id = str(uuid.uuid4())[:8]

        internal_txs: List[Transaction] = db.query(Transaction).filter(
            Transaction.source == TransactionSource.INTERNAL.value,
            Transaction.status == TransactionStatus.PENDING.value
        ).all()

        external_txs: List[Transaction] = db.query(Transaction).filter(
            Transaction.source == TransactionSource.EXTERNAL.value,
            Transaction.status == TransactionStatus.PENDING.value
        ).all()

        matched_count = 0
        unmatched_count = 0
        exceptions_created = 0

        external_by_ref: Dict[str, Transaction] = {tx.reference: tx for tx in external_txs}
        processed_external_ids = set()

        for int_tx in internal_txs:
            ext_tx = external_by_ref.get(int_tx.reference)

            if not ext_tx:
                int_tx.status = TransactionStatus.UNMATCHED.value
                unmatched_count += 1
                exceptions_created += 1

                rec_result = ReconciliationResult(
                    internal_transaction_id=int_tx.id,
                    external_transaction_id=None,
                    match_type=MatchType.UNMATCHED.value,
                    difference_amount=quantize_amount(int_tx.amount),
                    reason="Missing corresponding external transaction"
                )
                db.add(rec_result)

                exc = ExceptionRecord(
                    transaction_id=int_tx.id,
                    exception_type=ExceptionType.MISSING_EXTERNAL_TRANSACTION.value,
                    description=f"Internal transaction {int_tx.reference} has no matching external statement record.",
                    priority=ExceptionPriority.HIGH.value
                )
                db.add(exc)
                continue

            processed_external_ids.add(ext_tx.id)

            # Strict Banking Decimal Quantization & Comparison
            int_amount = quantize_amount(int_tx.amount)
            ext_amount = quantize_amount(ext_tx.amount)
            amount_diff = abs(int_amount - ext_amount)

            if amount_diff > Decimal("0.00"):
                int_tx.status = TransactionStatus.UNMATCHED.value
                ext_tx.status = TransactionStatus.UNMATCHED.value
                unmatched_count += 2
                exceptions_created += 1

                rec_result = ReconciliationResult(
                    internal_transaction_id=int_tx.id,
                    external_transaction_id=ext_tx.id,
                    match_type=MatchType.UNMATCHED.value,
                    difference_amount=amount_diff,
                    reason=f"Amount mismatch: Internal={int_amount}, External={ext_amount}"
                )
                db.add(rec_result)

                exc = ExceptionRecord(
                    transaction_id=int_tx.id,
                    exception_type=ExceptionType.AMOUNT_MISMATCH.value,
                    description=f"Transaction {int_tx.reference} amount mismatch: Diff={amount_diff} EUR.",
                    priority=ExceptionPriority.HIGH.value
                )
                db.add(exc)
                continue

            # Date Check
            if int_tx.transaction_date != ext_tx.transaction_date:
                int_tx.status = TransactionStatus.UNMATCHED.value
                ext_tx.status = TransactionStatus.UNMATCHED.value
                unmatched_count += 2
                exceptions_created += 1

                rec_result = ReconciliationResult(
                    internal_transaction_id=int_tx.id,
                    external_transaction_id=ext_tx.id,
                    match_type=MatchType.UNMATCHED.value,
                    difference_amount=Decimal("0.00"),
                    reason=f"Date mismatch: Internal={int_tx.transaction_date}, External={ext_tx.transaction_date}"
                )
                db.add(rec_result)

                exc = ExceptionRecord(
                    transaction_id=int_tx.id,
                    exception_type=ExceptionType.DATE_MISMATCH.value,
                    description=f"Transaction {int_tx.reference} date mismatch: Internal={int_tx.transaction_date}, External={ext_tx.transaction_date}.",
                    priority=ExceptionPriority.MEDIUM.value
                )
                db.add(exc)
                continue

            # Matched
            int_tx.status = TransactionStatus.MATCHED.value
            ext_tx.status = TransactionStatus.MATCHED.value
            matched_count += 2

            rec_result = ReconciliationResult(
                internal_transaction_id=int_tx.id,
                external_transaction_id=ext_tx.id,
                match_type=MatchType.EXACT_MATCH.value,
                difference_amount=Decimal("0.00"),
                reason="Exact reference, amount, and date match."
            )
            db.add(rec_result)

        for ext_tx in external_txs:
            if ext_tx.id not in processed_external_ids:
                ext_tx.status = TransactionStatus.UNMATCHED.value
                unmatched_count += 1
                exceptions_created += 1

                rec_result = ReconciliationResult(
                    internal_transaction_id=None,
                    external_transaction_id=ext_tx.id,
                    match_type=MatchType.UNMATCHED.value,
                    difference_amount=quantize_amount(ext_tx.amount),
                    reason="Missing corresponding internal transaction"
                )
                db.add(rec_result)

                exc = ExceptionRecord(
                    transaction_id=ext_tx.id,
                    exception_type=ExceptionType.MISSING_INTERNAL_TRANSACTION.value,
                    description=f"External transaction {ext_tx.reference} has no internal system record.",
                    priority=ExceptionPriority.HIGH.value
                )
                db.add(exc)

        total_processed = len(internal_txs) + len(external_txs)
        summary = ReconciliationSummaryResponse(
            batch_id=batch_id,
            total_processed=total_processed,
            matched_count=matched_count,
            unmatched_count=unmatched_count,
            exceptions_created=exceptions_created,
            executed_at=datetime.now(timezone.utc)
        )

        if idempotency_key:
            idempotency_entry = IdempotencyRecord(
                key=idempotency_key,
                endpoint="/api/v1/reconciliation/run",
                response_code=status.HTTP_200_OK,
                response_body=jsonable_encoder(summary)
            )
            db.add(idempotency_entry)

        db.commit()
        return summary


reconciliation_service = ReconciliationService()
