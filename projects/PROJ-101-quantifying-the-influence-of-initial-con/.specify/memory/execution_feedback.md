# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m pytest -q (rc=2); python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 (rc=1); python -m code.utils.validate --check-all (rc=1)

## Failing / missing run-book commands

- python -m pytest -q -> rc=2
/tests/unit/test_sweep_runner.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_sweep_runner.py:14: in <module>
    from analysis.sweep_runner import run_full_sweep, save_sweep_results, WINDOW_SIZES
code/analysis/__init__.py:13: in <module>
    from ..config import get_full_config  # noqa: F401
E   ImportError: attempted relative import beyond top-level package
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
ERROR tests/unit/test_boundedness.py
ERROR tests/unit/test_edge_cases.py
ERROR tests/unit/test_ftle.py
ERROR tests/unit/test_generator_t046.py
ERROR tests/unit/test_per_window_baseline.py
ERROR tests/unit/test_refactored_ftle.py
ERROR tests/unit/test_regression.py
ERROR tests/unit/test_shadowing.py
ERROR tests/unit/test_sweep_runner.py
!!!!!!!!!!!!!!!!!!! Interrupted: 10 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 10 errors in 0.43s ==============================


- python -m code.main  --N-values 3,5,7  --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0  --trials 30  --window-sizes 500,1000,5000  --seed 42 -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/code/main.py", line 10, in <module>
    from data.generator import (
ImportError: cannot import name 'generate_coupled_lorenz_trajectory' from 'data.generator' (/home/runner/work/llmXive/llmXive/projects/PROJ-101-quantifying-the-influence-of-initial-con/data/generator.py)

- python -m code.utils.validate --check-all -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-101-quantifying-the-influence-of-initial-con/bin/python: No module named code.utils.validate

