# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy`
  - script usage: `permutation.py [-h] [--L L] [--start START] [--output OUTPUT]`
  - argparse error: `permutation.py: error: unrecognized arguments: --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/calibration.py --array data/raw/mobius_array.npy --out-calibration data/processed/calibration_test.json --out-empirical data/processed/empirical_uniformity.json; 4 command(s) failed: python code/main.py (rc=-1); python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy (rc=2); python code/sensitivity.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy --out data/processed/sensitivity_summary.csv (rc=1); 1 declared deliverable(s) absent: data/processed/window_index.csv

## Failing / missing run-book commands

- python code/main.py -> rc=-1
Saved Möbius array of length 10000000 to data/raw/mobius_array.npy
Saved packed Möbius array (2500001 bytes) to data/raw/mobius_2bit.npy
Saved Möbius array of length 10000000 to data/raw/mobius_array.npy
Saved packed Möbius array (2500001 bytes) to data/raw/mobius_2bit.npy
Möbius array written to: data/raw/mobius_array.npy
Window start indices written to: data/raw/window_starts.json
Demo autocorrelation written to data/results/demo_autocorr.csv: start=44622, L=1000, h=1, autocorrelation=-0.047047047047
Full autocorrelation matrix written to data/processed/autocorr_raw.csv


[TIMEOUT after 120s]
- python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy -> rc=2

usage: permutation.py [-h] [--L L] [--start START] [--output OUTPUT]
                      [--block-size BLOCK_SIZE]
                      [--n-permutations N_PERMUTATIONS] [--seed SEED] [--run]
permutation.py: error: unrecognized arguments: --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy

- python code/calibration.py --array data/raw/mobius_array.npy --out-calibration data/processed/calibration_test.json --out-empirical data/processed/empirical_uniformity.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-728-autocorrelation-of-the-m-bius-function-i/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/calibration.py': [Errno 2] No such file or directory

- python code/sensitivity.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy --out data/processed/sensitivity_summary.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/sensitivity.py", line 198, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/sensitivity.py", line 97, in main
    raise FileNotFoundError(f"Required stats CSV not found: {STATS_CSV}")
FileNotFoundError: Required stats CSV not found: data/processed/autocorr_stats.csv

- python code/viz.py --stats data/processed/autocorrelation_stats.csv --outdir outputs/figures/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/viz.py", line 109, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/viz.py", line 100, in main
    raise FileNotFoundError(f"Required CSV not found: {INPUT_CSV}")
FileNotFoundError: Required CSV not found: data/processed/autocorr_stats.csv


## Declared deliverables still missing

- data/processed/window_index.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/window_index.csv` is declared but was NOT written. Scripts referencing it:
    - `code/window_index.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/window_index.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
