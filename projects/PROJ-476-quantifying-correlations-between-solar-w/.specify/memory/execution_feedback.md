# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m code.main --stage all (rc=1); 1 declared deliverable(s) absent: data/processed/synced.csv

## Failing / missing run-book commands

- python -m code.main --stage all -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 21, in <module>
    from code.data.fetch import fetch_ace, fetch_noaa
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch.py", line 25, in <module>
    from code.config import (
ImportError: cannot import name 'MAX_MEMORY_GB' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/config.py)


## Declared deliverables still missing

- data/processed/synced.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/synced.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/significance.py` — NOT invoked by the run-book
    - `code/analysis/thresholds.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/align.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/synced.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
