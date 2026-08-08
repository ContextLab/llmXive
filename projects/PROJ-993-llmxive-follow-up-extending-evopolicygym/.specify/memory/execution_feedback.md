# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode full --runs-per-condition 5 --seed 42`
  - script usage: `main.py [-h] [--run-evolution] [--run-shift-analysis] [--run-stats]`
  - argparse error: `main.py: error: unrecognized arguments: --mode full --runs-per-condition 5`
- run-book command: `python code/main.py --mode analyze`
  - script usage: `main.py [-h] [--run-evolution] [--run-shift-analysis] [--run-stats]`
  - argparse error: `main.py: error: unrecognized arguments: --mode analyze`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py --mode full --runs-per-condition 5 --seed 42 (rc=2); python code/main.py --mode analyze (rc=2); 3 declared deliverable(s) absent: data/evolution_results.csv; data/final_results.csv; data/stats_results.json

## Failing / missing run-book commands

- python code/main.py --mode full --runs-per-condition 5 --seed 42 -> rc=2
    usage: main.py [-h] [--run-evolution] [--run-shift-analysis] [--run-stats]
               [--config CONFIG] [--seeds SEEDS [SEEDS ...]] [--runs RUNS]
               [--envs ENVS [ENVS ...]] [--conditions CONDITIONS]
main.py: error: unrecognized arguments: --mode full --runs-per-condition 5
- python code/main.py --mode analyze -> rc=2
    usage: main.py [-h] [--run-evolution] [--run-shift-analysis] [--run-stats]
               [--config CONFIG] [--seeds SEEDS [SEEDS ...]] [--runs RUNS]
               [--envs ENVS [ENVS ...]] [--conditions CONDITIONS]
main.py: error: unrecognized arguments: --mode analyze

## Declared deliverables still missing

- data/evolution_results.csv
- data/final_results.csv
- data/stats_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/evolution_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/tests/test_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/evolution_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/final_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/final_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/stats_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/tests/test_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/stats_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
