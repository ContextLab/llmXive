# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/autocorrelation_stats.csv: header only, ZERO data rows — the analysis produced no rows

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/autocorrelation_stats.csv: header only, ZERO data rows — the analysis produced no rows; 1 run-book script(s) missing (plan/impl path mismatch): python code/calibration.py --array data/raw/mobius_array.npy --out-calibration data/processed/calibration_test.json --out-empirical data/processed/empirical_uniformity.json; 3 command(s) failed: python code/main.py (rc=-1); python code/sensitivity.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy --out data/processed/sensitivity_summary.csv (rc=1); python code/viz.py --stats data/processed/autocorrelation_stats.csv --outdir outputs/figures/ (rc=1); 1 declared deliverable(s) absent: data/processed/pipeline_status.json

## Failing / missing run-book commands

- python code/main.py -> rc=-1
Saved Möbius array of length 10000000 to data/raw/mobius_array.npy
Saved packed Möbius array (2500001 bytes) to data/raw/mobius_2bit.npy
Saved Möbius array of length 10000000 to data/raw/mobius_array.npy
Saved packed Möbius array (2500001 bytes) to data/raw/mobius_2bit.npy
Möbius array written to: data/raw/mobius_array.npy
Window start indices written to: data/raw/window_starts.json
Demo autocorrelation written to data/results/demo_autocorr.csv (legacy) and data/processed/demo_autocorr.csv (task T005): start=44622, L=1000, h=1, autocorrelation=-0.047047047047
Window index written to data/processed/window_index.csv (300 rows)
Generated missing window index CSV at data/processed/window_index.csv
Full autocorrelation matrix written to data/processed/autocorrelation_raw.csv


[TIMEOUT after 120s]
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

- data/processed/pipeline_status.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/pipeline_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/cross_validate_autocorrelation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pipeline_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
