# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py --num-tasks 100 --output-dir data/processed (rc=2); 1 declared deliverable(s) absent: data/processed/sensitivity_report.csv

## Failing / missing run-book commands

- python code/main.py --num-tasks 100 --output-dir data/processed -> rc=2
    Warning: LLM_API_KEY not found in environment. Local models will be used if available.

usage: main.py [-h] [--dataset DATASET] [--model MODEL]
               [--batch-size BATCH_SIZE] [--output-dir OUTPUT_DIR]
               [--catalog-path CATALOG_PATH]
main.py: error: unrecognized arguments: --num-tasks 100

## Declared deliverables still missing

- data/processed/sensitivity_report.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real, installable source was discovered AND verified by actually loading data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

ds_dict = datasets.load_dataset('openai/openai_humaneval')
total_records = sum(len(split) for split in ds_dict.values())
print(f"RECORDS={total_records}")

first_split = next(iter(ds_dict.values()))
print("FIELDS=" + ",".join(first_split.column_names))
```

Write the loader to use this package/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/sensitivity_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyzer.py` — NOT invoked by the run-book
    - `code/sensitivity_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
