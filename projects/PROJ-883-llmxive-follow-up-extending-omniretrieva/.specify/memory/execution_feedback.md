# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: run-book completed but produced no data/figure artifacts; 1 declared deliverable(s) absent: data/processed/generation_log.json

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/processed/generation_log.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **102023** real records with fields: answers, passages, query, query_id, query_type, wellFormedAnswers.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

data = datasets.load_dataset("microsoft/ms_marco", "v1.1")
total_records = sum(len(split) for split in data.values())
first_split = next(iter(data.values()))
print(f"RECORDS={total_records}")
print("FIELDS=" + ",".join(first_split.column_names))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/generation_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/benchmark_runner.py` — NOT invoked by the run-book
    - `code/generators/synthetic_query.py` — NOT invoked by the run-book
    - `code/query_generator.py` — NOT invoked by the run-book
    - `code/router/sut_router.py` — NOT invoked by the run-book
    - `code/transform_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/generation_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
