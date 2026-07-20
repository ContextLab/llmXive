# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/runner.py --mode synthetic --phi-range 0.0 0.9 --sample-sizes 50 100 200 --trials 1000`
  - script usage: `runner.py [-h] [--full] [--phi PHI] [--n N] [--resamples RESAMPLES]`
  - argparse error: `runner.py: error: unrecognized arguments: --mode synthetic --phi-range 0.0 0.9 --sample-sizes 50 100 200`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/runner.py --mode synthetic --phi-range 0.0 0.9 --sample-sizes 50 100 200 --trials 1000 (rc=2)

## Failing / missing run-book commands

- python code/runner.py --mode synthetic --phi-range 0.0 0.9 --sample-sizes 50 100 200 --trials 1000 -> rc=2
    usage: runner.py [-h] [--full] [--phi PHI] [--n N] [--resamples RESAMPLES]
                 [--trials TRIALS] [--seed SEED] [--setup]
runner.py: error: unrecognized arguments: --mode synthetic --phi-range 0.0 0.9 --sample-sizes 50 100 200
