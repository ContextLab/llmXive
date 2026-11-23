# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py --mode preprocess (rc=1); python code/main.py --mode train (rc=1); python -m pytest tests/ -v (rc=1); 3 declared deliverable(s) absent: data/derived/cohort_entropy_medians.csv; data/derived/connectivity_features_baseline.csv; data/processed/subject_entropy_features.csv

## Failing / missing run-book commands

- python code/main.py --mode preprocess -> rc=1

2026-10-10 00:50:15,015 [INFO] Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: In FT2Font: Can not load face (unknown file format; error code 0x2)
2026-10-10 00:50:15,039 [INFO] generated new fontManager
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-709-evaluating-resting-state-fmri-entropy-as/code/main.py", line 25, in <module>
    from config import (
ImportError: cannot import name 'TARGET_LENGTH' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-709-evaluating-resting-state-fmri-entropy-as/code/config.py)

- python code/main.py --mode train -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-709-evaluating-resting-state-fmri-entropy-as/code/main.py", line 25, in <module>
    from config import (
ImportError: cannot import name 'TARGET_LENGTH' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-709-evaluating-resting-state-fmri-entropy-as/code/config.py)

- python -m pytest tests/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-709-evaluating-resting-state-fmri-entropy-as/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/derived/cohort_entropy_medians.csv
- data/derived/connectivity_features_baseline.csv
- data/processed/subject_entropy_features.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/cohort_entropy_medians.csv` is declared but was NOT written. Scripts referencing it:
    - `code/entropy_engine.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/cohort_entropy_medians.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/connectivity_features_baseline.csv` is declared but was NOT written. Scripts referencing it:
    - `code/connectivity_engine.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/connectivity_features_baseline.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/subject_entropy_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/entropy_engine.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/validate_entropy.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/verify_output.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/subject_entropy_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
