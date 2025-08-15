from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class Account(BaseModel):
    """Simple account model held in memory."""
    account_number: str
    balance: Decimal = Field(default=Decimal("0.00"))

class MoneyChange(BaseModel):
    """Request body for deposit/withdraw endpoints."""
    amount: Decimal = Field(..., description="Positive amount in currency units")

    @field_validator("amount")
    @classmethod
    def positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be > 0")
        return v

class Error(BaseModel):
    error: str

class Txn(BaseModel):
    ts: datetime
    type: str  # "deposit" | "withdraw"
    amount: Decimal
    balance: Decimal
