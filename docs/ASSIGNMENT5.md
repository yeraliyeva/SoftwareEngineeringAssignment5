# Assignment #05: AI-assisted repository customization and risk governance

**Student:** Yeraliyeva Anel
**ID:** 24B031020
**Course:** Software Engineering (KBTU)

**Repository:** TripSplit, a command-line expense splitter for a group trip. It uses Python 3.9 and the standard library only. All names and amounts are fictional, and there are no secrets.

**AI assistant:** Claude Code (Anthropic), model Claude Opus 5.5. Date: 22 November 2026.

| | Commit |
|---|--------|
| Baseline | tag `a5-baseline` → `c902570` |
| Final | `HEAD` of `main` (the commit list is in the appendix) |

All quoted output comes from files in [`docs/evidence/`](evidence/). If a check was not run, the report says so.

---

## Task 01: Baseline and context

### Repository map

```
tripsplit/__main__.py   entry point: python3 -m tripsplit
tripsplit/cli.py        argparse: person, add, list, balance, settle
tripsplit/ledger.py     load/save JSON, add_person, add_expense, balances, describe, settle
tests/test_ledger.py    5 unittest cases (happy path only)
data/trip.json          tracked sample ledger (3 fictional people, 3 expenses)
requirements.txt        "pytest" (no version)
README.md               install + usage + test instructions
```

The project has no runtime dependencies, no build step, no CI and no lint configuration.

### Commands and actual results at baseline

| Command | Exit | Result | Evidence |
|---------|------|--------|----------|
| `python3 -m unittest -v` | 0 | `Ran 5 tests … OK` | `baseline-unittest.txt` |
| `pytest` (README) | 127 | `command not found: pytest` | `baseline-readme-lint-build.txt` |
| `python3 -m pytest` | 1 | `No module named pytest` | same |
| `python3 main.py balance` (README) | 2 | `can't open file '…/main.py'` | same |
| `python3 -m compileall -q tripsplit tests` | 0 | no output (syntax OK) | same |
| `ruff check .` (ruff 0.17.1) | 1 | `F401 json imported but unused --> tripsplit/cli.py:3:8` | `baseline-ruff.txt` |
| `flake8` / `mypy` | n/a | not installed (no type checking available) | same |
| `pip install -r requirements.txt` | not run | it would install an unpinned package that the tests do not use | same |

### Weaknesses found at baseline, with evidence

1. **The README is wrong.** Its commands `python main.py …` and `pytest` fail (see the table above).
2. **There is a dead, unpinned dependency.** `requirements.txt` lists `pytest`, but the tests use `unittest`.
3. **Lint fails.** There is an unused import in `cli.py`.
4. **Input is not validated.** `add_expense` stores whatever it receives (shown in Task 04: R2 and R3).
5. **Split logic is written twice.** `balances()` and `describe()` each have their own `if/elif` chain for the split types (Task 03).

### Facts, assumptions and unverified claims

- **Facts.** Every value in the table above, and every "confirmed" entry in Task 04, comes from command output.
- **Assumptions.** The tool runs on one person's laptop. The ledger file is edited only through the CLI. The users are friends, not attackers.
- **Unverified.** These AI statements were not proven: that an unpinned `pytest` could pull a harmful release (R8), and that `--file` is a security problem (R10).

### Acceptance criteria

These are also listed in `AGENTS.md` §7. They are checked by `tests/test_acceptance.py`, which was added **before** any code change and passes on the baseline code (see `task3-strategy-before-after.txt`).

| ID | Criterion | Baseline | Final |
|----|-----------|----------|-------|
| AC1 | `python3 -m unittest` passes | 5/5 | 23/23 |
| AC2 | `equal` / `percent` / `shares` give the same amounts as the baseline examples | pass | pass |
| AC3 | balances of a valid ledger sum to 0 (±0.01) | pass | pass |
| AC4 | applying the `settle` transfers clears every balance (±0.01) | pass | pass |
| AC5 | `list` / `balance` / `settle` output for `data/trip.json` is unchanged | pass | pass |

---

## Task 02: Agent instructions

I wrote `AGENTS.md` and a short `CLAUDE.md` that loads it with `@AGENTS.md` (commit `1e61dac`). It has 10 numbered sections:

