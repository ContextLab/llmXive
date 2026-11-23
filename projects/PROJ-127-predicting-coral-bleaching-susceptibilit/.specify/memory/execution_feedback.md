# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python code/main.py --simulation-mode (rc=1); 2 declared deliverable(s) absent: data/processed/independent_bleaching_events.csv; data/processed/reef_species_unified.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-127-predicting-coral-bleaching-susceptibilit/code/main.py", line 10, in <module>
    from features import main as run_feature_engineering
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-127-predicting-coral-bleaching-susceptibilit/code/features.py", line 8, in <module>
    from statsmodels.stats.outliers_influence import variance_inflation_factor
ModuleNotFoundError: No module named 'statsmodels'

- python code/main.py --simulation-mode -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-127-predicting-coral-bleaching-susceptibilit/code/main.py", line 10, in <module>
    from features import main as run_feature_engineering
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-127-predicting-coral-bleaching-susceptibilit/code/features.py", line 8, in <module>
    from statsmodels.stats.outliers_influence import variance_inflation_factor
ModuleNotFoundError: No module named 'statsmodels'


## Declared deliverables still missing

- data/processed/independent_bleaching_events.csv
- data/processed/reef_species_unified.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/independent_bleaching_events.csv` is declared but was NOT written. Scripts referencing it:
    - `code/map.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/independent_bleaching_events.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/reef_species_unified.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features.py` — NOT invoked by the run-book
    - `code/generate_schemas.py` — NOT invoked by the run-book
    - `code/ingest.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/map.py` — NOT invoked by the run-book
    - `code/train.py` — NOT invoked by the run-book
    - `code/verify_unified_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/reef_species_unified.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
