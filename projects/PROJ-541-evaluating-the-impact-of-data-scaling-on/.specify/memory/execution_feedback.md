# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/main.py --mode simulation (rc=1); python code/main.py --mode real_world (rc=1); python code/main.py --mode simulation --config-id "test-config-1" --iterations 100 (rc=1); 1 declared deliverable(s) absent: data/config/seed_config.json

## Failing / missing run-book commands

- python code/main.py --mode simulation -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 24, in <module>
    from simulation.persistence import save_synthetic_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/persistence.py", line 13, in <module>
    from simulation.schema import save_seed_config, compute_config_hash, load_seed_config, validate_seed_config
ImportError: cannot import name 'save_seed_config' from 'simulation.schema' (/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/schema.py)

- python code/main.py --mode real_world -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 24, in <module>
    from simulation.persistence import save_synthetic_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/persistence.py", line 13, in <module>
    from simulation.schema import save_seed_config, compute_config_hash, load_seed_config, validate_seed_config
ImportError: cannot import name 'save_seed_config' from 'simulation.schema' (/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/schema.py)

- python code/main.py --mode simulation --config-id "test-config-1" --iterations 100 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 24, in <module>
    from simulation.persistence import save_synthetic_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/persistence.py", line 13, in <module>
    from simulation.schema import save_seed_config, compute_config_hash, load_seed_config, validate_seed_config
ImportError: cannot import name 'save_seed_config' from 'simulation.schema' (/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/schema.py)

- python code/main.py --mode visualize -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 24, in <module>
    from simulation.persistence import save_synthetic_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/persistence.py", line 13, in <module>
    from simulation.schema import save_seed_config, compute_config_hash, load_seed_config, validate_seed_config
ImportError: cannot import name 'save_seed_config' from 'simulation.schema' (/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/schema.py)

- python code/main.py --mode analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 24, in <module>
    from simulation.persistence import save_synthetic_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/persistence.py", line 13, in <module>
    from simulation.schema import save_seed_config, compute_config_hash, load_seed_config, validate_seed_config
ImportError: cannot import name 'save_seed_config' from 'simulation.schema' (/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/schema.py)

- python code/main.py --mode verify-checksums -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/main.py", line 24, in <module>
    from simulation.persistence import save_synthetic_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/persistence.py", line 13, in <module>
    from simulation.schema import save_seed_config, compute_config_hash, load_seed_config, validate_seed_config
ImportError: cannot import name 'save_seed_config' from 'simulation.schema' (/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/code/simulation/schema.py)

- python -m pytest tests/unit/ -> rc=2
t-of-data-scaling-on/code/simulation/schema.py)
_____ ERROR collecting tests/unit/validation/test_quickstart_validation.py _____
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/tests/unit/validation/test_quickstart_validation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/validation/test_quickstart_validation.py:16: in <module>
    from validation.quickstart_validation import check_directories, run_aggregation
E   ModuleNotFoundError: No module named 'validation'
=========================== short test summary info ============================
ERROR tests/unit/preprocessing/test_ingestion.py
ERROR tests/unit/simulation/test_logger.py
ERROR tests/unit/simulation/test_main.py
ERROR tests/unit/validation/test_quickstart_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 1.38s ===============================



## Declared deliverables still missing

- data/config/seed_config.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `openml` to the project's `requirements.txt` and `pip install openml`.
- **Verified**: this loads **48842** real records with fields: sample_id, age, fnlwgt, education-num, capital-gain, capital-loss, hours-per-week, group_label, outcome.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import openml, pandas as pd
# Load the UCI Adult dataset via OpenML (ID 1590)
dataset = openml.datasets.get_dataset(1590)
X, y, _, _ = dataset.get_data(dataset_format='dataframe')
df = X.copy()
# Append target as numeric outcome (0/1)
df['outcome'] = y
# Map the binary protected attribute "sex" to group_label (Male=0, Female=1)
if 'sex' not in df.columns:
    raise ValueError('group column "sex" missing')
df['group_label'] = df['sex'].map({'Male': 0, 'Female': 1})
if df['group_label'].isnull().any():
    raise ValueError('unexpected values in group column')
# Create a sample identifier
df = df.reset_index().rename(columns={'index': 'sample_id'})
# Determine numeric feature columns (exclude identifiers and target columns)
numeric_cols = df.select_dtypes(include='number').columns.tolist()
for col in ['sample_id', 'outcome', 'group_label']:
    if col in numeric_cols:
        numeric_cols.remove(col)
feature_cols = numeric_cols
fields = ['sample_id'] + feature_cols + ['group_label', 'outcome']
print(f'RECORDS={len(df)}')
print('FIELDS=' + ','.join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/config/seed_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/simulation/logger.py` — NOT invoked by the run-book
    - `code/simulation/persistence.py` — NOT invoked by the run-book
    - `code/simulation/schema.py` — NOT invoked by the run-book
    - `code/tests/unit/simulation/test_logger.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/config/seed_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