1. **Purpose**
2. **Layout.** A file table plus a one-line rule: *"the CLI parses and prints, `ledger.py` stores and sums, `splits.py` divides"*.
3. **Setup.** Nothing to install.
4. **Commands an agent may run freely.** Tests, ruff, compileall and read-only git. Any manual CLI run must use a temporary `--file`.
5. **Conventions.** Python 3.9 syntax, 2-decimal money, validation at `add_expense`.
6. **Tests.** Write the failing test first. Never write to `data/trip.json`. Report real numbers.
7. **Acceptance criteria.**
8. **Forbidden without human approval.** Dependency changes, editing the sample data, the acceptance tests or the evidence, and any push, release or deploy.
9. **Never.** Real personal data or secrets, destructive git or `rm -rf`, `eval`/`exec`/`pickle` on input, claiming results that were not run.
10. **Review gate.** Work on a branch. A human reads the diff and re-runs tests and lint before merging.

In the same commit I fixed the README so that every command in it works, removed the unused `requirements.txt`, and fixed the lint error.

I updated `AGENTS.md` in later commits so that it always describes the code as it is in that commit. For example, `splits.py` is only mentioned after it exists.

**Disclosure.** Claude Code loads `CLAUDE.md` automatically, but only for the directory where the session starts. My session started in a parent folder, and `AGENTS.md` was written during the session. So for most of the work the rules were in the agent's context because it had written and re-read them, not because they were loaded automatically. The read-only review sub-agent ran before `AGENTS.md` existed. Its prompt contained the rules it needed (no file changes, no `add`/`person` against `data/trip.json`). The prompt is quoted in `evidence/ai-risk-review-raw.md`.

---

## Task 03: Pattern decision: Strategy

**Problem: duplicated conditionals that have already drifted apart.** At the baseline, the knowledge of "which split types exist and how each divides money" was spread over three places:

```
a5-baseline:tripsplit/cli.py:31     choices=["equal", "percent", "shares"]
a5-baseline:tripsplit/ledger.py:39  if e["split"] == "equal":      (balances)
a5-baseline:tripsplit/ledger.py:42  elif e["split"] == "percent":
a5-baseline:tripsplit/ledger.py:45  elif e["split"] == "shares":
a5-baseline:tripsplit/ledger.py:55  if e["split"] == "equal":      (describe)
a5-baseline:tripsplit/ledger.py:58  elif e["split"] == "percent":
a5-baseline:tripsplit/ledger.py:60  elif e["split"] == "shares":
```

The two chains already behaved differently on an unknown type. `balances()` credited the payer and charged nobody, so money appeared from nowhere. `describe()` printed `?` (risk R4).

**Options evaluated**

| Option | Verdict |
|--------|---------|
| Leave it as it is | It works today, but a 4th split type would need three coordinated edits, and the copies have already drifted. Rejected. |
| Strategy using classes (`class EqualSplit: def split(...)`) | Correct, but adds boilerplate. Each strategy is one formula. |
| **Strategy as a registry of functions** (`SPLITS = {"equal": equal, …}`) | Same separation, idiomatic Python, smallest diff. **Chosen.** |
| Adapter | There is no external interface to adapt. Not applicable. |

**Before and after structure (commit `a991a92`)**

| | Before | After |
|---|--------|-------|
| Where the division logic lives | 2 copies in `ledger.py` | `tripsplit/splits.py`, used by `balances()` and `describe()` through `split_expense()` |
| Where the CLI gets its split list | hard-coded list | `choices=list(SPLITS)` |
| Unknown split type | `balances()` creates money; `describe()` prints `?` | `ValueError: unknown split type 'Equal'` everywhere |
| Adding a split type | 3 edits in 2 files | 1 function + 1 `SPLITS` entry (tested by `test_new_strategy_is_picked_up…`) |
| `ledger.py` + `cli.py` | — | +7 / −23 lines (plus the new 32-line `splits.py`) |

**Proof that the acceptance criteria still hold:** `evidence/task3-strategy-before-after.txt`. The acceptance tests give **4/4 OK on the baseline code** and **11/11 OK after the refactor**, with ruff clean. The new `test_splits.py` cannot run on the baseline (`No module named 'tripsplit.splits'`), which is expected.

