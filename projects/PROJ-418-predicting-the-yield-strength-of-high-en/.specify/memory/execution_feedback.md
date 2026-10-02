# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.pipeline.run  --seed 42  --output-dir output/ (rc=1); 2 declared deliverable(s) absent: data/processed/hea_descriptors.csv; data/raw/heas_raw.csv

## Failing / missing run-book commands

- python -m src.pipeline.run  --seed 42  --output-dir output/ -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-418-predicting-the-yield-strength-of-high-en/code/.venv/bin/python: Error while finding module specification for 'src.pipeline.run' (ModuleNotFoundError: No module named 'src')

## Declared deliverables still missing

- data/processed/hea_descriptors.csv
- data/raw/heas_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/hea_descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/run_full_pipeline.py` — NOT invoked by the run-book
    - `code/models/evaluate.py` — NOT invoked by the run-book
    - `code/models/train.py` — NOT invoked by the run-book
    - `code/data/pipeline.py` — NOT invoked by the run-book
    - `code/data/status_writer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/hea_descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/heas_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_full_pipeline.py` — NOT invoked by the run-book
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/heas_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
