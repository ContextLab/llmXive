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
st epoch: 7 with val loss 0.0003.
2026-10-26 08:42:51,230 INFO models.gnn: Peak memory usage during training: 0.638 GB
2026-10-26 08:42:51,231 INFO __main__: GNN checkpoint written to code/models/gnn.pt
2026-10-26 08:42:51,232 INFO models.rf: Training Random Forest: n_estimators=200, max_features=sqrt
2026-10-26 08:42:51,441 INFO models.rf: Random Forest training complete. Feature importances shape: (6,)
2026-10-26 08:42:51,477 INFO __main__: Random Forest model saved to code/models/rf.pkl
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 281, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 234, in main
    gnn_val_rmse = _evaluate_gnn_on_loader(
                   ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 138, in _evaluate_gnn_on_loader
    all_preds.append(out.cpu().numpy())
                     ^^^^^^^^^^^^^^^^^
RuntimeError: Numpy is not available

- python code/analysis/explain.py -> rc=1
.11/site-packages/torch/nn/modules/transformer.py:20: UserWarning: Failed to initialize NumPy: _ARRAY_API not found (Triggered internally at ../torch/csrc/utils/tensor_numpy.cpp:84.)
  device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/explain.py", line 234, in main
    explain_gnn(model_path, test_data_path, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/explain.py", line 114, in explain_gnn
    test_graphs = load_test_graphs_from_csv(data_path, model_config)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/explain.py", line 75, in load_test_graphs_from_csv
    raise FileNotFoundError("Graph structure file 'data/interim/test_graphs.pt' not found. "
FileNotFoundError: Graph structure file 'data/interim/test_graphs.pt' not found. Please ensure T014b/T017 saved the graph structures.

- bash ./run_all.sh -> rc=1
t epoch: 10 with val loss 0.0012.
2026-10-26 08:43:00,418 INFO models.gnn: Peak memory usage during training: 0.638 GB
2026-10-26 08:43:00,419 INFO __main__: GNN checkpoint written to code/models/gnn.pt
2026-10-26 08:43:00,420 INFO models.rf: Training Random Forest: n_estimators=200, max_features=sqrt
2026-10-26 08:43:00,623 INFO models.rf: Random Forest training complete. Feature importances shape: (6,)
2026-10-26 08:43:00,659 INFO __main__: Random Forest model saved to code/models/rf.pkl
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 281, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 234, in main
    gnn_val_rmse = _evaluate_gnn_on_loader(
                   ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 138, in _evaluate_gnn_on_loader
    all_preds.append(out.cpu().numpy())
                     ^^^^^^^^^^^^^^^^^
RuntimeError: Numpy is not available

