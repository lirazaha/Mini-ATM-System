from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_balance_seed():
    r = client.get("/accounts/1001/balance")
    assert r.status_code == 200
    j = r.json()
    assert j["account_number"] == "1001"
    assert "balance" in j

def test_deposit_increases_balance():
    # Start from 500.00 → deposit 50 → 550.00
    r = client.post("/accounts/1001/deposit", json={"amount": "50.00"})
    assert r.status_code == 200
    assert r.json()["balance"] == "550.00"

def test_withdraw_ok():
    # Start from 1250.75 → withdraw 50.75 → 1200.00
    r = client.post("/accounts/1002/withdraw", json={"amount": "50.75"})
    assert r.status_code == 200
    assert r.json()["balance"] == "1200.00"

def test_withdraw_overdraft():
    r = client.post("/accounts/9999/withdraw", json={"amount": "1.00"})
    assert r.status_code == 400
    assert "error" in r.json()

def test_invalid_account():
    r = client.get("/accounts/nope/balance")
    assert r.status_code == 404
    assert "error" in r.json()

def test_zero_and_negative_amounts_rejected():
    r = client.post("/accounts/1001/deposit", json={"amount": "0"})
    assert r.status_code == 422
    r = client.post("/accounts/1001/deposit", json={"amount": "-1"})
    assert r.status_code in (400, 422)

def test_idempotency_key_prevents_duplicate_deposit():
    # Reset known amount by withdrawing earlier deposit to avoid dependence on order
    # Use a unique account 9999 which starts at 0.00
    # First attempt should fail (insufficient funds), so test on deposit instead:
    key = "idem-123"
    r1 = client.post("/accounts/1001/deposit", headers={"Idempotency-Key": key}, json={"amount": "1.00"})
    assert r1.status_code == 200
    bal1 = r1.json()["balance"]
    # Second call with same key should return identical balance (no double deposit)
    r2 = client.post("/accounts/1001/deposit", headers={"Idempotency-Key": key}, json={"amount": "1.00"})
    assert r2.status_code == 200
    assert r2.json()["balance"] == bal1

def test_transactions_log_populates():
    # Make a deposit and withdraw, then read log
    client.post("/accounts/1001/deposit", json={"amount": "2.00"})
    client.post("/accounts/1001/withdraw", json={"amount": "1.00"})
    r = client.get("/accounts/1001/transactions")
    assert r.status_code == 200
    data = r.json()
    assert data["account_number"] == "1001"
    assert isinstance(data["transactions"], list)
    assert len(data["transactions"]) >= 2
    assert set(data["transactions"][-1].keys()) == {"ts", "type", "amount", "balance"}
