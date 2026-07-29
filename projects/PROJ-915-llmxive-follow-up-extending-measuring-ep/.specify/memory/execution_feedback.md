# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 2 declared deliverable(s) absent: data/processed/features.csv; data/raw/medmis_subset.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    The 'biopython' package is required. Install with: pip install biopython
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/main.py", line 12, in <module>
    from static_ground_truth import run_static_ground_truth_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/static_ground_truth.py", line 17, in <module>
    from Bio import Entrez
ModuleNotFoundError: No module named 'Bio'

## Declared deliverables still missing

- data/processed/features.csv
- data/raw/medmis_subset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/labeling.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/features.py` — NOT invoked by the run-book
    - `code/feature_save.py` — NOT invoked by the run-book
    - `code/validation_logic.py` — NOT invoked by the run-book
    - `code/data_models.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/medmis_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/static_ground_truth.py` — NOT invoked by the run-book
    - `code/labeling.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/features.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/medmis_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
