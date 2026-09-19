# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --sample-size 100 --timeout 3600`
  - script usage: `main.py [-h] [--timeout TIMEOUT]`
  - argparse error: `main.py: error: unrecognized arguments: --sample-size 100`
- run-book command: `python code/main.py`
  - script usage: `ingestion.py [-h] --urls URLS [URLS ...] --output OUTPUT`
  - argparse error: `ingestion.py: error: the following arguments are required: --urls, --output`

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python code/main.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py --sample-size 100 --timeout 3600 (rc=2); python code/main.py (rc=1)

## Failing / missing run-book commands

- python code/main.py --sample-size 100 --timeout 3600 -> rc=2
    usage: main.py [-h] [--timeout TIMEOUT]
main.py: error: unrecognized arguments: --sample-size 100
- python code/main.py -> rc=1
    2026-09-19 13:33:43,433 - INFO - Hard timeout set to 18000 seconds (5:00:00).
2026-09-19 13:33:43,433 - INFO - Verifying runner environment...
2026-09-19 13:33:45,872 - INFO - No GPU detected. Running on CPU.
2026-09-19 13:33:45,872 - INFO - Detected CPU count: 4
2026-09-19 13:33:45,872 - INFO - Starting pipeline execution...
2026-09-19 13:33:45,873 - INFO - Data ingestion module found. Executing...
usage: ingestion.py [-h] --urls URLS [URLS ...] --output OUTPUT
                    [--stats STATS]
ingestion.py: error: the following arguments are required: --urls, --output
2026-09-19 13:33:46,849 - ERROR - Pipeline failed with unexpected error: Data ingestion failed with exit code 2
