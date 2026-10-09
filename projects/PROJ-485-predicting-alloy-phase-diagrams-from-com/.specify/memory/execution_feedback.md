# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 1 declared deliverable(s) absent: data/provenance.json

## Failing / missing run-book commands

- python code/main.py -> rc=1

2026-10-09 19:22:53,409 - features.seed_elemental_properties - INFO - Setting up data directories...
2026-10-09 19:22:53,409 - features.seed_elemental_properties - INFO - Starting step: provenance
2026-10-09 19:22:53,410 - features.seed_elemental_properties - ERROR - Step provenance failed: run_provenance() missing 1 required positional argument: 'state_file'


## Declared deliverables still missing

- data/provenance.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/provenance.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/provenance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/provenance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
