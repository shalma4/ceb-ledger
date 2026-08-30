import time
from decimal import Decimal


def test_incident_1_iso_timestamp_normalization(client):
    """CEB-INC-1042: External ISO 8601 timestamps normalized to calendar date."""
    client.post("/api/v1/transactions/", json={
        "reference": "CEB-SETTLE-8801",
        "account_id": "ACC-EUR-01",
        "amount": "1750000.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "INTERNAL"
    })

    ext_res = client.post("/api/v1/transactions/", json={
        "reference": "CEB-SETTLE-8801",
        "account_id": "ACC-EUR-01",
        "amount": "1750000.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29T18:45:00Z",
        "source": "EXTERNAL"
    })
    assert ext_res.status_code == 201

    rec_res = client.post("/api/v1/reconciliation/run")
    assert rec_res.status_code == 200
    summary = rec_res.json()

    assert summary["matched_count"] == 2
    assert summary["unmatched_count"] == 0
    assert summary["exceptions_created"] == 0


def test_incident_2_idempotent_reconciliation_replay(client):
    """CEB-INC-1043: Replaying reconciliation with same Idempotency-Key returns cached result."""
    client.post("/api/v1/transactions/", json={
        "reference": "CEB-IDEM-001",
        "account_id": "ACC-01",
        "amount": "500000.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "INTERNAL"
    })
    client.post("/api/v1/transactions/", json={
        "reference": "CEB-IDEM-001",
        "account_id": "ACC-01",
        "amount": "500000.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "EXTERNAL"
    })

    headers = {"Idempotency-Key": "IDEM-KEY-SETTLEMENT-20260829"}

    res1 = client.post("/api/v1/reconciliation/run", headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    first_batch_id = data1["batch_id"]

    res2 = client.post("/api/v1/reconciliation/run", headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["batch_id"] == first_batch_id
    assert data2["matched_count"] == 2


def test_incident_3_monetary_precision_quantization(client):
    """CEB-INC-1044: Strict 2-decimal financial quantization."""
    client.post("/api/v1/transactions/", json={
        "reference": "CEB-PRECISION-9901",
        "account_id": "ACC-TREASURY",
        "amount": "2500000.10",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "INTERNAL"
    })

    client.post("/api/v1/transactions/", json={
        "reference": "CEB-PRECISION-9901",
        "account_id": "ACC-TREASURY",
        "amount": "2500000.10",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "EXTERNAL"
    })

    rec_res = client.post("/api/v1/reconciliation/run")
    assert rec_res.status_code == 200
    summary = rec_res.json()

    assert summary["matched_count"] == 2
    assert summary["unmatched_count"] == 0
    assert summary["exceptions_created"] == 0


def test_incident_4_resilient_batch_statement_ingestion(client):
    """CEB-INC-1045: Resilient batch ingestion with error isolation."""
    batch_payload = [
        {
            "reference": "CEB-BATCH-001",
            "account_id": "ACC-BATCH",
            "amount": "120000.00",
            "currency": "EUR",
            "transaction_date": "2026-08-29",
            "source": "EXTERNAL"
        },
        {
            "reference": "CEB-BATCH-BAD",
            "account_id": "ACC-BATCH",
            "amount": "99000.00",
            "currency": "USD",
            "transaction_date": "2026-08-29",
            "source": "EXTERNAL"
        },
        {
            "reference": "CEB-BATCH-002",
            "account_id": "ACC-BATCH",
            "amount": "340000.00",
            "currency": "EUR",
            "transaction_date": "2026-08-29",
            "source": "EXTERNAL"
        }
    ]

    res = client.post("/api/v1/transactions/batch", json=batch_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_received"] == 3
    assert data["accepted_count"] == 2
    assert data["rejected_count"] == 1
    assert data["rejected_items"][0]["index"] == 1


def test_incident_5_bulk_reconciliation_performance(client):
    """
    CEB-INC-1046: Fast execution on high-volume transactions (200 records)
    ensuring index-backed queries and bulk in-memory hash-joins run sub-second.
    """
    internal_batch = []
    external_batch = []

    for i in range(100):
        ref = f"CEB-PERF-{i:04d}"
        internal_batch.append({
            "reference": ref,
            "account_id": "ACC-BULK",
            "amount": "50000.00",
            "currency": "EUR",
            "transaction_date": "2026-08-29",
            "source": "INTERNAL"
        })
        external_batch.append({
            "reference": ref,
            "account_id": "ACC-BULK",
            "amount": "50000.00",
            "currency": "EUR",
            "transaction_date": "2026-08-29",
            "source": "EXTERNAL"
        })

    # Ingest bulk records
    client.post("/api/v1/transactions/batch", json=internal_batch)
    client.post("/api/v1/transactions/batch", json=external_batch)

    # Benchmark reconciliation run time
    start_time = time.perf_counter()
    rec_res = client.post("/api/v1/reconciliation/run")
    duration = time.perf_counter() - start_time

    assert rec_res.status_code == 200
    summary = rec_res.json()
    assert summary["matched_count"] == 200
    assert summary["unmatched_count"] == 0
    # Must complete fast (well under 1.5 seconds)
    assert duration < 1.5
