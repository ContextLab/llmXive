# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --action download (rc=1); python code/main.py --action run --dataset openml_42803 --iterations 2000 (rc=1); python code/main.py --action visualize --output figures/ (rc=1); 3 declared deliverable(s) absent: data/processed/comparison_results.json; data/processed/power_results.json; data/processed/us1_results.json

## Failing / missing run-book commands

- python code/main.py --action download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 23, in <module>
    logging.FileHandler('code/logs/main.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'

- python code/main.py --action run --dataset openml_42803 --iterations 2000 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 23, in <module>
    logging.FileHandler('code/logs/main.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'

- python code/main.py --action visualize --output figures/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/main.py", line 23, in <module>
    logging.FileHandler('code/logs/main.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'

- python -m pytest tests/ -v -> rc=2
 ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_simulation.py:20: in <module>
    from simulation import simulate_missingness, permute_treatment_labels
E   ImportError: cannot import name 'simulate_missingness' from 'simulation' (/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/simulation.py)
=========================== short test summary info ============================
ERROR tests/integration/test_us2_sensitivity.py - FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-436-assessing-the-validity-of-statistical-si/code/logs/main.log'
ERROR tests/test_config.py
ERROR tests/test_logging.py
ERROR tests/unit/test_simulation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 1.30s ===============================



## Declared deliverables still missing

- data/processed/comparison_results.json
- data/processed/power_results.json
- data/processed/us1_results.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `openml` to the project's `requirements.txt` and `pip install openml`.
- **Verified**: this loads **768** real records with fields: outcome, covariate1.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import openml, pandas as pd
# Diabetes dataset (OpenML ID 37)
ds = openml.datasets.get_dataset(37)
df = ds.get_data(dataset_format='dataframe')[0]
records = len(df)
print(f'RECORDS={records}')
# Map requested generic fields to actual column names in this dataset
field_map = {
    'treatment': [],
    'outcome': ['class', 'target', 'y'],
    'covariate1': ['glucose', 'age'],
    'covariate2': ['bmi', 'blood_pressure']
}
present = [generic for generic, cols in field_map.items() if any(col in df.columns for col in cols)]
print('FIELDS=' + ','.join(present))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/comparison_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/visualize.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/comparison_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main_power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/power_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/us1_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main_us1.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/us1_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