---

## Task 04: Read-only AI risk review

**Prompt (summary):** a read-only Claude Code sub-agent was told not to create or modify files and not to run `person`/`add` against the sample. It could only read, run in-memory `python3 -I -c` probes, `unittest` and `ruff`. It was asked for 8–10 risks across 5 categories, each with a confidence level and L/I scores.

The raw answer is in `evidence/ai-risk-review-raw.md`. I re-checked every claim with my own script, using in-memory data and temporary files only (`evidence/verify-ai-findings-baseline.txt`).

| ID | AI claim | Category | AI said | **My classification** | What I observed |
|----|----------|----------|---------|------------------------|-----------------|
| R1 | Adding a person re-splits old equal expenses | correctness | confirmed | **Confirmed** | Taxi 90: `{'Aru': 60, 'Dana': -30, 'Timur': -30}` → after `add_person(Erlan)`: `{'Aru': 67.5, 'Dana': -22.5, 'Timur': -22.5, 'Erlan': -22.5}` |
| R2 | Percent/shares/amount are not validated, so balances do not net to 0 | correctness | confirmed | **Confirmed** | percent 50+25: `sum = 50.0`, settle `[('Aru','Dana',100.0)]`; shares all 0 → `ZeroDivisionError`; `-50` and **`nan`** accepted (`{'Aru': nan, …}`) |
| R3 | A name typo is saved, then `balance` crashes | correctness | confirmed (in memory) | **Confirmed end-to-end** (temp file) | `add Taxi 40 Ary` → exit 0, saved payer `Ary`; `balance` → `KeyError: 'Ary'`; `list` still works |
| R4 | Unknown split type handled inconsistently | correctness / maintainability | confirmed | **Confirmed** | `'Equal'` → `sum = 90.0`; describe → `-> ?` |
| R5 | Settle rounding loses or adds a cent | correctness | confirmed | **Confirmed** | 100 split 3 ways: transfers 66.66, owed 66.67 |
| R6 | Save is not atomic; `parse_weights` gives tracebacks | correctness / robustness | parse confirmed; save "plausible" | **Confirmed (both)**. I reproduced the save problem | a save that fails part-way through leaves a truncated file: `load()` → `JSONDecodeError … (char 177)` |
| R7 | README commands are wrong; the default `--file` is the tracked sample | agent operations | confirmed | **Confirmed** | `main.py` missing; `DEFAULT_FILE -> data/trip.json`, which is tracked by git |
| R8 | README test command fails; `pytest` is unpinned and unused | dependency | confirmed + speculative | Missing tool **confirmed**. Supply-chain harm **unsupported** | nothing is ever installed from it, and the tests do not import it |
| R9 | No CI, no agent rules, lint fails, tests are shallow | agent operations | confirmed | **Confirmed** | ruff F401; 5 happy-path tests; no `.github`/`AGENTS.md` |
| R10 | `--file` can overwrite any path | security | speculative | **Unsupported as a security risk** | the path comes from the user's own command line; there is no untrusted source and no privilege boundary |

Result: 10 investigated across 5 categories. 9 confirmed, 1 unsupported, and 1 sub-claim unsupported (R8). For R6 the AI was more cautious than necessary. I turned its "plausible" into "confirmed" by injecting a failure.

---

## Task 05: Risk register

L = likelihood, I = impact, both on a 1–3 scale. Score = L × I. **The owner of every row is Yeraliyeva Anel.**

