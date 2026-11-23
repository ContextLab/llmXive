# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --step ingest`
  - script usage: `main.py [-h] --action {download,run,metrics,scan-pii}`
  - argparse error: `main.py: error: the following arguments are required: --action`
- run-book command: `python code/main.py --step preprocess`
  - script usage: `main.py [-h] --action {download,run,metrics,scan-pii}`
  - argparse error: `main.py: error: the following arguments are required: --action`
- run-book command: `python code/main.py --step checks   # runs T010, T020, T021, T022 sequentially`
  - script usage: `main.py [-h] --action {download,run,metrics,scan-pii}`
  - argparse error: `main.py: error: the following arguments are required: --action`
- run-book command: `python code/main.py --step model`
  - script usage: `main.py [-h] --action {download,run,metrics,scan-pii}`
  - argparse error: `main.py: error: the following arguments are required: --action`
- run-book command: `python code/main.py --step report`
  - script usage: `main.py [-h] --action {download,run,metrics,scan-pii}`
  - argparse error: `main.py: error: the following arguments are required: --action`
- run-book command: `python code/main.py --run-all`
  - script usage: `main.py [-h] --action {download,run,metrics,scan-pii}`
  - argparse error: `main.py: error: the following arguments are required: --action`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/main.py --step ingest (rc=2); python code/main.py --step preprocess (rc=2); python code/main.py --step checks   # runs T010, T020, T021, T022 sequentially (rc=2); 1 declared deliverable(s) absent: data/processed/linked_trials.csv

## Failing / missing run-book commands

- python code/main.py --step ingest -> rc=2

usage: main.py [-h] --action {download,run,metrics,scan-pii}
main.py: error: the following arguments are required: --action

- python code/main.py --step preprocess -> rc=2

usage: main.py [-h] --action {download,run,metrics,scan-pii}
main.py: error: the following arguments are required: --action

- python code/main.py --step checks   # runs T010, T020, T021, T022 sequentially -> rc=2

usage: main.py [-h] --action {download,run,metrics,scan-pii}
main.py: error: the following arguments are required: --action

- python code/main.py --step model -> rc=2

usage: main.py [-h] --action {download,run,metrics,scan-pii}
main.py: error: the following arguments are required: --action

- python code/main.py --step report -> rc=2

usage: main.py [-h] --action {download,run,metrics,scan-pii}
main.py: error: the following arguments are required: --action

- python code/main.py --run-all -> rc=2

usage: main.py [-h] --action {download,run,metrics,scan-pii}
main.py: error: the following arguments are required: --action


## Declared deliverables still missing

- data/processed/linked_trials.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/linked_trials.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/calculate_ingest_metrics.py` — NOT invoked by the run-book
    - `code/data/chunked_processor.py` — NOT invoked by the run-book
    - `code/data/cleanup.py` — NOT invoked by the run-book
    - `code/data/generate_linked_trials.py` — NOT invoked by the run-book
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/linkage.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/linked_trials.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
