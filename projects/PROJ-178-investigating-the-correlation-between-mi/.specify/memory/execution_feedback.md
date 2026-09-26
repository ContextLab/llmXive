# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/run_analysis.py (rc=1); 2 declared deliverable(s) absent: data/processed/mito_aging_dataset.csv; data/validation/log_age_column.json

## Failing / missing run-book commands

- python code/run_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-178-investigating-the-correlation-between-mi/code/run_analysis.py", line 78, in <module>
    run_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-178-investigating-the-correlation-between-mi/code/run_analysis.py", line 52, in run_pipeline
    logger = setup_logging()
             ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-178-investigating-the-correlation-between-mi/code/run_analysis.py", line 11, in setup_logging
    log_dir = get_local_paths()['logs']
              ~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: 'logs'

## Declared deliverables still missing

- data/processed/mito_aging_dataset.csv
- data/validation/log_age_column.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/mito_aging_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config/environment.py` — NOT invoked by the run-book
    - `code/tests/test_data.py` — NOT invoked by the run-book
    - `code/tests/test_sensitivity.py` — NOT invoked by the run-book
    - `code/tests/test_environment.py` — NOT invoked by the run-book
    - `code/analysis/exclusion_logic.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/clean_dataset.py` — NOT invoked by the run-book
    - `code/analysis/model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mito_aging_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/log_age_column.json` is declared but was NOT written. Scripts referencing it:
    - `code/config/environment.py` — NOT invoked by the run-book
    - `code/analysis/load_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/log_age_column.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
