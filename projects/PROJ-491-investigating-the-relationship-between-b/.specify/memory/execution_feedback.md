# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 3 declared deliverable(s) absent: data/processed/excluded_session_ids.csv; data/processed/session_validation_metrics.json; data/processed/ventral_striatum_activation.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    main__ - INFO - --- Starting Phase 2: Generate Power264 Atlas Contract ---
2026-08-29 04:54:34,030 - __main__ - ERROR - --- Phase 2: Generate Power264 Atlas Contract failed: cannot import name 'fetch_atlas_power_2011' from 'nilearn.datasets' (/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/.venv/lib/python3.11/site-packages/nilearn/datasets/__init__.py) ---
2026-08-29 04:54:34,030 - __main__ - ERROR - Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/main.py", line 35, in run_stage
    module = __import__(module_name, fromlist=['main'])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/create_atlas_power264_json.py", line 4, in <module>
    from nilearn.datasets import fetch_atlas_power_2011
ImportError: cannot import name 'fetch_atlas_power_2011' from 'nilearn.datasets' (/home/runner/work/llmXive/llmXive/projects/PROJ-491-investigating-the-relationship-between-b/code/.venv/lib/python3.11/site-packages/nilearn/datasets/__init__.py)

## Declared deliverables still missing

- data/processed/excluded_session_ids.csv
- data/processed/session_validation_metrics.json
- data/processed/ventral_striatum_activation.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/excluded_session_ids.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/session_validation_metrics.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/write_excluded_session_ids.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/excluded_session_ids.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/session_validation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/session_validation_metrics.py` — NOT invoked by the run-book
    - `code/verify_session_validation_metrics.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/session_validation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ventral_striatum_activation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_vs_activation.py` — NOT invoked by the run-book
    - `code/verify_vs_activation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ventral_striatum_activation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
