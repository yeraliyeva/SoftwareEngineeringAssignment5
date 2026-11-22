"""Acceptance criteria AC2-AC5 (see AGENTS.md). Change only with human approval."""
import os
import subprocess
import sys
import unittest

from tripsplit import ledger as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "data", "trip.json")
TOL = 0.011  # one cent, plus float noise


def cli(*args):
    """Read-only CLI run against the tracked sample file."""
    out = subprocess.run([sys.executable, "-m", "tripsplit", "--file", SAMPLE, *args],
                         capture_output=True, text=True, cwd=ROOT, check=True)
    return out.stdout


def ledgers():
    """Baseline examples + the sample file."""
    examples = []
    for split, weights, amount in [("equal", None, 100), ("percent", {"Aru": 40, "Dana": 30, "Timur": 30}, 240),
                                   ("shares", {"Aru": 1, "Dana": 2, "Timur": 3}, 75.5)]:
        d = {"people": [], "expenses": []}
        for p in ["Aru", "Dana", "Timur"]:
            L.add_person(d, p)
        L.add_expense(d, "x", amount, "Aru", split, weights)
        examples.append(d)
    return examples + [L.load(SAMPLE)]


class AcceptanceTest(unittest.TestCase):
    def test_ac2_split_amounts_match_baseline_examples(self):
        a, b, c = ledgers()[:3]
        self.assertEqual({k: round(v, 2) for k, v in L.balances(a).items()}, {"Aru": 66.67, "Dana": -33.33, "Timur": -33.33})
        self.assertEqual(L.balances(b), {"Aru": 144.0, "Dana": -72.0, "Timur": -72.0})
        self.assertEqual({k: round(v, 2) for k, v in L.balances(c).items()}, {"Aru": 62.92, "Dana": -25.17, "Timur": -37.75})

    def test_ac3_balances_sum_to_zero(self):
        for d in ledgers():
            self.assertAlmostEqual(sum(L.balances(d).values()), 0, delta=TOL)

    def test_ac4_settle_transfers_clear_all_balances(self):
        for d in ledgers():
            bal = L.balances(d)
            for frm, to, amount in L.settle(d):
                bal[frm] += amount
                bal[to] -= amount
            for person, rest in bal.items():
                self.assertAlmostEqual(rest, 0, delta=TOL, msg=person)

    def test_ac5_cli_output_for_sample_unchanged(self):
        self.assertEqual(cli("list"),
                         "Train tickets: 100.00 paid by Aru -> Aru 33.33, Dana 33.33, Timur 33.33\n"
                         "Guesthouse: 240.00 paid by Dana -> Aru 96.00, Dana 72.00, Timur 72.00\n"
                         "Dinner: 75.50 paid by Timur -> Aru 25.17, Dana 25.17, Timur 25.17\n")
        self.assertEqual(cli("balance"), "Aru        -54.50\nDana       +109.50\nTimur      -55.00\n")
        self.assertEqual(cli("settle"), "Timur -> Dana: 55.00\nAru -> Dana: 54.50\n")


if __name__ == "__main__":
    unittest.main()
