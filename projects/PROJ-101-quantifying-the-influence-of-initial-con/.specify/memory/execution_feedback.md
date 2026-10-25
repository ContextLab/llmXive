# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m pytest -q (rc=2); python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 (rc=1); python -m code.utils.validate --check-all (rc=1); 1 declared deliverable(s) absent: data/processed/results.json

## Failing / missing run-book commands

- python -m pytest -q -> rc=2
runner.py:14: in <module>
    from analysis.sweep_runner import run_full_sweep, save_sweep_results, WINDOW_SIZES
code/analysis/__init__.py:37: in <module>
    from .regression import (
code/analysis/regression.py:183: in <module>
    def select_best_model(deviations_df: pd.DataFrame) -> Dict[str, Any]:
E   NameError: name 'pd' is not defined
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
ERROR tests/unit/test_ftle.py - NameError: name 'pd' is not defined
ERROR tests/unit/test_generator_t046.py
ERROR tests/unit/test_per_window_baseline.py - NameError: name 'pd' is not de...
ERROR tests/unit/test_refactor_utils.py - NameError: name 'Path' is not defined
ERROR tests/unit/test_refactored_ftle.py - NameError: name 'pd' is not defined
ERROR tests/unit/test_regression.py - NameError: name 'pd' is not defined
ERROR tests/unit/test_shadowing.py - NameError: name 'pd' is not defined
ERROR tests/unit/test_sweep_runner.py - NameError: name 'pd' is not defined
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 0.35s ===============================


- python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/code/main.py", line 10, in <module>
    from data.generator import (
ImportError: cannot import name 'generate_coupled_lorenz_trajectory' from 'data.generator' (/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/data/generator.py)

- python -m code.utils.validate --check-all -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-101-quantifying-the-influence-of-initial-con/bin/python: No module named code.utils.validate


## Declared deliverables still missing

- data/processed/results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/baseline.py` — NOT invoked by the run-book
    - `code/analysis/boundedness.py` — NOT invoked by the run-book
    - `code/analysis/ftle.py` — NOT invoked by the run-book
    - `code/analysis/per_window_baseline.py` — NOT invoked by the run-book
    - `code/analysis/refactored_ftle.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/shadowing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
