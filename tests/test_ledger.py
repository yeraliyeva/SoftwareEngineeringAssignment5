import unittest

from tripsplit import ledger as L


def sample():
    data = {"people": [], "expenses": []}
    for name in ["Aru", "Dana", "Timur"]:
        L.add_person(data, name)
    return data


class LedgerTest(unittest.TestCase):
    def test_add_person_ignores_duplicates(self):
        data = sample()
        L.add_person(data, "Aru")
        self.assertEqual(data["people"], ["Aru", "Dana", "Timur"])

    def test_equal_split(self):
        data = sample()
        L.add_expense(data, "Taxi", 90, "Aru")
        self.assertEqual(L.balances(data), {"Aru": 60, "Dana": -30, "Timur": -30})

    def test_percent_split(self):
        data = sample()
        L.add_expense(data, "Hotel", 200, "Dana", "percent", {"Aru": 50, "Dana": 25, "Timur": 25})
        self.assertEqual(L.balances(data), {"Aru": -100, "Dana": 150, "Timur": -50})

    def test_shares_split(self):
        data = sample()
        L.add_expense(data, "Food", 120, "Timur", "shares", {"Aru": 1, "Dana": 1, "Timur": 2})
        self.assertEqual(L.balances(data), {"Aru": -30, "Dana": -30, "Timur": 60})

    def test_settle_clears_debts(self):
        data = sample()
        L.add_expense(data, "Taxi", 90, "Aru")
        self.assertEqual(L.settle(data), [("Dana", "Aru", 30), ("Timur", "Aru", 30)])


if __name__ == "__main__":
    unittest.main()
