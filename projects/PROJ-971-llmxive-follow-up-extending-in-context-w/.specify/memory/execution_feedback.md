# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash -c "source scripts/quickstart.sh && ./scripts/run_minimal.sh"; 3 declared deliverable(s) absent: data/processed/descriptors.csv; data/processed/labels.csv; data/processed/task_complexity.csv

## Failing / missing run-book commands

- bash -c "source scripts/quickstart.sh && ./scripts/run_minimal.sh" -> rc=-1

shell script must be an existing project-local .sh file

## Declared deliverables still missing

- data/processed/descriptors.csv
- data/processed/labels.csv
- data/processed/task_complexity.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/compute_complexity.py` — NOT invoked by the run-book
    - `code/src/pipeline/extract_descriptors.py` — NOT invoked by the run-book
    - `code/src/pipeline/extract_descriptors_novel.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_end_to_end.py` — NOT invoked by the run-book
    - `code/src/pipeline/train_regressor.py` — NOT invoked by the run-book
    - `code/src/pipeline/validate_autocwm.py` — NOT invoked by the run-book
    - `code/tests/test_descriptor_schema.py` — NOT invoked by the run-book
    - `src/pipeline/compute_complexity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/labels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/grid_search_labels.py` — NOT invoked by the run-book
    - `code/src/pipeline/train_regressor.py` — NOT invoked by the run-book
    - `code/src/pipeline/validate_autocwm.py` — NOT invoked by the run-book
    - `src/pipeline/grid_search_labels.py` — NOT invoked by the run-book
    - `src/pipeline/train_regressor.py` — NOT invoked by the run-book
    - `src/pipeline/validate_autocwm.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/labels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/task_complexity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/compute_complexity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/task_complexity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
