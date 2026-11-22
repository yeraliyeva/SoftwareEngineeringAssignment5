"""Task 3: split strategies live in one place (tripsplit/splits.py)."""
import contextlib
import io
import unittest

from tripsplit import cli
from tripsplit import ledger as L
from tripsplit.splits import SPLITS


class SplitStrategyTest(unittest.TestCase):
    def test_unknown_split_type_is_an_error_everywhere(self):
        data = {"people": ["Aru", "Dana"], "expenses": [{"title": "X", "amount": 90, "payer": "Aru", "split": "Equal"}]}
        with self.assertRaisesRegex(ValueError, "unknown split type 'Equal'"):
            L.balances(data)
        with self.assertRaisesRegex(ValueError, "unknown split type 'Equal'"):
            L.describe(data, data["expenses"][0])

    def test_new_strategy_is_picked_up_by_ledger_and_cli_without_other_edits(self):
        SPLITS["payer_only"] = lambda amount, expense, people: {expense["payer"]: amount}
        try:
            data = {"people": ["Aru", "Dana"], "expenses": []}
            L.add_expense(data, "Gift", 50, "Aru", "payer_only")
            self.assertEqual(L.balances(data), {"Aru": 0, "Dana": 0})
            self.assertIn("Aru 50.00", L.describe(data, data["expenses"][0]))
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):  # argparse exits 2
                cli.main(["--file", "/nonexistent/x.json", "add", "X", "1", "Aru", "--split", "nope"])
        finally:
            del SPLITS["payer_only"]


if __name__ == "__main__":
    unittest.main()
