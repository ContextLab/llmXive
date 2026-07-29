# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 4 declared deliverable(s) absent: data/interim/labeled_responses.csv; data/processed/features.csv; data/raw/medmis_subset.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/interim/labeled_responses.csv
- data/processed/features.csv
- data/raw/medmis_subset.csv
- data/raw/static_medical_facts.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/labeled_responses.csv` is declared but was NOT written. Scripts referencing it:
    - `code/labeling.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/labeled_responses.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/secrets_manager.py` — NOT invoked by the run-book
    - `code/validation_gate.py` — NOT invoked by the run-book
    - `code/setup_linting.py` — NOT invoked by the run-book
    - `code/annotation.py` — NOT invoked by the run-book
    - `code/features.py` — NOT invoked by the run-book
    - `code/feature_save.py` — NOT invoked by the run-book
    - `code/validation_logic.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/medmis_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/medmis_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/static_medical_facts.json` is declared but was NOT written. Scripts referencing it:
    - `code/static_ground_truth.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/static_medical_facts.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
