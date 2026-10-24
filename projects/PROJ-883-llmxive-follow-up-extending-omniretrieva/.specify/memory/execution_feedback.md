# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: run-book completed but produced no data/figure artifacts; 3 declared deliverable(s) absent: data/processed/baseline_overhead.json; data/processed/cost_table.json; data/processed/optimal_ground_truth.json

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/processed/baseline_overhead.json
- data/processed/cost_table.json
- data/processed/optimal_ground_truth.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_overhead.json` is declared but was NOT written. Scripts referencing it:
    - `code/baseline_overhead.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_overhead.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cost_table.json` is declared but was NOT written. Scripts referencing it:
    - `code/generators/reference_engine.py` — NOT invoked by the run-book
    - `code/planners/optimal_planner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cost_table.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/optimal_ground_truth.json` is declared but was NOT written. Scripts referencing it:
    - `code/planners/optimal_planner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/optimal_ground_truth.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
