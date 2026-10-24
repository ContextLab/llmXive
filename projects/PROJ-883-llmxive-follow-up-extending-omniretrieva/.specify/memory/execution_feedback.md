# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: run-book completed but produced no data/figure artifacts; 1 declared deliverable(s) absent: data/processed/generation_log.json

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/processed/generation_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/generation_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/benchmark_runner.py` — NOT invoked by the run-book
    - `code/generators/synthetic_query.py` — NOT invoked by the run-book
    - `code/query_generator.py` — NOT invoked by the run-book
    - `code/router/sut_router.py` — NOT invoked by the run-book
    - `code/transform_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/generation_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
