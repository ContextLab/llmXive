# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/utils/validate.py --check-all; 2 command(s) failed: python -m pytest -q (rc=2); python code/main.py  --N-values 3,5  --noise-levels 0.0001,0.001,0.01,0.1  --trials 30  --window-sizes 500,1000,5000  --seed 42 (rc=1); 1 declared deliverable(s) absent: data/processed/results.json

## Failing / missing run-book commands

- python -m pytest -q -> rc=2
ake sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_sweep_runner.py:14: in <module>
    from analysis.sweep_runner import run_full_sweep, save_sweep_results, WINDOW_SIZES
code/analysis/__init__.py:24: in <module>
    from .ftle import (
code/analysis/ftle.py:22: in <module>
    from data.loader import load_trajectory
E   ModuleNotFoundError: No module named 'data.loader'
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
ERROR tests/unit/test_boundedness.py
ERROR tests/unit/test_ftle.py
ERROR tests/unit/test_per_window_baseline.py
ERROR tests/unit/test_refactor_utils.py - NameError: name 'Path' is not defined
ERROR tests/unit/test_refactored_ftle.py
ERROR tests/unit/test_regression.py
ERROR tests/unit/test_shadowing.py
ERROR tests/unit/test_sweep_runner.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 0.97s ===============================


- python code/main.py  --N-values 3,5  --noise-levels 0.0001,0.001,0.01,0.1  --trials 30  --window-sizes 500,1000,5000  --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/code/main.py", line 10, in <module>
    from data.generator import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/code/data/__init__.py", line 9, in <module>
    from .generator import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/code/data/generator.py", line 18, in <module>
    from ..config import NumericalSettings, SimulationConfig, AnalysisConfig, get_full_config
ImportError: attempted relative import beyond top-level package

- python code/utils/validate.py --check-all -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-101-quantifying-the-influence-of-initial-con/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/code/utils/validate.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/baseline.py` — NOT invoked by the run-book
    - `code/analysis/boundedness.py` — NOT invoked by the run-book
    - `code/analysis/ftle.py` — NOT invoked by the run-book
    - `code/analysis/refactored_ftle.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/shadowing.py` — NOT invoked by the run-book
    - `code/analysis/sweep_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
