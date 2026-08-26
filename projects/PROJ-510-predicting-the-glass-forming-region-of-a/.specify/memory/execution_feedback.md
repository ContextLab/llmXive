# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/ingestion.py (rc=1); python code/features.py (rc=1); python code/train.py (rc=1); 1 declared deliverable(s) absent: data/processed/processed_alloys.csv

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py", line 5, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 6, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analyze.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py", line 9, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/processed/processed_alloys.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/processed_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — IS a run-book command
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/processed_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
