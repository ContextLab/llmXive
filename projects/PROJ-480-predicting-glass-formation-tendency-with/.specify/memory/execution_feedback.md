# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/data/validation.py; python src/cli/run_pipeline.py; 2 command(s) failed: python src/data/download.py (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python src/data/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-480-predicting-glass-formation-tendency-with/src/data/download.py", line 21, in <module>
    from src.lib.constants import DATA_RAW_DIR, PROJECT_ID
ModuleNotFoundError: No module named 'src.lib.constants'

- python src/data/validation.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-480-predicting-glass-formation-tendency-with/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-480-predicting-glass-formation-tendency-with/src/data/validation.py': [Errno 2] No such file or directory

- python src/cli/run_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-480-predicting-glass-formation-tendency-with/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-480-predicting-glass-formation-tendency-with/src/cli/run_pipeline.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
le
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_exceptions.py:5: in <module>
    from src.lib.exceptions import (
E   ModuleNotFoundError: No module named 'src.lib.exceptions'
__________________ ERROR collecting tests/unit/test_utils.py ___________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-480-predicting-glass-formation-tendency-with/tests/unit/test_utils.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_utils.py:10: in <module>
    from src.lib.utils import calculate_sha256, get_logger
E   ModuleNotFoundError: No module named 'src.lib.utils'
=========================== short test summary info ============================
ERROR tests/unit/test_descriptors.py
ERROR tests/unit/test_exceptions.py
ERROR tests/unit/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 0.50s ===============================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