| ID | Category | Cause → event → consequence | Component | Evidence | L | I | Score | Mitigation | Verification plan | Residual |
|----|----------|-----------------------------|-----------|----------|---|---|-------|-----------|-------------------|----------|
| **R1** | correctness | Equal split uses the *current* roster → a friend joins mid-trip → past bills are re-split and the newcomer pays for them | `ledger.balances`, `add_expense` | T04 R1 | 3 | 3 | **9** | **M1**: store `participants` when the expense is added | `M1LateJoinerTest` fails before the fix and passes after | 2 (L1×I2): records saved **before** A5 still use the old rule |
| **R3** | correctness | No name check at `add` → a typo is saved to disk → every `balance` and `settle` crashes until the JSON is edited by hand | `add_expense`, `cli.py` | T04 R3 | 3 | 2 | **6** | **M2**: validate at `add_expense`; the CLI prints `error:` and exits 2 | `M2CliTest`: file unchanged, `balance` still exit 0 | 2: a hand-edited JSON can still contain unknown names |
| **R2** | correctness | Weights and amounts are not checked → percents sum to 75, amount is NaN or negative → money disappears and `settle` is wrong | `add_expense`, `splits.py` | T04 R2 | 2 | 3 | **6** | **M2** (same root cause as R3) | `M2ValidationTest`: 0, −50, NaN, inf, %≠100, shares ≤ 0, negative weight | 2: `load()` does not re-validate files |
| R7 | agent operations | README sent people to commands that fail; the default file is tracked → an agent improvises → the sample data is modified | README, `ledger.DEFAULT_FILE` | T04 R7 | 3 | 2 | 6 | Task 02: README fixed (every command executed), AGENTS.md "always use a temp `--file`" | `final-readme-commands.txt` | 4: the default is still `data/trip.json` |
| R9 | agent operations | No rules, no CI, shallow tests → regressions go unnoticed | repo | T04 R9 | 2 | 2 | 4 | AGENTS.md, acceptance tests, +18 tests, ruff clean | `final-checks.txt` | 2: still no CI |
| R6 | correctness | `save()` truncates, then writes → a crash or Ctrl-C mid-write → the whole ledger is lost | `ledger.save` | T04 R6 | 1 | 3 | 3 | not yet: proposed for a background agent (Task 08) | test with an injected `json.dump` failure | 3 |
| R5 | correctness | Float money and per-transfer rounding → 1-cent mismatches | `settle`, float amounts | T04 R5 | 3 | 1 | 3 | accepted for now (≤ 0.01 per transfer) | property test with integer cents | 3 |
| R4 | correctness / maintainability | Two copies of the split logic → an unknown type creates money | `ledger.py` | T04 R4 | 1 | 2 | 2 | Task 03 Strategy: unknown → `ValueError` | `test_splits.py` | 1 |
| R11 | agent operations | *(found during M2, not by the AI)* ruff is installed globally and the project has no ruff config → a different ruff version gives a different lint verdict | tooling | ruff 0.17.1 reported PLW1510/SIM115 on new test code (not default rules in older ruff) | 2 | 1 | 2 | none: documented | add `ruff.toml` with pinned `select` + a version note | 2 |
| R8 | dependency | Unpinned, unused `pytest` in `requirements.txt` → confusing setup | `requirements.txt` | T04 R8 | 2 | 1 | 2 | file removed (Task 02) | `final-checks.txt` | 1 |
| R10 | security | `--file` writes to any path | `cli.py` | code reading only | 1 | 1 | 1 | none: unsupported (T04) | none | 1 |

**Top two confirmed risks for corrective action:**

1. **R1 (9).**
2. **R3 / R2 (6 each).** They share one root cause, "nothing is validated at the trust boundary", so a single mitigation covers both.

R7 also scores 6. Its main cause (the wrong README) was already fixed as part of Task 02, and its remaining part (the default file path) changes how the tool is used, so I left it as residual.

---

## Task 06: Agent-readiness audit

| Area | Before | After | Evidence |
|------|--------|-------|----------|
| Readable structure | 3 small modules, split logic duplicated | CLI / ledger / strategies separated | Task 03 |
| README accuracy | 2 of the documented commands fail | every command in README executed, all exit 0 | `final-readme-commands.txt` |
| Reproducible setup | unclear (pip step, pytest) | stdlib only, nothing to install; Python 3.9+ stated | README, AGENTS.md §3 |
| Pinned dependencies | 1 unpinned, unused | none needed | `requirements.txt` removed |
| Tests | 5 happy-path tests | 23 tests: acceptance, strategies, mitigations, CLI end-to-end | `final-checks.txt` |
| Lint | 1 error | `All checks passed!`. The ruff version is not pinned (R11) | `final-checks.txt` |
| Type checks | none | none (no mypy). **Not claimed** | — |
| Build | `compileall` OK | `compileall` OK (pure Python, no build artifact) | `final-checks.txt` |
| Logging / errors | raw tracebacks | `error: <message>` on stderr, exit code 2. Still no log file | M2 evidence |
| Security safeguards | none needed beyond input handling | validation at `add_expense`; no `eval`/`pickle`; fictional data only | M2 |
| AGENTS.md permissions / safe commands / prohibited actions / review gate | — | §4 safe commands, §8 approval-required, §9 never, §10 review gate | `AGENTS.md` |

