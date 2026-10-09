# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/download.py (rc=1); python code/filter.py (rc=1); python code/fingerprints.py (rc=1); 2 declared deliverable(s) absent: data/processed/kfold_split_indices.json; data/processed/organophosphates_filtered.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/download.py", line 8, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/.venv/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/.venv/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/filter.py -> rc=1

2026-10-09 14:18:42 - __main__ - INFO - Loading compounds from data/raw/tox21_raw.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/filter.py", line 157, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/filter.py", line 137, in main
    df = load_compounds(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/filter.py", line 24, in load_compounds
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/raw/tox21_raw.csv

- python code/fingerprints.py -> rc=1

2026-10-09 14:18:42 - __main__ - ERROR - Input file not found: data/processed/organophosphates_filtered.csv
2026-10-09 14:18:42 - __main__ - ERROR - Please run code/filter.py first to generate the filtered dataset.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/fingerprints.py", line 205, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/fingerprints.py", line 200, in main
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/processed/organophosphates_filtered.csv

- python code/train.py -> rc=1

2026-10-09 14:18:44 - root - INFO - Starting K-Fold Cross-Validation Training (T019)
2026-10-09 14:18:44 - root - ERROR - Split indices file not found. Cannot proceed with training.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 240, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 188, in main
    raise FileNotFoundError(f"Split file not found: {split_file}")
FileNotFoundError: Split file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/data/processed/split_indices.json

- python -m pytest tests/ -> rc=2
,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
__________________ ERROR collecting tests/unit/test_split.py ___________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/tests/unit/test_split.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_split.py:11: in <module>
    from split import greedy_maximal_dissimilarity_split, save_splits
E   ImportError: cannot import name 'save_splits' from 'split' (/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/split.py)
=========================== short test summary info ============================
ERROR tests/integration/test_download.py
ERROR tests/unit/test_split.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.47s ===============================



## Declared deliverables still missing

- data/processed/kfold_split_indices.json
- data/processed/organophosphates_filtered.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/kfold_split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/split.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/kfold_split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/organophosphates_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter.py` — IS a run-book command
    - `code/fingerprints.py` — IS a run-book command
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/organophosphates_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
