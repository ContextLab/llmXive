# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash code/run_pipeline.sh; 2 command(s) failed: python code/data_loader.py (rc=1); python -m pytest tests/ -v (rc=2); 3 declared deliverable(s) absent: data/processed/first_arrival_sweep.csv; data/raw/checksums.json; data/raw/ebd_subset.csv

## Failing / missing run-book commands

- python code/data_loader.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-126-predicting-avian-migration-patterns-from/code/data_loader.py", line 11, in <module>
    import datasets
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-126-predicting-avian-migration-patterns-from/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-126-predicting-avian-migration-patterns-from/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-126-predicting-avian-migration-patterns-from/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- bash code/run_pipeline.sh -> rc=-1

shell script must be an existing project-local .sh file
- python -m pytest tests/ -v -> rc=2
y311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_data_loader_ebird.py
ERROR tests/unit/test_data_loader.py
ERROR tests/unit/test_first_arrival_sweep.py
ERROR tests/unit/test_grid_aggregation.py
ERROR tests/unit/test_regional_map.py - NameError: name 'Optional' is not def...
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 20 warnings, 5 errors in 1.00s ========================



## Declared deliverables still missing

- data/processed/first_arrival_sweep.csv
- data/raw/checksums.json
- data/raw/ebd_subset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/first_arrival_sweep.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/first_arrival_sweep.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_loader.py` — IS a run-book command
    - `code/data_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ebd_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/ebd_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
