# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 3 declared deliverable(s) absent: data/processed/excluded_session_ids.csv; data/processed/session_validation_metrics.json; data/processed/ventral_striatum_activation.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/excluded_session_ids.csv
- data/processed/session_validation_metrics.json
- data/processed/ventral_striatum_activation.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/excluded_session_ids.csv` is declared but was NOT written. Scripts referencing it:
    - `code/session_validation_metrics.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/write_excluded_session_ids.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/excluded_session_ids.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/session_validation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/session_validation_metrics.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/write_excluded_session_ids.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/session_validation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ventral_striatum_activation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_vs_activation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ventral_striatum_activation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
