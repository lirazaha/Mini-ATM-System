import logging, sys
from time import time
from typing import Dict, Tuple
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .models import MoneyChange, Error
from .store import Store

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("atm")

app = FastAPI(title="Mini ATM System", version="1.1.0")

# In-memory store
store = Store()
store.seed()

# Idempotency cache: key -> (timestamp, response_dict)
IDEMP_TTL = 10 * 60  # seconds
idemp_cache: Dict[str, Tuple[float, dict]] = {}

def idempotent_response(key: str | None, compute):
    now = time()
    # simple sweep to purge expired
    for k, (t, _) in list(idemp_cache.items()):
        if now - t > IDEMP_TTL:
            idemp_cache.pop(k, None)
    if not key:
        return compute()
    if key in idemp_cache:
        log.info("idempotency hit", extra={"idempotency_key": key})
        return idemp_cache[key][1]
    result = compute()
    idemp_cache[key] = (now, result)
    return result

# --- Exception mappers for consistent error schema ---
@app.exception_handler(HTTPException)
async def http_exc_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=Error(error=str(exc.detail)).model_dump())

@app.exception_handler(RequestValidationError)
async def validation_exc_handler(_: Request, exc: RequestValidationError):
    # Collapse Pydantic's verbose detail into a short message
    msg = "validation error"
    try:
        # Try to surface the first message if present
        if exc.errors():
            msg = exc.errors()[0].get("msg", msg)
    except Exception:
        pass
    return JSONResponse(status_code=422, content=Error(error=msg).model_dump())

@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(status_code=400, content=Error(error=str(exc)).model_dump())

# --- Endpoints ---
@app.get("/healthz")
def health():
    return {"status": "ok", "version": app.version}

@app.get("/accounts/{account_number}/balance")
def get_balance(account_number: str):
    log.info("get_balance", extra={"account": account_number})
    try:
        bal: Decimal = store.get_balance(account_number)
        return {"account_number": account_number, "balance": str(bal)}
    except KeyError:
        raise HTTPException(status_code=404, detail="account not found")

@app.post("/accounts/{account_number}/deposit")
def deposit(account_number: str, body: MoneyChange, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    log.info("deposit", extra={"account": account_number, "amount": str(body.amount), "idempotency_key": idempotency_key})
    def _do():
        bal: Decimal = store.deposit(account_number, body.amount)
        return {"account_number": account_number, "balance": str(bal)}
    try:
        return idempotent_response(idempotency_key, _do)
    except KeyError:
        raise HTTPException(status_code=404, detail="account not found")

@app.post("/accounts/{account_number}/withdraw")
def withdraw(account_number: str, body: MoneyChange, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    log.info("withdraw", extra={"account": account_number, "amount": str(body.amount), "idempotency_key": idempotency_key})
    def _do():
        bal: Decimal = store.withdraw(account_number, body.amount)
        return {"account_number": account_number, "balance": str(bal)}
    try:
        return idempotent_response(idempotency_key, _do)
    except KeyError:
        raise HTTPException(status_code=404, detail="account not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/accounts/{account_number}/transactions")
def txns(account_number: str):
    log.info("transactions", extra={"account": account_number})
    try:
        txlist = store.transactions(account_number)
        # serialize for JSON (convert Decimals and datetimes to strings)
        def _ser(tx):
            return {
                "ts": tx.ts.isoformat().replace("+00:00", "Z"),
                "type": tx.type,
                "amount": str(tx.amount),
                "balance": str(tx.balance),
            }
        return {"account_number": account_number, "transactions": [_ser(t) for t in txlist]}
    except KeyError:
        raise HTTPException(status_code=404, detail="account not found")
