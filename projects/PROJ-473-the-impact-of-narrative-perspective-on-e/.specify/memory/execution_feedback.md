# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --config code/config.py (rc=1); python code/main.py --step extraction (rc=1); python code/main.py --step analysis (rc=1); 3 declared deliverable(s) absent: data/processed/aligned_dataset.csv; data/processed/perspective_features.json; data/processed/reader_response.csv

## Failing / missing run-book commands

- python code/main.py --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 15, in <module>
    from analysis import run_analysis_pipeline
ModuleNotFoundError: No module named 'analysis'
- python code/main.py --step extraction -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 15, in <module>
    from analysis import run_analysis_pipeline
ModuleNotFoundError: No module named 'analysis'
- python code/main.py --step analysis -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/main.py", line 15, in <module>
    from analysis import run_analysis_pipeline
ModuleNotFoundError: No module named 'analysis'
- python -m pytest tests/contract/ -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-473-the-impact-of-narrative-perspective-on-e/code/.venv/bin/python: No module named pytest

## Declared deliverables still missing

- data/processed/aligned_dataset.csv
- data/processed/perspective_features.json
- data/processed/reader_response.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_collection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/perspective_features.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/extraction.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_collection.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/matching.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perspective_features.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/reader_response.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_collection.py` — NOT invoked by the run-book
    - `code/data_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/reader_response.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
