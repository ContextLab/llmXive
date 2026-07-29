# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/data/download.py; python code/data/clean.py --check-only; 1 command(s) failed: python code/main.py (rc=1); 1 declared deliverable(s) absent: data/processed/filtered_alloys.csv

## Failing / missing run-book commands

- python code/data/download.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/data/download.py': [Errno 2] No such file or directory
- python code/data/clean.py --check-only -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/data/clean.py': [Errno 2] No such file or directory
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/main.py", line 12, in <module>
    from data_cleaning import run_cleaning_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/data_cleaning.py", line 8, in <module>
    from compositional import compositions
ImportError: cannot import name 'compositions' from 'compositional' (/home/runner/work/llmXive/llmXive/projects/PROJ-420-predicting-the-effect-of-alloying-on-the/code/.venv/lib/python3.11/site-packages/compositional/__init__.py)

## Declared deliverables still missing

- data/processed/filtered_alloys.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/data_cleaning.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
