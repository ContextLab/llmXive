# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 6 declared deliverable(s) absent: data/processed/bias_flag.json; data/processed/metrics_all.csv; data/processed/metrics_valid.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l/code/main.py", line 14, in <module>
    from analysis.reporter import run_reporter_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l/code/analysis/reporter.py", line 9, in <module>
    import matplotlib
ModuleNotFoundError: No module named 'matplotlib'

## Declared deliverables still missing

- data/processed/bias_flag.json
- data/processed/metrics_all.csv
- data/processed/metrics_valid.csv
- data/processed/samples_all.csv
- data/processed/samples_valid.csv
- data/processed/sensitivity_results.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import sys
from datasets import load_dataset

data = load_dataset("openai/openai_humaneval")
if isinstance(data, dict):
    total = sum(len(split) for split in data.values())
    # get a sample record from the first non‑empty split
    sample = {}
    for split in data.values():
        if len(split) > 0:
            sample = split[0]
            break
else:
    total = len(data)
    sample = data[0] if total > 0 else {}

if total == 0:
    raise RuntimeError("Loaded dataset contains zero records")

fields = list(sample.keys()) if isinstance(sample, dict) else []

print(f"RECORDS={total}")
if fields:
    print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/bias_flag.json` is declared but was NOT written. Scripts referencing it:
    - `code/generation/pipeline.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bias_flag.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_all.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/generation/directories.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_all.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_valid.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_valid.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/samples_all.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/generation/pipeline.py` — NOT invoked by the run-book
    - `code/generation/generator.py` — NOT invoked by the run-book
    - `code/generation/tester.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/samples_all.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/samples_valid.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/generation/directories.py` — NOT invoked by the run-book
    - `code/generation/pipeline.py` — NOT invoked by the run-book
    - `code/generation/tester.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/samples_valid.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
