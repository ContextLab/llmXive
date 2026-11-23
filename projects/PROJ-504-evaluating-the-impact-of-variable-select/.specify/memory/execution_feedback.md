# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/verify.py --check-memory --check-runtime`
  - script usage: `verify.py [-h] [--mode {pilot,check}] [--count COUNT] [--seed SEED]`
  - argparse error: `verify.py: error: unrecognized arguments: --check-memory --check-runtime`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/main.py --mode simulate; python code/main.py --mode analyze; python code/main.py --mode paper; 3 command(s) failed: python code/data/downloader.py (rc=1); python -m pytest tests/ -v (rc=1); python code/verify.py --check-memory --check-runtime (rc=2); 1 declared deliverable(s) absent: data/processed/simulation_results.csv

## Failing / missing run-book commands

- python code/data/downloader.py -> rc=1
nloader.py:185: FutureWarning: Support for `dataset_format='array'` will be removed in 0.15,start using `dataset_format='dataframe' to ensure your code will continue to work. You can use the dataframe's `to_numpy` function to continue using numpy arrays.
  X, y, categorical, attribute_names = dataset_obj.get_data(
/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/data/downloader.py:185: FutureWarning: Support for `dataset_format='array'` will be removed in 0.15,start using `dataset_format='dataframe' to ensure your code will continue to work. You can use the dataframe's `to_numpy` function to continue using numpy arrays.
  X, y, categorical, attribute_names = dataset_obj.get_data(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/data/downloader.py", line 343, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/data/downloader.py", line 301, in main
    raise RuntimeError("No valid datasets found after validation")
RuntimeError: No valid datasets found after validation

- python code/main.py --mode simulate -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/main.py': [Errno 2] No such file or directory

- python code/main.py --mode analyze -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/main.py': [Errno 2] No such file or directory

- python code/main.py --mode paper -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-504-evaluating-the-impact-of-variable-select/code/.venv/bin/python: No module named pytest

- python code/verify.py --check-memory --check-runtime -> rc=2

usage: verify.py [-h] [--mode {pilot,check}] [--count COUNT] [--seed SEED]
verify.py: error: unrecognized arguments: --check-memory --check-runtime


## Declared deliverables still missing

- data/processed/simulation_results.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `openml` to the project's `requirements.txt` and `pip install openml`.
- **Verified**: this loads **5300** real records with fields: dataset_id, feature_names, X, y, n_rows, n_features.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import openml, pandas as pd
# Load a known regression dataset (e.g., Diabetes dataset, OpenML ID 1460)
dataset = openml.datasets.get_dataset(1460)
# Retrieve the data as a pandas DataFrame
X, y, _, attribute_names = dataset.get_data(dataset_format='dataframe')
# Compute required fields
dataset_id = dataset.dataset_id
feature_names = list(X.columns)
n_rows = X.shape[0]
n_features = X.shape[1]
# Record count is number of rows (samples)
print(f'RECORDS={n_rows}')
# List which of the required fields are present
fields = ['dataset_id','feature_names','X','y','n_rows','n_features']
print('FIELDS=' + ','.join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/simulation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/simulation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
