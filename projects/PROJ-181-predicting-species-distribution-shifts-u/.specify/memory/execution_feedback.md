# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py download`
  - script usage: `main.py [-h] [--species-list SPECIES_LIST] [--year-range YEAR_RANGE]`
  - argparse error: `main.py: error: unrecognized arguments: download`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/main.py download (rc=2); python code/main.py preprocess (rc=1); python code/main.py train (rc=1)

## Failing / missing run-book commands

- python code/main.py download -> rc=2

usage: main.py [-h] [--species-list SPECIES_LIST] [--year-range YEAR_RANGE]
               [--target {historical,recent}]
               [--climate {historical,recent,future}] [--scenario SCENARIO]
               [--year YEAR]
main.py: error: unrecognized arguments: download

- python code/main.py preprocess -> rc=1
2026-10-23 12:37:00,032 - __main__ - ERROR - preprocess command not implemented yet.

2026-10-23 12:37:00,032 ERROR __main__: preprocess command not implemented yet.
preprocess command not implemented yet.

- python code/main.py train -> rc=1
2026-10-23 12:37:00,215 - __main__ - ERROR - train command not implemented yet.

2026-10-23 12:37:00,215 ERROR __main__: train command not implemented yet.
train command not implemented yet.

- python code/main.py evaluate -> rc=1
2026-10-23 12:37:00,392 - __main__ - ERROR - evaluate command not implemented yet.

2026-10-23 12:37:00,392 ERROR __main__: evaluate command not implemented yet.
evaluate command not implemented yet.

- python code/main.py report -> rc=1
2026-10-23 12:37:00,572 - __main__ - ERROR - report command not implemented yet.

2026-10-23 12:37:00,572 ERROR __main__: report command not implemented yet.
report command not implemented yet.

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
