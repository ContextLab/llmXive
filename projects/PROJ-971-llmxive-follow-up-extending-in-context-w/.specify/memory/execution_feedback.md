# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash -c "source scripts/quickstart.sh && ./scripts/run_minimal.sh"; 1 declared deliverable(s) absent: data/processed/task_complexity.csv

## Failing / missing run-book commands

- bash -c "source scripts/quickstart.sh && ./scripts/run_minimal.sh" -> rc=-1

shell script must be an existing project-local .sh file

## Declared deliverables still missing

- data/processed/task_complexity.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/task_complexity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/compute_complexity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/task_complexity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