**Readiness level: 2, Documented.** At the baseline it was level 1, because the README instructions failed and there were no agent rules.

It is not level 3, Agent-ready, because this evidence is missing:

1. CI that runs `unittest` and `ruff` on every branch.
2. A pinned ruff version and a project ruff config.
3. Type checking.
4. Atomic save (R6), so that an interrupted agent run cannot destroy data.
5. Branch protection that enforces the review gate.

---

## Task 07: Mitigation and verification

### M1: R1, participants are fixed when an expense is added (commit `ea515f9`)

**Diff (2 files):**

- `ledger.add_expense` now stores `expense["participants"] = list(ledger["people"])` for equal splits.
- `splits.equal` now uses `expense.get("participants", people)`. Records from before A5 fall back to everyone, so old files still load and AC5 still passes.

**How I reviewed it:** I checked that the fallback keeps `data/trip.json` output byte-identical (AC5 test) and that `percent`/`shares` are not affected, because they already list their people explicitly.

**Tests (written first):** 3 tests in `tests/test_mitigations.py`.

| Run | Result |
|-----|--------|
| Before the fix | `FAIL: test_person_added_later_does_not_pay_for_earlier_equal_expense`, `{'Aru': 67.5, 'Dana': -22.5, 'Timur': -22.5, 'Erlan': -22.5} != {'Aru': 60, 'Dana': -30, 'Timur': -30, 'Erlan': 0}`, i.e. `Ran 3 … FAILED (failures=1)` |
| After the fix | `Ran 14 tests … OK`, ruff clean |
| CLI, temp file | Erlan joins after the taxi: `Aru +60.00, Dana -30.00, Timur -30.00, Erlan +0.00` |

**Score:** 9 → 2.

**Limitation:** old records have no participant list, so their split is still based on the current roster. There is no way to recover who was present.

### M2: R2 and R3, validation at the trust boundary (commit `bb6ff70`)

**Diff:**

- `add_expense` checks the amount (a finite number greater than 0) and that the payer exists. It then runs the split strategy *before* storing the expense, and rejects weight names that are not known people.
- The strategies in `splits.py` check their own weights: they must be present, finite and non-negative; percent weights must sum to 100 (±0.01); shares must sum to more than 0.
- `parse_weights` rejects malformed or duplicate items with a readable message.
- `cli.main` turns any `ValueError` into `error: …` on stderr and exit code 2.

**How I reviewed it:** I deliberately kept the type-specific checks inside each strategy. Putting them in `ledger.py` would have brought back an `if split == …` chain and undone Task 03. Ruff 0.17.1 flagged 4 style issues in the new test (`subprocess.run` without `check`, and `open()` without a context manager). I fixed them, which is how I found R11.

**Tests (written first):** 7 validation tests (with sub-tests) and 2 end-to-end CLI tests.

| Run | Result |
|-----|--------|
| Before the fix | `Ran 9 tests … FAILED (failures=14)`, e.g. `ValueError not raised` for 0/−50/nan/inf, and `Tuples differ: (0, '') != (2, "error: unknown payer 'Ary' (known: Aru, Dana)")` |
| After the fix | `Ran 23 tests … OK`, `ruff check .`: `All checks passed!` |
| CLI, temp file | `add Taxi 40 Ary` → `error: unknown payer 'Ary' (known: Aru, Dana)`, exit 2. `add Refund -50 Aru` → `amount must be a positive number`, exit 2. `nan` → same. Percent 50+25 → `must add up to 100, got 75`. `Aru=50,Dana` → `bad --weights item 'Dana'`. A valid `add Taxi 40 Aru` → exit 0, and `balance` works |

