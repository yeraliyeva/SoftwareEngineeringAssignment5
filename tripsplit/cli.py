"""Command line interface: python -m tripsplit <command>."""
import argparse

from . import ledger as L
from .splits import SPLITS


def parse_weights(text):
    # "Aru=50,Dana=30,Timur=20"
    if not text:
        return None
    out = {}
    for pair in text.split(","):
        name, value = pair.split("=")
        out[name.strip()] = float(value)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tripsplit", description="Split shared trip expenses.")
    parser.add_argument("--file", default=L.DEFAULT_FILE)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("person")
    p.add_argument("name")

    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("amount", type=float)
    a.add_argument("payer")
    a.add_argument("--split", default="equal", choices=list(SPLITS))
    a.add_argument("--weights")

    sub.add_parser("list")
    sub.add_parser("balance")
    sub.add_parser("settle")

    args = parser.parse_args(argv)
    data = L.load(args.file)

    if args.cmd == "person":
        L.add_person(data, args.name)
        L.save(data, args.file)
        print(f"Added {args.name}")
    elif args.cmd == "add":
        L.add_expense(data, args.title, args.amount, args.payer, args.split, parse_weights(args.weights))
        L.save(data, args.file)
        print(f"Added {args.title} ({args.amount:.2f})")
    elif args.cmd == "list":
        for e in data["expenses"]:
            print(L.describe(data, e))
    elif args.cmd == "balance":
        for person, b in L.balances(data).items():
            print(f"{person:10} {b:+.2f}")
    elif args.cmd == "settle":
        for frm, to, amount in L.settle(data):
            print(f"{frm} -> {to}: {amount:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
