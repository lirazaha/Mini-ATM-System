# Mini ATM System
Live Demo: https://mini-atm-system.onrender.com/docs
A FastAPI-based REST API that simulates ATM banking operations with in-memory storage, transaction history, and production-ready features.

## Overview
This project implements a complete ATM system backend with three core banking operations: balance inquiry, deposit, and withdrawal. The system uses in-memory storage with thread-safe operations and includes advanced features like idempotency, transaction logging, and comprehensive error handling.

## Features

### Core Banking Operations
Balance Inquiry – Get current account balance
Deposit – Add money with validation
Withdrawal – Remove money with overdraft protection
Transaction History – Audit trail of all operations

### Advanced Features
Decimal Precision – Accurate monetary calculations with Decimal
Thread Safety – Per-account locks prevent race conditions
Idempotency – Idempotency-Key header prevents duplicate operations
Structured Logging – Contextual logs for debugging and monitoring
Error Handling – Consistent JSON error schema
Health Monitoring – /healthz endpoint for status checks

## Technology Stack
FastAPI – Modern Python web framework
Pydantic – Data validation and serialization
Uvicorn – ASGI server
pytest – Testing framework
GitHub Actions – CI pipeline

## Quick Start
### Installation
```git clone https://github.com/lirazaha/Mini-ATM-System
cd Mini-ATM-System
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt```

### Run Locally
```uvicorn app.main:app --reload```
The API will be available at:
- **API Docs**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/healthz

## API Endpoints
### Health Check
```GET /healthz```
Returns server status and version information.

### Get Balance
```GET /accounts/{account_number}/balance```
Retrieves the current balance for the specified account.

### Deposit Money
```POST /accounts/{account_number}/deposit```
Retrieves the deposit money for the specified account.

### Withdraw Money
```POST /accounts/{account_number}/withdraw```
Retrieves the withdraw money for the specified account.

### Transaction History
```GET /accounts/{account_number}/transactions```
Returns all transactions for the specified account.

## Idempotency Support
Prevent duplicate operations by including an `Idempotency-Key`:

```bash
curl -X POST http://localhost:8000/accounts/1001/deposit \
     -H "Content-Type: application/json" \
     -H "Idempotency-Key: unique-key-123" \
     -d '{"amount": "10.00"}'
```
The system caches responses for 10 minutes. Repeated requests with the same key return the cached result.

## Test Accounts
The system comes pre-loaded with test accounts:
Account Numbers - 1001, 1002, 9999
Initial Balance - $500.00, $1250.75, $0.0, respectively

## Error Handling
All errors return a consistent Json format:
```{ "error": "Error description" }```
HTTP Status Codes:
- `200` - Success
- `400` - Bad request (insufficient funds, invalid amount)
- `404` - Account not found
- `422` - Validation error

## Testing
Run tests with pytest:
```pytest -v```
Coverage includes:
Health check
Balance retrieval
Deposits & withdrawals
Overdraft prevention
Invalid accounts
Validation of positive amounts
Idempotency
Transaction history

## Deployment

### Render
The project includes `render.yaml` for easy deployment:
1. Connect the repository to Render
2. Create a new Web Service
3. Render will automatically use the configuration

## Implementation Details
Money Handling – Decimal with rounding to 2dp (ROUND_HALF_UP)
Concurrency – Per-account locks ensure thread safety
Audit Trail – Every operation logged in-memory
Idempotency – Prevents duplicate POSTs
Logging – Structured logs with contextual info
Storage – In-memory only (resets on restart)

## Challenges
Precision in money handling – Solved with Decimal
Concurrent updates – Solved with per-account locks
Retry safety – Solved with Idempotency-Key header
Error consistency – Solved with custom exception handlers
Traceability – Solved with transaction log endpoint

## Development
### Code Quality
- Type hints throughout the codebase
- Pydantic models for data validation
- Consistent error handling patterns
- Comprehensive test coverage

### CI/CD
- GitHub Actions workflow runs tests on every push
- Automated testing ensures code quality
- Ready for integration with deployment pipelines
