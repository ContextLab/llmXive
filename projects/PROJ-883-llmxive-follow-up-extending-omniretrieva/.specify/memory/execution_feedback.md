# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: run-book completed but produced no data/figure artifacts; 4 declared deliverable(s) absent: data/processed/baseline_overhead.json; data/processed/cost_table.json; data/processed/generation_log.json

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/processed/baseline_overhead.json
- data/processed/cost_table.json
- data/processed/generation_log.json
- data/processed/optimal_ground_truth.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **102023** real records with fields: answers, passages, query, query_id, query_type, wellFormedAnswers.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from datasets import load_dataset

# Load the full dataset (use a valid config name)
dataset_dict = load_dataset("microsoft/ms_marco", name="v1.1")

# Count total records across all splits
total_records = sum(len(split) for split in dataset_dict.values())
print(f"RECORDS={total_records}")

# Show field names from a sample record
first_split = next(iter(dataset_dict.values()))
sample_record = first_split[0]
print(f"FIELDS={','.join(sample_record.keys())}")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_overhead.json` is declared but was NOT written. Scripts referencing it:
    - `code/baseline_overhead.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_overhead.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cost_table.json` is declared but was NOT written. Scripts referencing it:
    - `code/generators/reference_engine.py` — NOT invoked by the run-book
    - `code/planners/optimal_planner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cost_table.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/generation_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/benchmark_runner.py` — NOT invoked by the run-book
    - `code/generators/reference_engine.py` — NOT invoked by the run-book
    - `code/generators/run_synthetic_query.py` — NOT invoked by the run-book
    - `code/generators/synthetic_query.py` — NOT invoked by the run-book
    - `code/planners/optimal_planner.py` — NOT invoked by the run-book
    - `code/query_generator.py` — NOT invoked by the run-book
    - `code/router/sut_router.py` — NOT invoked by the run-book
    - `code/transform_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/generation_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/optimal_ground_truth.json` is declared but was NOT written. Scripts referencing it:
    - `code/planners/optimal_planner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/optimal_ground_truth.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
