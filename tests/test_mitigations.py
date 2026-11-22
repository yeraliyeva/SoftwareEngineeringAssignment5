"""Regression tests for the two Assignment 5 mitigations (M1: R1, M2: R2/R3)."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from tripsplit import ledger as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def trio():
    data = {"people": [], "expenses": []}
    for name in ["Aru", "Dana", "Timur"]:
        L.add_person(data, name)
    return data


class M1LateJoinerTest(unittest.TestCase):
    """R1: an equal split is shared by the people present when the expense was added."""

    def test_person_added_later_does_not_pay_for_earlier_equal_expense(self):
        data = trio()
        L.add_expense(data, "Taxi", 90, "Aru")
        L.add_person(data, "Erlan")
        self.assertEqual(L.balances(data), {"Aru": 60, "Dana": -30, "Timur": -30, "Erlan": 0})

    def test_late_joiner_shares_expenses_added_after_joining(self):
        data = trio()
        L.add_person(data, "Erlan")
        L.add_expense(data, "Dinner", 80, "Erlan")
        self.assertEqual(L.balances(data), {"Aru": -20, "Dana": -20, "Timur": -20, "Erlan": 60})

    def test_old_records_without_participants_still_load(self):
        data = trio()
        data["expenses"].append({"title": "Old", "amount": 90, "payer": "Aru", "split": "equal"})
        self.assertEqual(L.balances(data), {"Aru": 60, "Dana": -30, "Timur": -30})


class M2ValidationTest(unittest.TestCase):
    """R2/R3: invalid input is rejected before it reaches the ledger or the file."""

    def assertRejected(self, *args, match):
        data = trio()
        with self.assertRaisesRegex(ValueError, match):
            L.add_expense(data, "X", *args)
        self.assertEqual(data["expenses"], [], "nothing may be stored")

    def test_amount_must_be_a_positive_finite_number(self):
        for bad in [0, -50, float("nan"), float("inf")]:
            with self.subTest(amount=bad):
                self.assertRejected(bad, "Aru", match="amount must be a positive number")

    def test_payer_must_be_a_known_person(self):
        self.assertRejected(40, "Ary", match="unknown payer 'Ary'")

    def test_weights_must_name_known_people(self):
        self.assertRejected(60, "Aru", "shares", {"aru": 1, "Dana": 1}, match="unknown people in weights: aru")

    def test_percent_weights_must_add_up_to_100(self):
        self.assertRejected(200, "Dana", "percent", {"Aru": 50, "Dana": 25}, match="add up to 100, got 75")

    def test_shares_must_be_positive(self):
        self.assertRejected(60, "Aru", "shares", {"Aru": 0, "Dana": 0}, match="shares must add up to more than 0")
        self.assertRejected(60, "Aru", "shares", {"Aru": 2, "Dana": -1}, match="must not be negative")

    def test_weighted_split_needs_weights(self):
        self.assertRejected(60, "Aru", "percent", None, match="needs --weights")

    def test_valid_expenses_are_still_accepted(self):
        data = trio()
        L.add_expense(data, "Hotel", 200, "Dana", "percent", {"Aru": 50, "Dana": 25, "Timur": 25})
        L.add_expense(data, "Food", 120, "Timur", "shares", {"Aru": 1, "Dana": 1, "Timur": 2})
        self.assertEqual(len(data["expenses"]), 2)


class M2CliTest(unittest.TestCase):
    """The R3 scenario end to end: a typo must not poison the saved ledger."""

    def setUp(self):
        self.file = os.path.join(tempfile.mkdtemp(), "trip.json")
        for name in ["Aru", "Dana"]:
            self.run_cli("person", name)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "tripsplit", "--file", self.file, *args],
                              check=False, capture_output=True, text=True, cwd=ROOT)

    def test_typo_in_payer_is_rejected_and_file_unchanged(self):
        before = pathlib.Path(self.file).read_text()
        r = self.run_cli("add", "Taxi", "40", "Ary")
        self.assertEqual((r.returncode, r.stderr.strip()), (2, "error: unknown payer 'Ary' (known: Aru, Dana)"))
        self.assertEqual(pathlib.Path(self.file).read_text(), before)
        self.assertEqual(self.run_cli("balance").returncode, 0)

    def test_malformed_weights_give_a_message_not_a_traceback(self):
        for bad in ["Aru=50,Dana", "Aru=abc", "Aru=50,Aru=50"]:
            with self.subTest(weights=bad):
                r = self.run_cli("add", "Hotel", "100", "Aru", "--split", "percent", "--weights", bad)
                self.assertEqual(r.returncode, 2)
                self.assertTrue(r.stderr.startswith("error: "), r.stderr)
                self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(pathlib.Path(self.file).read_text())["expenses"], [])


if __name__ == "__main__":
    unittest.main()
