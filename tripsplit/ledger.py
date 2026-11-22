"""Shared-expense ledger: who paid what, who owes whom."""
import json
import os

DEFAULT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "trip.json")


def load(path=DEFAULT_FILE):
    if not os.path.exists(path):
        return {"people": [], "expenses": []}
    with open(path) as f:
        return json.load(f)


def save(ledger, path=DEFAULT_FILE):
    with open(path, "w") as f:
        json.dump(ledger, f, indent=2)


def add_person(ledger, name):
    if name not in ledger["people"]:
        ledger["people"].append(name)


def add_expense(ledger, title, amount, payer, split="equal", weights=None):
    expense = {"title": title, "amount": amount, "payer": payer, "split": split}
    if weights:
        expense["weights"] = weights
    ledger["expenses"].append(expense)
    return expense


def balances(ledger):
    """Positive balance = the person should receive money."""
    result = {p: 0.0 for p in ledger["people"]}
    for e in ledger["expenses"]:
        people = ledger["people"]
        result[e["payer"]] += e["amount"]
        if e["split"] == "equal":
            for p in people:
                result[p] -= e["amount"] / len(people)
        elif e["split"] == "percent":
            for p, pct in e["weights"].items():
                result[p] -= e["amount"] * pct / 100
        elif e["split"] == "shares":
            total = sum(e["weights"].values())
            for p, s in e["weights"].items():
                result[p] -= e["amount"] * s / total
    return result


def describe(ledger, e):
    """One line per expense for the `list` command."""
    people = ledger["people"]
    if e["split"] == "equal":
        each = e["amount"] / len(people)
        parts = ", ".join(f"{p} {each:.2f}" for p in people)
    elif e["split"] == "percent":
        parts = ", ".join(f"{p} {e['amount'] * pct / 100:.2f}" for p, pct in e["weights"].items())
    elif e["split"] == "shares":
        total = sum(e["weights"].values())
        parts = ", ".join(f"{p} {e['amount'] * s / total:.2f}" for p, s in e["weights"].items())
    else:
        parts = "?"
    return f"{e['title']}: {e['amount']:.2f} paid by {e['payer']} -> {parts}"


def settle(ledger):
    """Greedy settle-up: biggest debtor pays biggest creditor."""
    bal = balances(ledger)
    debtors = sorted([[p, -b] for p, b in bal.items() if b < 0], key=lambda x: -x[1])
    creditors = sorted([[p, b] for p, b in bal.items() if b > 0], key=lambda x: -x[1])
    transfers = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        pay = min(debtors[i][1], creditors[j][1])
        transfers.append((debtors[i][0], creditors[j][0], round(pay, 2)))
        debtors[i][1] -= pay
        creditors[j][1] -= pay
        if debtors[i][1] < 0.01:
            i += 1
        if creditors[j][1] < 0.01:
            j += 1
    return transfers