**Score:** R3 6 → 2, R2 6 → 2.

**Limitation:** `load()` does not re-validate a hand-edited file.

### Final checks (`evidence/final-checks.txt`, `final-readme-commands.txt`)

| Check | Baseline | Final |
|-------|----------|-------|
| `python3 -m unittest -v` | 5 run, OK | **23 run, OK** (exit 0) |
| `ruff check .` | 1 error (exit 1) | **All checks passed!** (exit 0) |
| `python3 -m compileall -q tripsplit tests` | exit 0 | exit 0 |
| README commands | 2 fail | **8/8 usage commands exit 0** |
| `git diff a5-baseline -- data/trip.json` | — | empty (sample data untouched) |

**Not executed:**

- Type checking (no tool installed).
- Tests on Python 3.10 and newer. Only 3.9.6 was available.
- CI, because none exists.
- Any test of R6 or R5 fixes, because those were not implemented.

**Screenshots:** none, because this is a CLI. The terminal output is saved as text instead, which is easier to compare.

---

## Task 08: Background agent safeguards (hypothetical)

**Task for an asynchronous agent:** "Make `ledger.save` atomic (R6). Write to a temporary file in the same folder, `fsync` it, then `os.replace` it over the target. Add a test that injects a failure during `json.dump` and checks that the previous file is still intact."

| Control | Plan |
|---------|------|
| Isolation | Branch `agent/r6-atomic-save` in a separate `git worktree`. The agent never sees `main` as writable. |
| Allowed files | `tripsplit/ledger.py`, new `tests/test_storage.py`. Everything else is read-only. |
| Allowed commands | `python3 -m unittest -v`, `ruff check .`, `python3 -m compileall -q tripsplit tests`, `git diff`, `git add`/`commit` on its branch. CLI runs only with a `tempfile` path. |
| Time limit | 20 minutes or 6 test runs, whichever comes first. Stop after 2 consecutive red runs and report. |
| Prohibited | network access, `pip install`, editing `data/`, `docs/evidence/`, `tests/test_acceptance.py`, `AGENTS.md`; deleting or skipping tests; `git push`, `--force`, `reset --hard`, rebase of shared history; reading environment variables or credentials. |
| Artifacts to return | **change summary** (what changed, which risk, why); **unified diff**; **test log** of the full `unittest -v` output before and after; **build result** (`compileall` exit code and `ruff` output); **risk notes** (e.g. "`os.replace` is atomic on POSIX and Windows for the same volume; not verified on network drives"). |
| Human review | Anel reads the whole diff, runs the new test on `main` to see it fail, re-runs all checks locally, and approves the merge. No auto-merge, no deploy step. |
| Failure handling | If any check is red at the time limit, the agent stops and returns the logs. The branch is kept for inspection and the worktree is removed. A weakened test is grounds for rejecting the change. |
| Rollback | Merge as one commit, so `git revert <sha>` restores the previous `save()`. User data is not migrated, so a rollback needs no data change. |

---

## Task 09: Release decision

**Decision: CONDITIONAL.** This is for the reviewed version (`main` after commit `bb6ff70` plus the documentation), used as a personal trip-splitting tool with fictional or own data.

**Why it is not NO-GO.** All critical checks pass: 23/23 tests, lint clean, all README commands work, and the acceptance criteria hold. The two highest risks (R1 = 9, R2/R3 = 6) are mitigated and verified with tests that failed before the fix.

**Why it is not GO.** Known limitations remain:

- R6: a crash during save loses data (score 3).
- R5: settle-up can be off by 1 cent.
- R7: without `--file`, the tool writes to the tracked sample.
- R11: the lint result depends on the installed ruff version.

None of these is unacceptable for a single-user tool, but each needs a control:

| Condition | Control | Owner |
|-----------|---------|-------|
| R6 | Keep a backup: commit or copy the ledger file before a long session. The atomic save from Task 08 must be merged before any shared use. | Anel |
| R5 | Treat differences of ≤ 0.01 as settled (documented in AGENTS.md §5). Move to integer cents before handling real money. | Anel |
| R7 | Always pass `--file` (README and AGENTS.md). Next step: change the default to the current folder. | Anel |
| R11 / R9 | Before merging, run `ruff --version` and include it in the PR. Add CI and a pinned ruff later. | Anel |

