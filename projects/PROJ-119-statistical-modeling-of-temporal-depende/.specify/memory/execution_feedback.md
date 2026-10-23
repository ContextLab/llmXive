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
- **Verified**: this loads **62** real records with fields: date, open, high, low, close, volume.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from pycoingecko import CoinGeckoAPI
import time, datetime

cg = CoinGeckoAPI()
# time range: last 30 days
end_ts = int(time.time())
start_ts = end_ts - 30 * 24 * 60 * 60

coins = ["bitcoin", "ethereum"]
records = []
for coin in coins:
    # OHLC data (open, high, low, close) – returns list of [timestamp, o, h, l, c]
    ohlc = cg.get_coin_ohlc_by_id(id=coin, vs_currency="usd", days=30)
    daily = {}
    for ts, o, h, l, c in ohlc:
        d = datetime.datetime.utcfromtimestamp(ts / 1000).date().isoformat()
        daily[d] = {"date": d, "open": o, "high": h, "low": l, "close": c}
    # Volume data – list of [timestamp, volume]
    vol_data = cg.get_coin_market_chart_range_by_id(
        id=coin, vs_currency="usd", from_timestamp=start_ts, to_timestamp=end_ts
    )
    for ts, v in vol_data.get("total_volumes", []):
        d = datetime.datetime.utcfromtimestamp(ts / 1000).date().isoformat()
        if d in daily:
            daily[d]["volume"] = v
    # keep only days where volume was merged
    for rec in daily.values():
        if "volume" in rec:
            records.append(rec)

print(f"RECORDS={len(records)}")
print("FIELDS=date,open,high,low,close,volume")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_raw_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
