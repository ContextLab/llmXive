# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m pytest tests/test_fetcher.py -v (rc=2); python -m pytest tests/test_integration_fetch.py -v (rc=2); 3 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/graph_metrics.csv; data/processed/performance_metrics.csv

## Failing / missing run-book commands

- python -m pytest tests/test_fetcher.py -v -> rc=2
env/py311-6f1866971868/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/test_fetcher.py:16: in <module>
    from fetcher import process_historical_data
E   ImportError: cannot import name 'process_historical_data' from 'fetcher' (/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/fetcher.py)
=========================== short test summary info ============================
ERROR tests/test_fetcher.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.47s ===============================


- python -m pytest tests/test_integration_fetch.py -v -> rc=2
/py311-6f1866971868/_pytest/pathlib.py:591: in import_path
    importlib.import_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/test_integration_fetch.py:29: in <module>
    from code.fetcher import (
E   ImportError: cannot import name 'fetch_all_backends' from 'code.fetcher' (/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/fetcher.py)
=========================== short test summary info ============================
ERROR tests/test_integration_fetch.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.52s ===============================



## Declared deliverables still missing

- data/processed/correlation_results.csv
- data/processed/graph_metrics.csv
- data/processed/performance_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/generate_mdes_report_section.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graph_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/generate_graph_metrics_csv.py` — NOT invoked by the run-book
    - `code/graph_builder.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/validate_graph_metrics_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graph_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/fetcher.py` — NOT invoked by the run-book
    - `code/generate_calibration_csv.py` — NOT invoked by the run-book
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/validate_performance_metrics_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
