# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python src/main.py --stage ingestion; python src/main.py --stage preprocessing; python src/main.py --stage synthesis; 2 command(s) failed: python -m pytest tests/unit/ (rc=2); python -m pytest tests/integration/ (rc=2); 6 declared deliverable(s) absent: data/processed/metrics.json; data/results/baseline_status.json; data/results/filtered_features.json

## Failing / missing run-book commands

- python src/main.py --stage ingestion -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory

- python src/main.py --stage preprocessing -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory

- python src/main.py --stage synthesis -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory

- python src/main.py --stage hypothesis_testing -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory

- python src/main.py --stage regression -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory

- python src/main.py --stage viz -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
les/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_validation.py:10: in <module>
    from src.synthesis.validation import (
src/synthesis/validation.py:16: in <module>
    from src.data.metrics import compute_acf_lag20
E   ImportError: cannot import name 'compute_acf_lag20' from 'src.data.metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/data/metrics.py)
=========================== short test summary info ============================
ERROR tests/unit/test_baseline_validation.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_preprocessing.py
ERROR tests/unit/test_regression.py
ERROR tests/unit/test_synthesis.py
ERROR tests/unit/test_synthesis_metrics.py
ERROR tests/unit/test_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 8 errors in 1.65s ===============================


- python -m pytest tests/integration/ -> rc=2
ation/test_ingestion.py _____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/tests/integration/test_ingestion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_ingestion.py:19: in <module>
    from src.data.ingestion import load_noaa_etalon
E   ImportError: cannot import name 'load_noaa_etalon' from 'src.data.ingestion' (/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/data/ingestion.py)
=========================== short test summary info ============================
ERROR tests/integration/test_baseline_validity.py
ERROR tests/integration/test_data_pipeline.py
ERROR tests/integration/test_ingestion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 1.20s ===============================



## Declared deliverables still missing

- data/processed/metrics.json
- data/results/baseline_status.json
- data/results/filtered_features.json
- data/results/null_distribution_gate.json
- data/results/regression_model.json
- data/results/synthetic_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_feature_filter.py` — NOT invoked by the run-book
    - `code/scripts/run_metrics_real.py` — NOT invoked by the run-book
    - `code/scripts/run_metrics_synthetic.py` — NOT invoked by the run-book
    - `code/scripts/run_metrics_verification.py` — NOT invoked by the run-book
    - `code/scripts/verify_regression_implementation.py` — NOT invoked by the run-book
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/src/data/metrics.py` — NOT invoked by the run-book
    - `code/src/data/schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/baseline_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/baseline_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/filtered_features.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_feature_filter.py` — NOT invoked by the run-book
    - `code/scripts/verify_regression_implementation.py` — NOT invoked by the run-book
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/unit/test_integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression_inputs.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression_stability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/filtered_features.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/null_distribution_gate.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_null_distribution_gate.py` — NOT invoked by the run-book
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/null_distribution_gate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/regression_model.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/unit/test_integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression_stability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/regression_model.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/synthetic_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/synthesis/verification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/synthetic_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
