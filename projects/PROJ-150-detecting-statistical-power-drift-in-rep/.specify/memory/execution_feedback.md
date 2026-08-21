# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/models.py; 5 command(s) failed: python code/preprocess.py --download-only (rc=1); python code/main.py (rc=1); python code/preprocess.py (rc=1); 3 declared deliverable(s) absent: data/derived/cleaned_data.csv; data/derived/grouping_validation.json; data/raw/data.csv

## Failing / missing run-book commands

- python code/preprocess.py --download-only -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/preprocess.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/main.py -> rc=1
    ERROR: huggingface_hub is not installed. Please run: pip install huggingface_hub
- python code/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/preprocess.py", line 5, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/models.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/models.py': [Errno 2] No such file or directory
- python code/robustness.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/robustness.py", line 7, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/visualize.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/visualize.py", line 7, in <module>
    import matplotlib.pyplot as plt
ModuleNotFoundError: No module named 'matplotlib'

## Declared deliverables still missing

- data/derived/cleaned_data.csv
- data/derived/grouping_validation.json
- data/raw/data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/visualize.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/robustness.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/grouping_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/grouping_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/update_state.py` — NOT invoked by the run-book
    - `code/run_subset_pipeline.py` — NOT invoked by the run-book
    - `code/validate_source.py` — NOT invoked by the run-book
    - `code/compute_trends.py` — NOT invoked by the run-book
    - `code/visualize.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/timing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
