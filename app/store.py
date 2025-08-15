from decimal import Decimal, ROUND_HALF_UP
from threading import Lock
from typing import Dict, List
from collections import defaultdict
from datetime import datetime, timezone

from .models import Account, Txn

_TWO_DP = Decimal("0.01")

def _money(v: Decimal) -> Decimal:
    """Normalize money to 2 decimal places (ROUND_HALF_UP)."""
    return v.quantize(_TWO_DP, rounding=ROUND_HALF_UP)

class Store:
    """In-memory data store with per-account locks and an audit log."""
    def __init__(self) -> None:
        self._accounts: Dict[str, Account] = {}
        # per-account locks
        self._locks: Dict[str, Lock] = {}
        # audit log per account
        self._log: Dict[str, List[Txn]] = defaultdict(list)

    # ----- admin/seed -----
    def seed(self) -> None:
        for num, bal in [("1001", "500.00"), ("1002", "1250.75"), ("9999", "0.00")]:
            self._accounts[num] = Account(account_number=num, balance=_money(Decimal(bal)))

    # ----- helpers -----
    def _require(self, account_number: str) -> Account:
        try:
            return self._accounts[account_number]
        except KeyError:
            raise KeyError("account not found")

    def _get_lock(self, account_number: str) -> Lock:
        # create lock lazily
        lock = self._locks.get(account_number)
        if lock is None:
            lock = Lock()
            self._locks[account_number] = lock
        return lock

    # ----- operations -----
    def get_balance(self, account_number: str) -> Decimal:
        acc = self._require(account_number)
        return _money(acc.balance)

    def deposit(self, account_number: str, amount: Decimal) -> Decimal:
        amount = _money(amount)
        lock = self._get_lock(account_number)
        with lock:
            acc = self._require(account_number)
            acc.balance = _money(acc.balance + amount)
            # append audit log
            self._log[account_number].append(Txn(
                ts=datetime.now(tz=timezone.utc),
                type="deposit",
                amount=amount,
                balance=acc.balance
            ))
            return acc.balance

    def withdraw(self, account_number: str, amount: Decimal) -> Decimal:
        amount = _money(amount)
        lock = self._get_lock(account_number)
        with lock:
            acc = self._require(account_number)
            if acc.balance < amount:
                raise ValueError("insufficient funds")
            acc.balance = _money(acc.balance - amount)
            # append audit log
            self._log[account_number].append(Txn(
                ts=datetime.now(tz=timezone.utc),
                type="withdraw",
                amount=amount,
                balance=acc.balance
            ))
            return acc.balance

    def transactions(self, account_number: str) -> list[Txn]:
        self._require(account_number)
        return list(self._log[account_number])
