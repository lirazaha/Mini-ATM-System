# Mini ATM System (Server-Side)

A tiny ATM API built with FastAPI. Data is stored **in-memory** (resets on restart).

## Features
- Get balance: `GET /accounts/{account_number}/balance`
- Deposit: `POST /accounts/{account_number}/deposit`
- Withdraw: `POST /accounts/{account_number}/withdraw`
- Validation: positive amounts, sufficient funds
- Uses `Decimal` for money, rounded to 2dp
- Seed accounts: `1001=500.00`, `1002=1250.75`, `9999=0.00`

## Quickstart (local)
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# browse http://127.0.0.1:8000/docs
```

## API Examples (curl)
```bash
curl http://localhost:8000/accounts/1001/balance

curl -X POST http://localhost:8000/accounts/1001/deposit       -H "Content-Type: application/json" -d '{"amount":"25.00"}'

curl -X POST http://localhost:8000/accounts/1001/withdraw       -H "Content-Type: application/json" -d '{"amount":"10.00"}'
```

### Responses
- 200: `{ "account_number": "1001", "balance": "515.00" }`
- 400: `{ "detail": "insufficient funds" }` or `{ "detail": "amount must be > 0" }`
- 404: `{ "detail": "account not found" }`

## Tests
```bash
pytest -q
```

## Deployment

### Option A: Render (no Docker)
1. Push this repo to GitHub.
2. Create a new **Web Service** on Render, connect the repo.
3. **Build Command:** `pip install -r requirements.txt`
   **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Deploy. Copy the public URL for submission.

### Option B: Heroku (with Dockerfile or Procfile)
**Using Procfile (no Docker):**
1. Install the Heroku CLI and login.
2. `heroku create`
3. `heroku buildpacks:add heroku/python`
4. `git push heroku main` (or `master`)
5. `heroku ps:scale web=1`
6. `heroku open`

**Using Dockerfile:**
```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Build & run locally:
```bash
docker build -t mini-atm .
docker run -p 8000:8000 mini-atm
```

## Notes & Design Decisions
- In-memory store with a single process-wide lock is sufficient for this task.
- `Decimal` avoids float rounding issues.
- Pydantic validation ensures positive amounts.
- Seeded accounts simplify evaluation.


## Extras added
- **/healthz** endpoint
- **Consistent error schema**: `{ "error": "..." }` for 4xx/5xx
- **Per-account locks** (better concurrency)
- **Idempotency** for POSTs via `Idempotency-Key` header (TTL 10 minutes)
- **Audit trail**: `GET /accounts/{account_number}/transactions`
- **Pre-commit**: Black + Ruff
- **CI**: GitHub Actions runs tests on every push

### Transactions endpoint
```bash
curl http://localhost:8000/accounts/1001/transactions
# {"account_number":"1001","transactions":[{"ts":"2025-08-15T14:00:00Z","type":"deposit","amount":"50.00","balance":"550.00"}, ...]}
```

### Idempotency header example
```bash
curl -X POST http://localhost:8000/accounts/1001/deposit       -H "Content-Type: application/json"       -H "Idempotency-Key: my-unique-key-123"       -d '{"amount":"10.00"}'
```
