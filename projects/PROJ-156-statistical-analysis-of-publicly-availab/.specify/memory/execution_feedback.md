# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest code/tests/ (rc=2); 3 declared deliverable(s) absent: data/checkpoints/fetch_checkpoint.json; data/processed/distribution_fits.csv; data/processed/run_records.csv

## Failing / missing run-book commands

- python -m pytest code/tests/ -> rc=2
_mixed_effects.py:20: in <module>
    from scripts.preprocess import load_config, load_schema, validate_record
code/scripts/preprocess.py:181: in <module>
    schema: Union[Dict[str, List[str]], List[str]] = None,
E   NameError: name 'Union' is not defined
_ ERROR collecting projects/PROJ-156-statistical-analysis-of-publicly-availab/code/tests/test_preprocess_checkpoint.py _
code/tests/test_preprocess_checkpoint.py:14: in <module>
    from scripts.preprocess import main, load_config, setup_logging
code/scripts/preprocess.py:181: in <module>
    schema: Union[Dict[str, List[str]], List[str]] = None,
E   NameError: name 'Union' is not defined
=========================== short test summary info ============================
ERROR code/tests/test_distribution_fitting.py - NameError: name 'Union' is no...
ERROR code/tests/test_fetch.py - NameError: name 'Union' is not defined
ERROR code/tests/test_models.py - NameError: name 'Union' is not defined
ERROR code/tests/test_preprocess_checkpoint.py - NameError: name 'Union' is n...
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.76s ===============================



## Declared deliverables still missing

- data/checkpoints/fetch_checkpoint.json
- data/processed/distribution_fits.csv
- data/processed/run_records.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `speedruncomapi` to the project's `requirements.txt` and `pip install speedruncomapi`.
- **Verified**: this loads **10000** real records with fields: id, weblink, game, level, category, videos, comment, status, players, date, date-time, submitted, times, system, splits, values, links.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from speedruncomapi import requests

url = "https://www.speedrun.com/api/v1/runs"
params = {"max": 200, "offset": 0}
all_runs = []

while True:
    resp = requests.get(url, params=params)
    data = resp.json()
    batch = data.get("data", [])
    if not batch:
        break
    all_runs.extend(batch)
    if len(batch) < params["max"]:
        break
    params["offset"] += params["max"]

print(f"RECORDS={len(all_runs)}")
if all_runs:
    fields = list(all_runs[0].keys())
    print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checkpoints/fetch_checkpoint.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fetch_data.py` — NOT invoked by the run-book
    - `code/scripts/utils/checkpoint.py` — NOT invoked by the run-book
    - `code/tests/test_fetch_checkpoint.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checkpoints/fetch_checkpoint.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/distribution_fits.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fit_distributions.py` — NOT invoked by the run-book
    - `code/scripts/generate_report.py` — NOT invoked by the run-book
    - `code/scripts/utils/bonferroni.py` — NOT invoked by the run-book
    - `code/scripts/validate_distribution_fits.py` — NOT invoked by the run-book
    - `code/tests/test_distribution_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/distribution_fits.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/run_records.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fit_distributions.py` — NOT invoked by the run-book
    - `code/scripts/fit_mixed_effects.py` — NOT invoked by the run-book
    - `code/scripts/generate_report.py` — NOT invoked by the run-book
    - `code/scripts/preprocess.py` — NOT invoked by the run-book
    - `code/scripts/utils/pressure.py` — NOT invoked by the run-book
    - `code/tests/test_distribution_fitting.py` — NOT invoked by the run-book
    - `code/tests/test_models.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/run_records.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
