# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python main.py; 4 command(s) failed: python code/data/download.py (rc=1); python code/data/descriptors.py (rc=1); python code/models/train.py (rc=1); 2 declared deliverable(s) absent: data/processed/features.csv; data/processed/hypothetical_library.csv

## Failing / missing run-book commands

- python main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/main.py': [Errno 2] No such file or directory
- python code/data/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/data/download.py", line 14, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/data/descriptors.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/data/descriptors.py", line 4, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/models/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/models/train.py", line 9, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/models/predict.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/models/predict.py", line 7, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/processed/features.csv
- data/processed/hypothetical_library.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validate.py` — NOT invoked by the run-book
    - `code/viz/plot.py` — NOT invoked by the run-book
    - `code/models/screening_full.py` — NOT invoked by the run-book
    - `code/models/predict.py` — IS a run-book command
    - `code/models/model_utils.py` — NOT invoked by the run-book
    - `code/models/train.py` — IS a run-book command
    - `code/data/verify_nulls.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/hypothetical_library.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/screening_full.py` — NOT invoked by the run-book
    - `code/models/predict.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/hypothetical_library.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
