# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/mobius_2bit.npy, data/raw/mobius_array.npy) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/mobius_2bit.npy, data/raw/mobius_array.npy) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/calibration.py --array data/raw/mobius_array.npy --out-calibration data/processed/calibration_test.json --out-empirical data/processed/empirical_uniformity.json; 5 command(s) failed: python code/main.py (rc=1); python code/autocorrelation.py --array data/raw/mobius_array.npy --out data/processed/autocorrelation_stats.csv (rc=1); python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy (rc=1); 4 declared deliverable(s) absent: data/processed/autocorrelation_raw.csv; data/processed/demo_autocorr.csv; data/processed/pipeline_status.json

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/main.py", line 35, in <module>
    from null_distribution import main as null_dist_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/null_distribution.py", line 39, in <module>
    from permutation import (
ImportError: cannot import name 'generate_permutations' from 'permutation' (/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/permutation.py)

- python code/autocorrelation.py --array data/raw/mobius_array.npy --out data/processed/autocorrelation_stats.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/autocorrelation.py", line 288, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/autocorrelation.py", line 190, in main
    with WINDOW_STARTS_JSON.open("r", encoding="utf-8") as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/window_starts.json'

- python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/permutation.py", line 186, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/code/permutation.py", line 113, in main
    raise FileNotFoundError(f"Window index not found: {window_index_path}")
FileNotFoundError: Window index not found: data/processed/window_index.csv

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

- data/processed/autocorrelation_raw.csv
- data/processed/demo_autocorr.csv
- data/processed/pipeline_status.json
- data/processed/window_index.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/autocorrelation_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/autocorrelation.py` — IS a run-book command
    - `code/cross_validate_autocorrelation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/autocorrelation_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/demo_autocorr.csv` is declared but was NOT written. Scripts referencing it:
    - `code/autocorrelation.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/demo_autocorr.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pipeline_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/cross_validate_autocorrelation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pipeline_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/window_index.csv` is declared but was NOT written. Scripts referencing it:
    - `code/autocorrelation.py` — IS a run-book command
    - `code/permutation.py` — IS a run-book command
    - `code/window_index.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/window_index.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
