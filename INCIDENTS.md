# CEB-Ledger Incident Management & Jira Backlog

---

## [RESOLVED] Ticket ID: CEB-INC-1042
- **Type:** Incident (Production Bug)
- **Severity:** P2 - High
- **Summary:** Valid external transactions marked as UNMATCHED due to ISO 8601 UTC timestamp format.
- **Fix:** Implemented pre-validation normalization in `app/schemas/transaction.py`. Added regression test `test_incident_1_iso_timestamp_normalization`.

---

## [RESOLVED] Ticket ID: CEB-INC-1043
- **Type:** Incident (Data Integrity / Idempotency)
- **Severity:** P1 - Critical
- **Summary:** Duplicate reconciliation executions process identical settlement batches twice.
- **Fix:** Added `IdempotencyRecord` table and header-level caching in `app/services/reconciliation_service.py`. Added regression test `test_incident_2_idempotent_reconciliation_replay`.

---

## [RESOLVED] Ticket ID: CEB-INC-1044
- **Type:** Incident (Financial Accuracy)
- **Severity:** P1 - Critical
- **Summary:** Floating-point rounding inaccuracies detected during high-value ledger operations.
- **Fix:** Created `app/core/money.py` to enforce Decimal arithmetic and `ROUND_HALF_EVEN` quantization. Added regression test `test_incident_3_monetary_precision_quantization`.

---

## [RESOLVED] Ticket ID: CEB-INC-1045
- **Type:** Incident (Resilience / Ingestion Fault Tolerance)
- **Severity:** P3 - Medium
- **Summary:** Corrupted external statement batch feeds crash the ingestion pipeline.
- **Fix:** Implemented `POST /api/v1/transactions/batch` with partial-failure error isolation and exception generation. Added regression test `test_incident_4_resilient_batch_statement_ingestion`.

---

## [RESOLVED] Ticket ID: CEB-INC-1046
- **Type:** Performance Degradation
- **Severity:** P2 - High
- **Summary:** Reconciliation job degrades across large datasets due to unindexed queries and $O(N)$ ORM lookups.
- **Fix:** Added composite database indexes `idx_tx_source_status` and `idx_tx_ref_source` on `transactions` table. Added performance benchmark regression test `test_incident_5_bulk_reconciliation_performance`.
