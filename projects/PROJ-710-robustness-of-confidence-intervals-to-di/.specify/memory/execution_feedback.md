# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/data/synthetic_pop.py; 3 command(s) failed: python code/main.py (rc=1); python code/analysis/convergence_check.py (rc=1); python -m pytest code/tests/ (rc=2)

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/main.py", line 16, in <module>
    from data.download_utils import load_real_dataset, DataFetchError
ModuleNotFoundError: No module named 'data.download_utils'

- python code/data/synthetic_pop.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-710-robustness-of-confidence-intervals-to-di/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/data/synthetic_pop.py': [Errno 2] No such file or directory

- python code/analysis/convergence_check.py -> rc=1
2026-10-15 23:27:35,798 - INFO - Starting convergence check analysis.
2026-10-15 23:27:35,798 - ERROR - Results file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-710-robustness-of-confidence-intervals-to-di/artifacts/coverage_results.csv. Did you run the main simulation (T013a/T042)?


- python -m pytest code/tests/ -> rc=2
i' has no attribute 'GLMResultsWrapper'
________________ ERROR collecting code/tests/test_validation.py ________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/tests/test_validation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/test_validation.py:6: in <module>
    from code.analysis.validation import (
code/analysis/validation.py:6: in <module>
    import torch
E   ModuleNotFoundError: No module named 'torch'
=========================== short test summary info ============================
ERROR code/tests/test_ci_builder.py
ERROR code/tests/test_coverage_pipeline.py
ERROR code/tests/test_dp_noise.py
ERROR code/tests/test_glm_analysis.py - AttributeError: module 'statsmodels.a...
ERROR code/tests/test_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 1.02s ===============================


