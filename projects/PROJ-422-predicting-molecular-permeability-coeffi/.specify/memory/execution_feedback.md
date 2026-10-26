# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/split_metadata.json: metric is null/NaN (stratify_column) — not a real measurement
- every produced artifact is gitignored (data/processed/processed_data.csv, data/processed/processed_data.parquet, data/processed/split_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/split_metadata.json: metric is null/NaN (stratify_column) — not a real measurement; every produced artifact is gitignored (data/processed/processed_data.csv, data/processed/processed_data.parquet, data/processed/split_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/analysis/train.py --config config.yaml (rc=1); python code/analysis/explain.py (rc=1); bash ./run_all.sh (rc=1)

## Failing / missing run-book commands

- python code/analysis/train.py --config config.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(
2026-10-26 08:18:54,926 INFO __main__: === GNN + RF training step (T007) ===
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 281, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 188, in main
    df_train = _load_split("train")
               ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 55, in _load_split
    raise FileNotFoundError(f"{split_name} split not found at {csv_path}")
FileNotFoundError: train split not found at /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed/train.csv

- python code/analysis/explain.py -> rc=1
{"timestamp": "2026-10-26T08:18:59.042479+00:00", "level": "ERROR", "task_id": "T004", "logger": "__main__", "message": "Model checkpoint not found at data/interim/gnn_checkpoint.pt. Please run training (T022) first.", "module": "explain", "function": "main", "line": 229}

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(

- bash ./run_all.sh -> rc=1
-10-26 08:19:06,484 INFO models.gnn: GNN training completed. Best epoch: 50 with val loss 0.0154.
2026-10-26 08:19:06,485 INFO __main__: GNN checkpoint written to code/models/gnn.pt
2026-10-26 08:19:06,486 INFO models.rf: Training Random Forest: n_estimators=200, max_features=sqrt
2026-10-26 08:19:06,684 INFO models.rf: Random Forest training complete. Feature importances shape: (6,)
2026-10-26 08:19:06,720 INFO __main__: Random Forest model saved to code/models/rf.pkl
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 281, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 234, in main
    gnn_val_rmse = _evaluate_gnn_on_loader(
                   ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 141, in _evaluate_gnn_on_loader
    y_pred = np.concatenate(all_preds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: zero-dimensional arrays cannot be concatenated

