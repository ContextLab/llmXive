# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 2 declared deliverable(s) absent: data/outputs/metrics.json; data/processed/cleaned_data.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-158-investigating-the-correlation-between-mo/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-158-investigating-the-correlation-between-mo/code/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/outputs/metrics.json
- data/processed/cleaned_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/outputs/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/merge.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/models/rf.py` — NOT invoked by the run-book
    - `code/models/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/outputs/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/split.py` — NOT invoked by the run-book
    - `code/models/rf.py` — NOT invoked by the run-book
    - `code/models/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
