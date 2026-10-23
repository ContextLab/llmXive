# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest -q tests/contract/  # validates raw_price, regime_labels, rsvart_output schemas (rc=4); 1 declared deliverable(s) absent: data/checksums.json

## Failing / missing run-book commands

- python -m pytest -q tests/contract/  # validates raw_price, regime_labels, rsvart_output schemas -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: #



## Declared deliverables still missing

- data/checksums.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `pycoingecko` to the project's `requirements.txt` and `pip install pycoingecko`.
- **Verified**: this loads **180** real records with fields: timestamp, open, high, low, close.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()
ohlc = cg.get_coin_ohlc_by_id(id="bitcoin", vs_currency="usd", days=30)
if not ohlc:
    raise ValueError("No OHLC data returned")

records = [
    {
        "timestamp": entry[0],
        "open": entry[1],
        "high": entry[2],
        "low": entry[3],
        "close": entry[4],
    }
    for entry in ohlc
]

print(f"RECORDS={len(records)}")
print("FIELDS=timestamp,open,high,low,close")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_raw_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
