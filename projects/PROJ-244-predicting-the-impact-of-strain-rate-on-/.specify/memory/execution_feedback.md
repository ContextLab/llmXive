# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/ingestion/fetchers.py --mode simulated --output data/raw/simulated_tensile.csv`
  - script usage: `fetchers.py [-h] [--mode {real,dry-run}]`
  - argparse error: `fetchers.py: error: argument --mode: invalid choice: 'simulated' (choose from 'real', 'dry-run')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 4 command(s) failed: python code/ingestion/fetchers.py --mode simulated --output data/raw/simulated_tensile.csv (rc=2); python code/ingestion/fetchers.py --mode real (rc=-1); python -m pytest tests/contract/ -v (rc=2); 5 declared deliverable(s) absent: data/processed/encoded_features.csv; data/processed/failure_regimes.csv; data/processed/test.csv

## Failing / missing run-book commands

- python code/ingestion/fetchers.py --mode simulated --output data/raw/simulated_tensile.csv -> rc=2

usage: fetchers.py [-h] [--mode {real,dry-run}]
fetchers.py: error: argument --mode: invalid choice: 'simulated' (choose from 'real', 'dry-run')

- python code/ingestion/fetchers.py --mode real -> rc=-1

2026-10-22 01:33:53,018 INFO root: Starting [get] request for the URL https://www.openml.org/api/v1/xml/data/1234

[TIMEOUT after 120s]
- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-244-predicting-the-impact-of-strain-rate-on-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -v -> rc=2
/work/llmXive/llmXive/projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/contract/test_model_output_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/contract/test_model_output_schema.py:13: in <module>
    from ingestion.preprocess import load_config
code/ingestion/preprocess.py:15: in <module>
    from ingestion.preprocess import (
E   ImportError: cannot import name 'load_raw_for_sensitivity' from partially initialized module 'ingestion.preprocess' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py)
=========================== short test summary info ============================
ERROR code/tests/contract/test_dataset_schema.py
ERROR code/tests/contract/test_model_output_schema.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.95s ===============================


- python -m pytest tests/ -v -> rc=2
1868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_plots.py
ERROR tests/unit/test_sample_size_estimator.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 2 errors in 1.90s ========================



## Declared deliverables still missing

- data/processed/encoded_features.csv
- data/processed/failure_regimes.csv
- data/processed/test.csv
- data/processed/train.csv
- data/raw/raw_input.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/encoded_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/preprocess.py` — NOT invoked by the run-book
    - `code/modeling/ml_models.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/contract/test_dataset_schema.py` — NOT invoked by the run-book
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/encoded_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/failure_regimes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/reporting/append_failure_regimes.py` — NOT invoked by the run-book
    - `code/visualization/failure_regimes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/failure_regimes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/preprocess.py` — NOT invoked by the run-book
    - `code/modeling/evaluation.py` — NOT invoked by the run-book
    - `code/modeling/ml_models.py` — NOT invoked by the run-book
    - `code/modeling/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/reporting/append_failure_regimes.py` — NOT invoked by the run-book
    - `code/reporting/compile_metrics.py` — NOT invoked by the run-book
    - `code/tests/contract/test_dataset_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/preprocess.py` — NOT invoked by the run-book
    - `code/modeling/empirical_models.py` — NOT invoked by the run-book
    - `code/modeling/evaluation.py` — NOT invoked by the run-book
    - `code/modeling/ml_models.py` — NOT invoked by the run-book
    - `code/modeling/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/reporting/append_failure_regimes.py` — NOT invoked by the run-book
    - `code/research/sample_size_estimator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/raw_input.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/fetchers.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/raw_input.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
