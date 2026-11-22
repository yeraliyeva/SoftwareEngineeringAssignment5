# TripSplit

Small command-line tool that splits shared trip expenses between friends and tells
everyone who owes whom. Pure Python standard library, no packages to install.
Sample data lives in `data/trip.json` (fictional names and amounts).

**Assignment #05 (Yeraliyeva Anel, 24B031020):** report in [`docs/ASSIGNMENT5.md`](docs/ASSIGNMENT5.md),
agent rules in [`AGENTS.md`](AGENTS.md). Baseline = tag `a5-baseline`.

## Requirements

Python 3.9 or newer. Optional: `ruff` for linting.

## Usage

Without `--file` the tool reads and **writes** `data/trip.json`. Use your own file for experiments:

```bash
python3 -m tripsplit --file my-trip.json person Aru
python3 -m tripsplit --file my-trip.json person Dana
python3 -m tripsplit --file my-trip.json person Timur
python3 -m tripsplit --file my-trip.json add "Taxi" 90 Aru
python3 -m tripsplit --file my-trip.json add "Hotel" 200 Dana --split percent --weights "Aru=50,Dana=25,Timur=25"
python3 -m tripsplit --file my-trip.json list
python3 -m tripsplit --file my-trip.json balance
python3 -m tripsplit --file my-trip.json settle
```

Split types: `equal`, `percent` (weights add up to 100), `shares` (any positive numbers).

## Checks

```bash
python3 -m unittest -v                     # tests
ruff check .                               # lint
python3 -m compileall -q tripsplit tests   # syntax check
```
