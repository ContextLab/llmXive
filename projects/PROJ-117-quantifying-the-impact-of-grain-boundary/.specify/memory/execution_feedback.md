# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/diagnostics.py (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_dataset.parquet; data/processed/parsed_geometry.parquet

## Failing / missing run-book commands

- python code/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/download.py", line 12, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/preprocess.py", line 21, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/diagnostics.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/diagnostics.py", line 11, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/train.py", line 8, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/validate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/validate.py", line 14, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/interpret.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/interpret.py", line 16, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/processed/cleaned_dataset.parquet
- data/processed/parsed_geometry.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/interpret.py` — IS a run-book command
    - `code/train.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/parsed_geometry.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/parsed_geometry.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
