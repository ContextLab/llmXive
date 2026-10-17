# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.main --thin`
  - script usage: `main.py [-h] [--max-samples MAX_SAMPLES]`
  - argparse error: `main.py: error: unrecognized arguments: --thin`
- run-book command: `python code/main.py  --max-samples 2000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01  --seed 42`
  - script usage: `main.py [-h] [--max-samples MAX_SAMPLES]`
  - argparse error: `main.py: error: unrecognized arguments: --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.main --thin (rc=2); python code/main.py  --max-samples 2000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01  --seed 42 (rc=2)

## Failing / missing run-book commands

- python -m code.main --thin -> rc=2

usage: main.py [-h] [--max-samples MAX_SAMPLES]
               [--mc-dropout-passes MC_DROPOUT_PASSES]
               [--ensemble-size ENSEMBLE_SIZE]
               [--coverage-sweep-start COVERAGE_SWEEP_START]
               [--coverage-sweep-stop COVERAGE_SWEEP_STOP]
               [--coverage-sweep-step COVERAGE_SWEEP_STEP]
main.py: error: unrecognized arguments: --thin

- python code/main.py  --max-samples 2000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01  --seed 42 -> rc=2

usage: main.py [-h] [--max-samples MAX_SAMPLES]
               [--mc-dropout-passes MC_DROPOUT_PASSES]
               [--ensemble-size ENSEMBLE_SIZE]
               [--coverage-sweep-start COVERAGE_SWEEP_START]
               [--coverage-sweep-stop COVERAGE_SWEEP_STOP]
               [--coverage-sweep-step COVERAGE_SWEEP_STEP]
main.py: error: unrecognized arguments: --seed 42

