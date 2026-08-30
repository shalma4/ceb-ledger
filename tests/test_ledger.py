from decimal import Decimal


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "CEB-Ledger"}


def test_create_transaction_success(client):
    payload = {
        "reference": "CEB-TEST-001",
        "account_id": "ACC-01",
        "amount": "1000000.50",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "INTERNAL"
    }
    response = client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["reference"] == "CEB-TEST-001"
    assert data["amount"] == "1000000.50"
    assert data["status"] == "PENDING"


def test_create_duplicate_transaction_conflict(client):
    payload = {
        "reference": "CEB-TEST-DUP",
        "account_id": "ACC-01",
        "amount": "500.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "INTERNAL"
    }
    # First creation should succeed
    res1 = client.post("/api/v1/transactions/", json=payload)
    assert res1.status_code == 201

    # Second creation with identical source and reference must return 409 Conflict
    res2 = client.post("/api/v1/transactions/", json=payload)
    assert res2.status_code == 409


def test_reconciliation_exact_match(client):
    # 1. Create Internal Transaction
    client.post("/api/v1/transactions/", json={
        "reference": "CEB-REC-001",
        "account_id": "SETTLE-1",
        "amount": "2500000.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "INTERNAL"
    })

    # 2. Create matching External Transaction
    client.post("/api/v1/transactions/", json={
        "reference": "CEB-REC-001",
        "account_id": "SETTLE-1",
        "amount": "2500000.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "EXTERNAL"
    })

    # 3. Run reconciliation
    rec_res = client.post("/api/v1/reconciliation/run")
    assert rec_res.status_code == 200
    summary = rec_res.json()
    assert summary["matched_count"] == 2
    assert summary["unmatched_count"] == 0
    assert summary["exceptions_created"] == 0


def test_reconciliation_amount_mismatch_creates_exception(client):
    # 1. Internal transaction
    client.post("/api/v1/transactions/", json={
        "reference": "CEB-MISMATCH-001",
        "account_id": "SETTLE-1",
        "amount": "2500000.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "INTERNAL"
    })

    # 2. External transaction with 500 EUR difference
    client.post("/api/v1/transactions/", json={
        "reference": "CEB-MISMATCH-001",
        "account_id": "SETTLE-1",
        "amount": "2499500.00",
        "currency": "EUR",
        "transaction_date": "2026-08-29",
        "source": "EXTERNAL"
    })

    # 3. Run reconciliation
    rec_res = client.post("/api/v1/reconciliation/run")
    assert rec_res.status_code == 200
    summary = rec_res.json()
    assert summary["matched_count"] == 0
    assert summary["unmatched_count"] == 2
    assert summary["exceptions_created"] == 1

    # 4. Verify Exception Record exists
    exc_res = client.get("/api/v1/exceptions/")
    assert exc_res.status_code == 200
    exceptions = exc_res.json()
    assert len(exceptions) == 1
    assert exceptions[0]["exception_type"] == "AMOUNT_MISMATCH"
    assert exceptions[0]["status"] == "OPEN"
