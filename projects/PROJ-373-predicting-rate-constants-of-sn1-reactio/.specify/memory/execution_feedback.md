# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/main.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_sn1.csv; data/processed/exclusion_report.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/main.py", line 39, in <module>
    from data.ingest import main as ingest_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/__init__.py", line 6, in <module>
    from .finalize_dataset import load_split_datasets, save_final_dataset, save_checksum, main
ImportError: cannot import name 'load_split_datasets' from 'data.finalize_dataset' (/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/finalize_dataset.py)

## Declared deliverables still missing

- data/processed/cleaned_sn1.csv
- data/processed/exclusion_report.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_sn1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/final_validation.py` — NOT invoked by the run-book
    - `code/models/evaluate.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_runner.py` — NOT invoked by the run-book
    - `code/analysis/collinearity.py` — NOT invoked by the run-book
    - `code/analysis/consistency.py` — NOT invoked by the run-book
    - `code/analysis/hyperparameter_sensitivity.py` — NOT invoked by the run-book
    - `code/data/clean.py` — NOT invoked by the run-book
    - `code/data/split.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_sn1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/final_validation.py` — NOT invoked by the run-book
    - `code/data/__init__.py` — NOT invoked by the run-book
    - `code/data/clean.py` — NOT invoked by the run-book
    - `code/data/exclusion_report.py` — NOT invoked by the run-book
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/finalize_dataset.py` — NOT invoked by the run-book
    - `code/validation/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
