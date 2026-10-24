# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/processed_data.csv: column(s) bias_warning are EMPTY in every one of 5 rows — that measure was never recorded

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/processed_data.csv: column(s) bias_warning are EMPTY in every one of 5 rows — that measure was never recorded; 1 run-book script(s) missing (plan/impl path mismatch): bash ./run_all.sh; 3 command(s) failed: python code/data/preprocess.py (rc=1); python code/analysis/train.py --config config.yaml (rc=1); python code/analysis/explain.py (rc=1); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python code/data/preprocess.py -> rc=1
ect on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  processed_df[col].fillna(median_val, inplace=True)
2026-10-24 18:36:56,995 INFO __main__: Performing bias check (FR‑013)...
2026-10-24 18:36:56,998 INFO __main__: Bias check passed; no high correlations detected.
2026-10-24 18:36:57,000 INFO __main__: Processed CSV written to /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/processed_data.csv
2026-10-24 18:36:57,004 ERROR __main__: Preprocessing failed: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python code/analysis/train.py --config config.yaml -> rc=1
{"timestamp": "2026-10-24T18:36:57.795357+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "============================================================", "module": "train", "function": "main", "line": 321}
{"timestamp": "2026-10-24T18:36:57.795471+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "Molecular Permeability \u2013 Training Pipeline", "module": "train", "function": "main", "line": 322}
{"timestamp": "2026-10-24T18:36:57.795527+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "============================================================", "module": "train", "function": "main", "line": 323}
{"timestamp": "2026-10-24T18:36:57.795782+00:00", "level": "ERROR", "task_id": "T004", "logger": "root", "message": "Training or test split not found. Ensure the split step has run.", "module": "train", "function": "main", "line": 338}


- python code/analysis/explain.py -> rc=1
{"timestamp": "2026-10-24T18:37:00.132896+00:00", "level": "ERROR", "task_id": "T004", "logger": "__main__", "message": "Model checkpoint not found at data/interim/gnn_checkpoint.pt. Please run training (T022) first.", "module": "explain", "function": "main", "line": 229}


- bash ./run_all.sh -> rc=-1

shell script must be an existing project-local .sh file

## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
