# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 3 declared deliverable(s) absent: data/processed/bcc_filtered.csv; data/processed/features_engineered.csv; data/raw/mpea_raw.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1

Failed to import code.data_ingestion: cannot import name 'setup_logger' from 'utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-525-predicting-the-yield-strength-of-bcc-all/code/utils/__init__.py)
Step code.data_ingestion failed with exit code 1


## Declared deliverables still missing

- data/processed/bcc_filtered.csv
- data/processed/features_engineered.csv
- data/raw/mpea_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/bcc_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_download.py` — NOT invoked by the run-book
    - `code/02_engineer.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/feature_engineering.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/bcc_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_engineered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/feature_engineering.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/traceability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_engineered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/mpea_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_download.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/mpea_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
