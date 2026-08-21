# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python src/main.py --stage ingestion; python src/main.py --stage preprocessing; python src/main.py --stage synthesis; 2 declared deliverable(s) absent: data/results/filtered_features.json; data/results/regression_model.json

## Failing / missing run-book commands

- python src/main.py --stage ingestion -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage preprocessing -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage synthesis -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage hypothesis_testing -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage regression -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage viz -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/results/filtered_features.json
- data/results/regression_model.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `yfinance` to the project's `requirements.txt` and `pip install yfinance`.
- **Verified**: this loads **5** real records with fields: timestamp, value, series_id.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import yfinance as yf, pandas as pd
ticker = "AAPL"
# Download recent daily closing prices
df = yf.download(ticker, period="5d", interval="1d")
# Keep date, close price and add series identifier
df = df.reset_index()[["Date", "Close"]]
df["series_id"] = ticker
# Rename to required field names
df = df.rename(columns={"Date": "timestamp", "Close": "value"})
print(f"RECORDS={len(df)}")
print("FIELDS=timestamp,value,series_id")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/filtered_features.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression_inputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/filtered_features.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/regression_model.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/regression_model.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
