# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (results/perf_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (results/perf_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/main.py --action download (rc=1); python code/main.py --action simulate --config data/dependency_manifest.yaml (rc=1); python code/main.py --action plot --input results/type1_error_rates.csv (rc=1)

## Failing / missing run-book commands

- python code/main.py --action download -> rc=1
Loading configuration...
Estimated replications: 1000
Loading and validating datasets...
Pipeline failed: load_datasets() missing 3 required positional arguments: 'manifest_path', 'data_raw_dir', and 'checksums_path'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-483-evaluating-the-robustness-of-common-stat/code/main.py", line 225, in main
    load_datasets() # Ensures data/raw/ exists and is valid
    ^^^^^^^^^^^^^^^
TypeError: load_datasets() missing 3 required positional arguments: 'manifest_path', 'data_raw_dir', and 'checksums_path'

- python code/main.py --action simulate --config data/dependency_manifest.yaml -> rc=1
Loading configuration...
Estimated replications: 1000
Loading and validating datasets...
Pipeline failed: load_datasets() missing 3 required positional arguments: 'manifest_path', 'data_raw_dir', and 'checksums_path'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-483-evaluating-the-robustness-of-common-stat/code/main.py", line 225, in main
    load_datasets() # Ensures data/raw/ exists and is valid
    ^^^^^^^^^^^^^^^
TypeError: load_datasets() missing 3 required positional arguments: 'manifest_path', 'data_raw_dir', and 'checksums_path'

- python code/main.py --action plot --input results/type1_error_rates.csv -> rc=1
Loading configuration...
Estimated replications: 1000
Loading and validating datasets...
Pipeline failed: load_datasets() missing 3 required positional arguments: 'manifest_path', 'data_raw_dir', and 'checksums_path'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-483-evaluating-the-robustness-of-common-stat/code/main.py", line 225, in main
    load_datasets() # Ensures data/raw/ exists and is valid
    ^^^^^^^^^^^^^^^
TypeError: load_datasets() missing 3 required positional arguments: 'manifest_path', 'data_raw_dir', and 'checksums_path'

- python code/main.py --action verify -> rc=1
Loading configuration...
Estimated replications: 1000
Loading and validating datasets...
Pipeline failed: load_datasets() missing 3 required positional arguments: 'manifest_path', 'data_raw_dir', and 'checksums_path'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-483-evaluating-the-robustness-of-common-stat/code/main.py", line 225, in main
    load_datasets() # Ensures data/raw/ exists and is valid
    ^^^^^^^^^^^^^^^
TypeError: load_datasets() missing 3 required positional arguments: 'manifest_path', 'data_raw_dir', and 'checksums_path'

