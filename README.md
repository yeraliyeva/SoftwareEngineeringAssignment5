# TripSplit

Small command-line tool that splits shared trip expenses between friends and tells
everyone who owes whom. Data lives in `data/trip.json` (fictional sample data).

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py person Aru
python main.py add "Taxi" 90 Aru
python main.py add "Hotel" 200 Dana --split percent --weights "Aru=50,Dana=25,Timur=25"
python main.py balance
python main.py settle
```

Split types: `equal`, `percent`, `shares`.

## Tests

```bash
pytest
```
