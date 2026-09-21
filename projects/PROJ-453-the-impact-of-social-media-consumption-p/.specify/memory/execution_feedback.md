# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/04_visualize.py; 2 command(s) failed: python code/02_engineer.py (rc=1); python code/03_model.py (rc=1); 1 declared deliverable(s) absent: data/processed/participants_cleaned.csv

## Failing / missing run-book commands

- python code/02_engineer.py -> rc=1
    [2026-09-21 04:42:45,470] INFO: Starting variable engineering pipeline.
[2026-09-21 04:42:45,470] ERROR: No raw CSV files found in data/raw/
- python code/03_model.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/03_model.py", line 134, in <module>
    ) -> Tuple[sm.OLSResults, Dict[str, Any]]:
               ^^^^^^^^^^^^^
AttributeError: module 'statsmodels.api' has no attribute 'OLSResults'
- python code/04_visualize.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/04_visualize.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/participants_cleaned.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/participants_cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_engineer.py` — IS a run-book command
    - `code/03_model.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/participants_cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
