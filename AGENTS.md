# AGENTS.md — TripSplit

Operating rules for any AI coding assistant (and for people) working in this repository.
`CLAUDE.md` points here for Claude Code. If your tool does not load `AGENTS.md` by itself, paste the
sections you rely on into the prompt and write in the task notes that you did so.

## 1. What this project is

A command-line tool that records shared trip expenses for a small group of friends, computes
each person's balance and suggests who should pay whom. Pure Python standard library.
The only data file is `data/trip.json`, which holds fictional sample names and amounts.

## 2. Layout

| Path | Role |
|------|------|
| `tripsplit/__main__.py` | entry point for `python3 -m tripsplit` |
| `tripsplit/cli.py` | argparse commands `person`, `add`, `list`, `balance`, `settle`. Input parsing only |
| `tripsplit/ledger.py` | load/save JSON, add people/expenses, balances, settle-up |
| `tripsplit/splits.py` | split strategies `equal`, `percent`, `shares` (`SPLITS`). The single place that knows how an amount is divided |
| `tests/` | `unittest` suites. `test_acceptance.py` holds the acceptance criteria |
| `data/trip.json` | tracked sample ledger. Tests must never write to it |
| `docs/` | Assignment 5 report and saved command output |

Rule of thumb: the CLI parses and prints, `ledger.py` stores and sums, `splits.py` divides.
New split type = one function + one `SPLITS` entry, plus tests. Nothing else should change.

## 3. Setup

Python 3.9+. No third-party runtime or test dependencies, so there is nothing to `pip install`.
Optional linter: `ruff` (if installed globally).

## 4. Commands an agent may run freely

```bash
python3 -m unittest -v                          # all tests, must pass
ruff check .                                     # lint, must report no errors
python3 -m compileall -q tripsplit tests         # syntax check ("build")
python3 -m tripsplit --file /tmp/x.json balance  # manual runs ALWAYS use a temp --file
git status / git diff / git log                  # read-only git
```

## 5. Conventions

- Python 3.9 syntax (no `match`, no `X | Y` type unions at runtime).
- Money is entered with at most 2 decimals and displayed with 2 decimals. Balances are compared with a 0.01 tolerance.
- User input must be validated in `ledger.add_expense` (the trust boundary). This is currently missing (risks R2/R3 in `docs/ASSIGNMENT5.md`).
- Functions return new data or mutate only the ledger dict they are given. No globals.
- Small commits, one concern each, message in imperative mood.

## 6. Tests

- Every bug fix or behaviour change adds a failing test first, then the fix.
- Tests use temporary files (`tempfile`) and never touch `data/trip.json`.
- Report real numbers from `python3 -m unittest`. Do not invent or round up results.
- The acceptance tests in `tests/test_acceptance.py` may only change with human approval.

## 7. Acceptance criteria

| ID | Must stay true |
|----|---------------|
| AC1 | `python3 -m unittest` passes all tests |
| AC2 | `equal`, `percent` and `shares` give the same per-person amounts as the baseline examples |
| AC3 | For any valid ledger, all balances add up to 0 (±0.01) |
| AC4 | Applying the `settle` transfers brings every balance to 0 (±0.01) |
| AC5 | `list`, `balance` and `settle` print the same text for `data/trip.json` as at the baseline |

## 8. Forbidden without explicit human approval

- Adding, upgrading or removing dependencies (`requirements*.txt`, `pip install`, new imports outside the stdlib).
- Editing or deleting `data/trip.json`, `tests/test_acceptance.py` or anything under `docs/evidence/`.
- Any `git push`, publishing to PyPI, creating releases or deploying anywhere.

## 9. Never

- Put real names, phone numbers, card numbers, API keys, tokens or `.env` files in the repo.
- Run destructive commands: `rm -rf`, `git reset --hard`, `git clean -fdx`, `git push --force`, history rewrites.
- Use `eval`, `exec`, `pickle` or shell calls on user input.
- Mark a task done when tests were not run. Say "not run" instead.

## 10. Review gate

Work happens on a branch. A human reads the full diff, runs `python3 -m unittest -v` and `ruff check .`
locally, and only then merges. AI-reported risks count as unverified until a person reproduces them.
