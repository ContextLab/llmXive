# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 4 declared deliverable(s) absent: data/processed/autocorrelation_raw.csv; data/processed/demo_autocorr.csv; data/processed/pipeline_status.json

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/main.py", line 35, in <module>
    from null_distribution import main as null_dist_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/null_distribution.py", line 39, in <module>
    from permutation import (
ImportError: cannot import name '_load_window_starts' from 'permutation' (/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/permutation.py)


## Declared deliverables still missing

- data/processed/autocorrelation_raw.csv
- data/processed/demo_autocorr.csv
- data/processed/pipeline_status.json
- data/processed/window_index.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/autocorrelation_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/autocorrelation.py` — NOT invoked by the run-book
    - `code/cross_validate_autocorrelation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/autocorrelation_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/demo_autocorr.csv` is declared but was NOT written. Scripts referencing it:
    - `code/autocorrelation.py` — NOT invoked by the run-book
    - `code/demo_autocorr.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/demo_autocorr.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pipeline_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/cross_validate_autocorrelation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pipeline_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/window_index.csv` is declared but was NOT written. Scripts referencing it:
    - `code/autocorrelation.py` — NOT invoked by the run-book
    - `code/permutation.py` — NOT invoked by the run-book
    - `code/window_index.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/window_index.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
