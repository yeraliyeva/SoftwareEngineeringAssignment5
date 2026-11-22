"""Split strategies: how one expense amount is divided between people.

Each strategy takes (amount, expense, people) and returns {person: part}.
Adding a split type = one function + one SPLITS entry; ledger and CLI pick it up.
A strategy raises ValueError when the expense's weights do not make sense for it.
"""
import math


def _weights(expense):
    weights = expense.get("weights")
    if not weights:
        raise ValueError(f'a {expense["split"]} split needs --weights, e.g. "Aru=50,Dana=50"')
    if any(not math.isfinite(w) or w < 0 for w in weights.values()):
        raise ValueError("weights must be finite numbers and must not be negative")
    return weights


def equal(amount, expense, people):
    # Records saved before A5 have no "participants": fall back to everyone (old behaviour).
    people = expense.get("participants", people)
    each = amount / len(people)
    return {p: each for p in people}


def percent(amount, expense, people):
    weights = _weights(expense)
    total = sum(weights.values())
    if abs(total - 100) > 0.01:
        raise ValueError(f"percent weights must add up to 100, got {total:g}")
    return {p: amount * pct / 100 for p, pct in weights.items()}


def shares(amount, expense, people):
    weights = _weights(expense)
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("shares must add up to more than 0")
    return {p: amount * s / total for p, s in weights.items()}


SPLITS = {"equal": equal, "percent": percent, "shares": shares}


def split_expense(expense, people):
    """{person: part} for one expense. Unknown split types are an error, never silently ignored."""
    strategy = SPLITS.get(expense["split"])
    if strategy is None:
        raise ValueError(f"unknown split type {expense['split']!r} (use one of: {', '.join(SPLITS)})")
    return strategy(expense["amount"], expense, people)
