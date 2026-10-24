# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/processed_data.csv: results file is EMPTY — the analysis produced no rows

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/processed_data.csv: results file is EMPTY — the analysis produced no rows; 1 run-book script(s) missing (plan/impl path mismatch): bash ./run_all.sh; 3 command(s) failed: python code/data/preprocess.py (rc=1); python code/analysis/train.py --config config.yaml (rc=1); python code/analysis/explain.py (rc=1)

## Failing / missing run-book commands

- python code/data/preprocess.py -> rc=1
value; row excluded.
2026-10-24 19:18:39,438 WARNING __main__: Missing SMILES value; row excluded.
2026-10-24 19:18:39,438 WARNING __main__: Missing SMILES value; row excluded.
2026-10-24 19:18:39,438 WARNING __main__: Missing SMILES value; row excluded.
2026-10-24 19:18:39,438 WARNING __main__: Missing SMILES value; row excluded.
2026-10-24 19:18:39,438 INFO __main__: Valid molecules after SMILES parsing: 0
2026-10-24 19:18:39,438 INFO __main__: Invalid SMILES count: 5
2026-10-24 19:18:39,438 INFO __main__: Retention rate (mol_valid / total): 0.00%
2026-10-24 19:18:39,439 INFO __main__: Performing bias check (FR‑013)...
2026-10-24 19:18:39,439 WARNING __main__: No descriptor columns found for bias check.
2026-10-24 19:18:39,439 INFO __main__: Processed CSV written to /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/processed_data.csv
2026-10-24 19:18:39,449 INFO __main__: Processed Parquet written to /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/processed_data.parquet
2026-10-24 19:18:39,449 ERROR __main__: Retention rate 0.00% below threshold 95.00%. Aborting.

- python code/analysis/train.py --config config.yaml -> rc=1
{"timestamp": "2026-10-24T19:18:40.108510+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "============================================================", "module": "train", "function": "main", "line": 321}
{"timestamp": "2026-10-24T19:18:40.108600+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "Molecular Permeability \u2013 Training Pipeline", "module": "train", "function": "main", "line": 322}
{"timestamp": "2026-10-24T19:18:40.108633+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "============================================================", "module": "train", "function": "main", "line": 323}
{"timestamp": "2026-10-24T19:18:40.108795+00:00", "level": "ERROR", "task_id": "T004", "logger": "root", "message": "Training or test split not found. Ensure the split step has run.", "module": "train", "function": "main", "line": 338}


- python code/analysis/explain.py -> rc=1
{"timestamp": "2026-10-24T19:18:42.732914+00:00", "level": "ERROR", "task_id": "T004", "logger": "__main__", "message": "Model checkpoint not found at data/interim/gnn_checkpoint.pt. Please run training (T022) first.", "module": "explain", "function": "main", "line": 229}

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(

- bash ./run_all.sh -> rc=-1

shell script must be an existing project-local .sh file
