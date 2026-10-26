# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/split_metadata.json: metric is null/NaN (max_distribution_diff) — not a real measurement

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/split_metadata.json: metric is null/NaN (max_distribution_diff) — not a real measurement; 3 command(s) failed: python code/analysis/train.py --config config.yaml (rc=1); python code/analysis/explain.py (rc=1); bash ./run_all.sh (rc=1)

## Failing / missing run-book commands

- python code/analysis/train.py --config config.yaml -> rc=1
-coeffi/code/analysis/train.py\", line 342, in main\n    _, feature_cols, X_train, y_train = load_data(train_path, target_col=\"target\")\n                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py\", line 79, in load_data\n    X = df[feature_cols].values.astype(np.float32)\n        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nValueError: could not convert string to float: '{\"nodes\": [{\"atom_idx\": 0, \"symbol\": \"C\", \"atomic_num\": 6, \"degree\": 1, \"formal_charge\": 0, \"hybridization\": \"SP3\", \"aromatic\": false}, {\"atom_idx\": 1, \"symbol\": \"C\", \"atomic_num\": 6, \"degree\": 2, \"formal_charge\": 0, \"hybridization\": \"SP3\", \"aromatic\": false}, {\"atom_idx\": 2, \"symbol\": \"N\", \"atomic_num\": 7, \"degree\": 1, \"formal_charge\": 0, \"hybridization\": \"SP3\", \"aromatic\": false}], \"edges\": [{\"source\": 0, \"target\": 1, \"bond_type\": \"SINGLE\", \"aromatic\": false}, {\"source\": 1, \"target\": 2, \"bond_type\": \"SINGLE\", \"aromatic\": false}]}'\n", "module": "train", "function": "main", "line": 473}


- python code/analysis/explain.py -> rc=1
{"timestamp": "2026-10-26T07:53:33.624876+00:00", "level": "ERROR", "task_id": "T004", "logger": "__main__", "message": "Model checkpoint not found at data/interim/gnn_checkpoint.pt. Please run training (T022) first.", "module": "explain", "function": "main", "line": 229}

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(

- bash ./run_all.sh -> rc=1
permeability-coeffi/data/processed/processed_data.parquet
2026-10-26 07:53:37,491 INFO __main__: Retention rate: 100.00%
2026-10-26 07:53:38,386 INFO __main__: Loading processed data from /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/processed_data.parquet
2026-10-26 07:53:38,403 INFO __main__: Dataset has 5 rows (≤5); using leave‑one‑out split.
2026-10-26 07:53:38,407 INFO __main__: Wrote train split: /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/train.csv & /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/train.parquet
2026-10-26 07:53:38,409 INFO __main__: Wrote test split: /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/test.csv & /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/test.parquet
2026-10-26 07:53:38,410 INFO __main__: Split metadata written to /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/split_metadata.json

