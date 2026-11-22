"""Split strategies: how one expense amount is divided between people.

Each strategy takes (amount, expense, people) and returns {person: part}.
Adding a split type = one function + one SPLITS entry; ledger and CLI pick it up.
"""


def equal(amount, expense, people):
    each = amount / len(people)
    return {p: each for p in people}


def percent(amount, expense, people):
    return {p: amount * pct / 100 for p, pct in expense["weights"].items()}


def shares(amount, expense, people):
    total = sum(expense["weights"].values())
    return {p: amount * s / total for p, s in expense["weights"].items()}


SPLITS = {"equal": equal, "percent": percent, "shares": shares}


def split_expense(expense, people):
    """{person: part} for one expense. Unknown split types are an error, never silently ignored."""
    strategy = SPLITS.get(expense["split"])
    if strategy is None:
        raise ValueError(f"unknown split type {expense['split']!r} (use one of: {', '.join(SPLITS)})")
    return strategy(expense["amount"], expense, people)
