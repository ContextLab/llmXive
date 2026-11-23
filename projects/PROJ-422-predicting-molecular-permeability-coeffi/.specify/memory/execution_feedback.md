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
icting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/nn/modules/transformer.py:20: UserWarning: Failed to initialize NumPy: _ARRAY_API not found (Triggered internally at ../torch/csrc/utils/tensor_numpy.cpp:84.)
  device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),
2026-10-26 09:18:31,219 INFO __main__: === GNN + RF training step (T007) ===
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
effi/code/analysis/explain.py", line 70, in load_test_graphs_from_csv
    df = pd.read_csv(csv_path)
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1026, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/test.csv'

- bash ./run_all.sh -> rc=1
st epoch: 5 with val loss 0.0000.
2026-10-26 09:18:38,616 INFO models.gnn: Peak memory usage during training: 0.636 GB
2026-10-26 09:18:38,617 INFO __main__: GNN checkpoint written to code/models/gnn.pt
2026-10-26 09:18:38,617 INFO models.rf: Training Random Forest: n_estimators=200, max_features=sqrt
2026-10-26 09:18:38,767 INFO models.rf: Random Forest training complete. Feature importances shape: (6,)
2026-10-26 09:18:38,793 INFO __main__: Random Forest model saved to code/models/rf.pkl
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

