# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python -m pytest tests/test_physics.py -v (rc=2); 4 declared deliverable(s) absent: data/processed/derived_physics.csv; data/processed/merged_filtered.csv; data/results/correlation_results.json

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-501-investigating-the-relationship-between-s/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-501-investigating-the-relationship-between-s/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/test_physics.py -v -> rc=2
-s
plugins: platformdirs-4.13.0
collecting ... collected 0 items / 1 error

==================================== ERRORS ====================================
____________________ ERROR collecting tests/test_physics.py ____________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-501-investigating-the-relationship-between-s/tests/test_physics.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_physics.py:18: in <module>
    from code.config import G, EFFICIENCY, K_TIDE, M_ATM_INITIAL_BASELINE
E   ImportError: cannot import name 'EFFICIENCY' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-501-investigating-the-relationship-between-s/code/config.py)
=========================== short test summary info ============================
ERROR tests/test_physics.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.24s ===============================



## Declared deliverables still missing

- data/processed/derived_physics.csv
- data/processed/merged_filtered.csv
- data/results/correlation_results.json
- data/results/flux_vs_retention.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/derived_physics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/integration_test_runner.py` — NOT invoked by the run-book
    - `code/physics.py` — NOT invoked by the run-book
    - `code/physics_pipeline_runner.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/derived_physics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/integration_test_runner.py` — NOT invoked by the run-book
    - `code/physics.py` — NOT invoked by the run-book
    - `code/physics_pipeline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/integration_test_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/flux_vs_retention.png` is declared but was NOT written. Scripts referencing it:
    - `code/integration_test_runner.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/flux_vs_retention.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
