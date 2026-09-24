# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python main.py --mode full --timeout [configured duration]`
  - script usage: `main.py [-h] [--mode {full,data,inference,train,analysis}]`
  - argparse error: `main.py: error: argument --timeout: invalid int value: '[configured'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python main.py --mode full --timeout [configured duration] (rc=2); 2 declared deliverable(s) absent: data/context_splits.json; data/teacher_distribution.json

## Failing / missing run-book commands

- python main.py --mode full --timeout [configured duration] -> rc=2
    usage: main.py [-h] [--mode {full,data,inference,train,analysis}]
               [--timeout TIMEOUT]
main.py: error: argument --timeout: invalid int value: '[configured'

## Declared deliverables still missing

- data/context_splits.json
- data/teacher_distribution.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/context_splits.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_artifacts.py` — NOT invoked by the run-book
    - `code/data/test_context_sim.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/models/inference_only.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/context_splits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/teacher_distribution.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_artifacts.py` — NOT invoked by the run-book
    - `code/models/inference_only.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/teacher_distribution.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
