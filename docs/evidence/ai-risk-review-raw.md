# Raw AI output: read-only risk review (Task 4)

- **Tool / model:** Claude Code (Anthropic), model Claude Opus 5.5, read-only "Explore" sub-agent (no Edit/Write tools)
- **Date:** 2026-11-22
- **Reviewed version:** `a5-baseline` (commit `c902570`)
- **Prompt (verbatim summary):** "You are doing a READ-ONLY risk review of a small Python 3.9 repository … Do NOT create, modify or delete any files (including data/trip.json — do not run CLI commands that save …). You may read files and run read-only commands (cat, grep, `python3 -I -c` one-liners on in-memory data, `python3 -m unittest`, `ruff check .`). Propose 8–10 candidate risks spanning: correctness, maintainability, security, dependency, agent operations. For each give: ID, category, title, cause → event → consequence, affected files/lines, evidence, confidence (confirmed / plausible / speculative), likelihood 1–3, impact 1–3. Do not overstate; if you are guessing, say so."
- **Status:** The text below is unedited AI output. Its claims are **not** accepted until verified. Verification is in `verify-ai-findings-baseline.txt` and in the risk register in `docs/ASSIGNMENT5.md`.

---

## TripSplit — read-only risk review

Scope: `tripsplit/ledger.py`, `tripsplit/cli.py`, `tripsplit/__main__.py`, 5 unit tests. One commit (`c902570`, tag `a5-baseline`). Ran: `python3 -m unittest` (5 OK, Py 3.9.6), `ruff check .` (1 error), read-only CLI (`balance`/`settle`/`list`), and in-memory `python3 -I -c` reproductions. `data/trip.json` was not modified.

### R1 — Correctness: equal split is recomputed against the *current* roster, so adding a person rewrites past expenses
- Cause → event → consequence: `balances()` splits "equal" expenses over `ledger["people"]` at calculation time, not the participants at the time of the expense → someone joins mid-trip → every earlier equal expense is silently re-split including the newcomer, who is charged for things they did not share, and earlier debts shrink.
- Where: `tripsplit/ledger.py:37-41`. `add_expense` (25-30) does not store participants.
- Evidence: Taxi 90 paid by Aru with 3 people, then `add_person('Erlan')`: `before {'Aru': 60.0, 'Dana': -30.0, 'Timur': -30.0}` → `after add person {'Aru': 67.5, 'Dana': -22.5, 'Timur': -22.5, 'Erlan': -22.5}`
- Confidence: confirmed. Likelihood 3, impact 3.

### R2 — Correctness: no validation of weights/amounts, so balances no longer sum to zero
- Cause → event → consequence: no check that percent weights sum to 100, that share totals are > 0, or that amounts are positive → user enters percents summing to 75 or omits a person → balances don't net to zero and `settle` produces wrong transfers silently.
- Where: `tripsplit/ledger.py:25-30`, `42-48`. `tripsplit/cli.py:29` (`type=float` accepts negatives).
- Evidence: percent `{'Aru':50,'Dana':25}` on 200 → `{'Aru': -100.0, 'Dana': 150.0, 'Timur': 0.0} sum 50.0`, settle `[('Aru', 'Dana', 100.0)]` (Dana is owed 150 but told to collect 100). Shares `{'Aru':0,'Dana':0}` → `ZeroDivisionError`. Amount `-50` accepted.
- Confidence: confirmed. Likelihood 2, impact 3.

### R3 — Correctness: a typo'd name is saved, then `balance`/`settle` crash permanently
- Cause → event → consequence: `add` persists an expense without checking that payer/weight names exist → typo `Ary` or `aru` → record saved → every `balance`/`settle` raises `KeyError` until the JSON is hand-edited. `list` still works, which hides the cause.
- Where: `tripsplit/cli.py:45-47`, `tripsplit/ledger.py:38,44,48`.
- Evidence: in-memory payer `'Ary'` → `err KeyError 'Ary'`. Shares `{'aru':1,...}` → `err KeyError 'aru'`. `cli.py:46-47` calls `L.save(...)` right after `add_expense` with no checks.
- Confidence: confirmed for the crash in memory. Persistence is from reading the code (did not run `add` because writing is forbidden). Likelihood 3, impact 2.

### R4 — Correctness/Maintainability: unknown split type handled inconsistently, split maths duplicated
- Cause → event → consequence: `balances()` has no `else` → a hand-edited or future split type (e.g. `"Equal"`) loaded from JSON → payer credited, nobody debited, money created. `describe()` prints `?`. Split maths is duplicated in `balances` and `describe`, so they can drift.
- Where: `tripsplit/ledger.py:39-48` (no else) vs `55-64` (duplicate maths).
- Evidence: `split: 'Equal'` → `{'Aru': 90.0, 'Dana': 0.0, 'Timur': 0.0} sum 90.0`. `describe` → `X: 90.00 paid by Aru -> ?`
- Confidence: confirmed. Likelihood 1, impact 2.

