"""Regression tests for the two Assignment 5 mitigations (M1: R1, M2: R2/R3)."""
import unittest

from tripsplit import ledger as L


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


if __name__ == "__main__":
    unittest.main()
