# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/download.py --subjects <N>`
  - script usage: `download.py [-h] [--subjects SUBJECTS] [--dataset-id DATASET_ID]`
  - argparse error: `download.py: error: argument --subjects: invalid int value: '<N>'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/verify_references.py --stage dataset (rc=1); python code/download.py --subjects <N> (rc=2); 2 declared deliverable(s) absent: data/raw/checksums.json; data/results/citation_verification.json

## Failing / missing run-book commands

- python code/verify_references.py --stage dataset -> rc=1

REFERENCE VERIFICATION FAILED: Invalid OpenNeuro dataset ID 'ds004510': expected the form 'ds######'.

- python code/download.py --subjects <N> -> rc=2

usage: download.py [-h] [--subjects SUBJECTS] [--dataset-id DATASET_ID]
download.py: error: argument --subjects: invalid int value: '<N>'


## Declared deliverables still missing

- data/raw/checksums.json
- data/results/citation_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/citation_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_references.py` — IS a run-book command
  Make ONE of these WRITE `data/results/citation_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