### R5 — Correctness: settle-up rounding leaks/creates cents
- Cause → event → consequence: transfers are individually `round(pay, 2)` while the 0.01 stopping threshold works on unrounded floats, and money is float (not Decimal/cents) → indivisible amounts → transfers don't sum to the creditor's balance.
- Where: `tripsplit/ledger.py:76-83`, float money throughout.
- Evidence: 100 paid by P0 split 3 ways → `[('P1','P0',33.33),('P2','P0',33.33)]` = 66.66 vs owed 66.67. A sweep of 8 amounts × 2–7 people found 25 combos with a cent mismatch.
- Confidence: confirmed (small magnitude). Likelihood 3, impact 1.

### R6 — Correctness/Robustness: non-atomic save, unchecked load and weight parsing
- Cause → event → consequence: `save()` opens the real file with `"w"` (truncates) then writes → crash, Ctrl-C or full disk mid-write → `data/trip.json` empty or truncated → all later commands fail with a `json.load` traceback. `load()` silently returns an empty ledger for a non-existent path (a typo in `--file` shows nothing for reads and creates a new file for writes). `parse_weights` raises raw tracebacks and silently collapses duplicates.
- Where: `tripsplit/ledger.py:8-17`, `tripsplit/cli.py:8-16`.
- Evidence: `'Aru=50,Dana'` → `ValueError not enough values to unpack`. `'Aru=abc'` → `could not convert string to float`. `'Aru=50,Aru=50'` → `{'Aru': 50.0}`. Truncation not reproduced (would require a file write).
- Confidence: parse_weights confirmed. Non-atomic save plausible from the code. Likelihood 2, impact 2.

### R7 — Agent operations: README commands wrong, CLI writes the tracked data file by default
- Cause → event → consequence: README shows `python main.py ...`, but there is no `main.py` (the entry point is `python -m tripsplit`) → an agent or new user following the README gets "No such file", improvises, and the natural fix (`python -m tripsplit person Aru`/`add ...`) mutates the git-tracked `data/trip.json`, because `DEFAULT_FILE` is resolved relative to the package, not the cwd. The only safety net is `git checkout data/trip.json`.
- Where: `README.md:15-19`, `tripsplit/ledger.py:5`, `tripsplit/cli.py:21`.
- Evidence: `can't open file '.../main.py': [Errno 2] No such file or directory`. `cli.py:1` docstring says `python -m tripsplit <command>`. `git ls-files` lists `data/trip.json`.
- Confidence: confirmed. Likelihood 3, impact 2.

### R8 — Dependency/Agent ops: README test command fails, test dependency unpinned and not installed
- Cause → event → consequence: `requirements.txt` contains only `pytest` (no version, no lock, no Python version declared, no `pyproject.toml`). pytest is not installed, the README says `pytest` → `pytest not found` → an agent may `pip install` (environment mutation, pulls latest) or conclude tests can't run, while `python3 -m unittest` already works with no install. The project has no runtime deps, yet listing pytest as a requirement makes `pip install -r requirements.txt` look necessary.
- Where: `requirements.txt:1`, `README.md:7-9,25-27`.
- Evidence: `which pytest` → `pytest not found`. `import pytest` → `ModuleNotFoundError`. `python3 -m unittest` → `Ran 5 tests ... OK`.
- Confidence: confirmed (missing tool). Supply-chain drift from the unpinned version is speculative and low impact for a dev-only tool. Likelihood 2, impact 1.

### R9 — Agent operations/Maintainability: no CI, no agent instructions, lint failing, shallow tests
- Cause → event → consequence: no CI workflow, no `CLAUDE.md`/`AGENTS.md`, no lint or format config. Tests cover only happy-path `ledger.py` with exact float equality, and nothing for `cli.py`, `describe`, `load`/`save` or error cases → agent changes pass green tests (none of R1–R6 would be caught) → regressions slip through.
- Where: repo root, `tests/test_ledger.py`, `tripsplit/cli.py:3`.
- Evidence: `ruff check .` → `F401 json imported but unused --> tripsplit/cli.py:3:8`. Glob of the root found no `.github`, `pyproject`, `CLAUDE` or `AGENTS`. The 5 tests use 3 people and amounts that divide evenly (90/3, 200, 120).
- Confidence: confirmed absence. The regression risk is plausible. Likelihood 2, impact 2.

### R10 — Security: `--file` writes anywhere, JSON trusted without a schema (low)
- Cause → event → consequence: `--file` accepts any path and `save` overwrites it with JSON → wrong path, or a script/agent building the path from untrusted input → an unrelated file is clobbered. `load` does `json.load` with no schema check, so a malformed or hostile ledger causes crashes (R3/R4). There is no code-execution vector (no pickle/eval).
- Where: `tripsplit/cli.py:21`, `tripsplit/ledger.py:8-17`.
- Evidence: code reading only.
- Confidence: speculative. Local single-user CLI, weak threat model. Likelihood 1, impact 2.

---

**Top priorities:** R1, R2/R3 (silently wrong money or a corrupted ledger), then R7 (wrong README commands push agents toward the tracked data file).
