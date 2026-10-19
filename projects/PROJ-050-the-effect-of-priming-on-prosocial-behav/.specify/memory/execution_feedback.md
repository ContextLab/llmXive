# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/03_validate.py; python code/04_analyze.py; 5 command(s) failed: python -m pipeline.run (rc=1); python code/00_check_dataset.py   # prints missing fields, exits if title missing (rc=1); python code/01_ingest.py (rc=1); 1 declared deliverable(s) absent: data/processed/anonymized.csv

## Failing / missing run-book commands

- python -m pipeline.run -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: Error while finding module specification for 'pipeline.run' (ModuleNotFoundError: No module named 'pipeline')

- python code/00_check_dataset.py   # prints missing fields, exits if title missing -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/00_check_dataset.py", line 28, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/01_ingest.py -> rc=1
2026-10-19 14:39:22 - ingest_feasibility - INFO - === Starting T015b: Feasibility Check for FR-002c ===
2026-10-19 14:39:22 - ingest_feasibility - ERROR - Feasibility check failed: get_logger() missing 1 required positional argument: 'name'


- python code/02_score.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/02_score.py", line 261, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/02_score.py", line 235, in main
    log_abort_condition(f"Input file not found: {input_path}")
TypeError: log_abort_condition() missing 2 required positional arguments: 'reason' and 'condition_name'

- python code/03_validate.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/03_validate.py': [Errno 2] No such file or directory

- python code/04_analyze.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-050-the-effect-of-priming-on-prosocial-behav/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/04_analyze.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
RS
E   ImportError: cannot import name 'REQUIRED_DIRS' from 'code.utils.directory_setup' (/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code/utils/directory_setup.py)
______________ ERROR collecting tests/unit/test_power_analysis.py ______________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/tests/unit/test_power_analysis.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_power_analysis.py:18: in <module>
    import code._00_power_analysis as power_module
E   ModuleNotFoundError: No module named 'code._00_power_analysis'
=========================== short test summary info ============================
ERROR tests/unit/test_directory_setup.py
ERROR tests/unit/test_power_analysis.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.65s ===============================



## Declared deliverables still missing

- data/processed/anonymized.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/anonymized.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest.py` — IS a run-book command
    - `code/02_score.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/anonymized.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
