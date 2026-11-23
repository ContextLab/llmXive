# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.cli.run_simulation --agent ca_eco_director --steps 2000 --seed 42`
  - script usage: `run_simulation.py [-h] [--steps STEPS] [--memory-limit MEMORY_LIMIT]`
  - argparse error: `run_simulation.py: error: unrecognized arguments: --agent ca_eco_director --seed 42`
- run-book command: `python -m src.cli.run_simulation --mode sweep --steps 2000 --seed 42`
  - script usage: `run_simulation.py [-h] [--steps STEPS] [--memory-limit MEMORY_LIMIT]`
  - argparse error: `run_simulation.py: error: unrecognized arguments: --mode sweep --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.cli.run_simulation --agent ca_eco_director --steps 2000 --seed 42 (rc=2); python -m src.cli.run_simulation --mode sweep --steps 2000 --seed 42 (rc=2); python -m src.cli.validate_data --path data/raw/ (rc=1)

## Failing / missing run-book commands

- python -m src.cli.run_simulation --agent ca_eco_director --steps 2000 --seed 42 -> rc=2

usage: run_simulation.py [-h] [--steps STEPS] [--memory-limit MEMORY_LIMIT]
                         [--time-limit TIME_LIMIT] [--output OUTPUT]
run_simulation.py: error: unrecognized arguments: --agent ca_eco_director --seed 42

- python -m src.cli.run_simulation --mode sweep --steps 2000 --seed 42 -> rc=2

usage: run_simulation.py [-h] [--steps STEPS] [--memory-limit MEMORY_LIMIT]
                         [--time-limit TIME_LIMIT] [--output OUTPUT]
run_simulation.py: error: unrecognized arguments: --mode sweep --seed 42

- python -m src.cli.validate_data --path data/raw/ -> rc=1

2026-10-14 09:29:34,153 ERROR __main__: No Parquet files found under data/raw.

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