---

## Task 10: AI reflection

I used Claude Code with the Claude Opus 5.5 model. The assistant received the assignment slides, my repository and, once I had written it, AGENTS.md. For the risk review I used a separate read-only sub-agent. Its whole context was the repository path and a prompt that forbade edits and any command that would write to the sample ledger, so it could not "fix while reviewing".

The most useful suggestion was R1: an equal split is recalculated with whoever is in the group *now*. I had tested splits only with a fixed group of three, so I never thought about someone joining halfway through a trip. Reproducing it took one line, and it became my highest risk (score 9) and my first mitigation.

The weakest claims were R10 and the supply-chain part of R8. Calling `--file` a security risk ignores the fact that the path comes from the user's own command line, and nothing ever installs `pytest`, so I marked both unsupported. The AI was also too careful about R6. It called the non-atomic save only "plausible". I injected a failure into `save()` and watched the previous ledger become unreadable, so I changed it to confirmed.

I checked every finding myself with temporary files, and I left `data/trip.json` untouched, as `git diff` shows. Tests changed my decisions. Because I wrote the failing tests first, I could see 14 failures turn into passes. Running ruff on the new tests exposed R11, which no AI review had mentioned.

AGENTS.md helped most by banning writes to the sample file and requiring real numbers. Next I would add CI and pin the ruff version, so that these rules are enforced by tools and not only by text.

---

## Appendix: AI evidence and use record

| # | Date | Tool / model | Prompt summary | Output used | Problems found in the output | Decision / change | Verified by |
|---|------|--------------|----------------|-------------|------------------------------|-------------------|-------------|
| 1 | 2026-11-22 | Claude Code, Opus 5.5 | Read the assignment PDF and plan the work; create a small existing-style project for the baseline | baseline TripSplit code (commit `c902570`) and the work plan | baseline written with AI help on the same day; the README already contained wrong commands | kept as the honest starting point and tagged `a5-baseline` | `baseline-*.txt` |
| 2 | 2026-11-22 | Claude Code read-only sub-agent, Opus 5.5 | Read-only risk review, 8–10 risks, 5 categories, confidence and L/I (full prompt in the evidence file) | 10 candidate risks | R6 under-confident; R8 supply-chain and R10 overstated | classified in Task 04; R6 upgraded, R10 rejected | `ai-risk-review-raw.md`, `verify-ai-findings-baseline.txt` |
| 3 | 2026-11-22 | Claude Code, Opus 5.5 | Write AGENTS.md / CLAUDE.md, fix README | files | the first draft described `splits.py` before it existed | corrected so that each commit is accurate | `git show 1e61dac`, `a991a92` |
| 4 | 2026-11-22 | Claude Code, Opus 5.5 | Task 03 Strategy refactor | `splits.py` + 2 tests | none | accepted after AC2–AC5 passed before and after | `task3-strategy-before-after.txt` |
| 5 | 2026-11-22 | Claude Code, Opus 5.5 | M1, test-first | 3 tests + 2-line fix | none | accepted | `mitigation-M1-participants.txt` |
| 6 | 2026-11-22 | Claude Code, Opus 5.5 | M2, test-first | validation + CLI error handling + 9 tests | 4 ruff findings in the new test; a shell quoting mistake in the first evidence capture | fixed both and re-captured the evidence | `mitigation-M2-validation.txt` |
| 7 | 2026-11-22 | Claude Code, Opus 5.5 | Draft this report from the evidence files | report text | every number was checked against `docs/evidence/` | edited and approved by me | `docs/evidence/*` |

**Commit hashes:** before publishing, the author e-mail of every commit was changed from a placeholder to my GitHub no-reply address with `git filter-branch`. The content is unchanged, but the hashes are new, so the hashes quoted in this report and in `evidence/ai-risk-review-raw.md` were updated to match.

**Human verification:**

- The results come from raw command output saved in `docs/evidence/`. No result was typed by hand.
- The sample data contains only fictional names.
- Every commit carries a `Co-Authored-By: Claude` trailer that discloses AI assistance.
