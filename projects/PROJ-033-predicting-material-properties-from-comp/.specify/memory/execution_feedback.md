# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/materials_processed.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/materials_processed.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python src/interpret/pca_correlation.py --report_out interpretability_report.md; 5 command(s) failed: python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 (rc=1); python src/training/evaluate.py --metrics_out data/results_composition_only.json (rc=1); python src/inference/predict.py --formula "Fe2O3" --out data/predictions.json (rc=1)

## Failing / missing run-book commands

- python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 -> rc=1
ve/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/train_gnn.py", line 173, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/train_gnn.py", line 65, in main
    train_df, val_df, _ = stratified_split(df, random_state=args.seed)
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/split.py", line 51, in stratified_split
    train_val_idx, test_idx = next(sss_test.split(df, df["crystal_system"]))
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/sklearn/model_selection/_split.py", line 1841, in split
    for train, test in self._iter_indices(X, y, groups):
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/sklearn/model_selection/_split.py", line 2245, in _iter_indices
    raise ValueError(
ValueError: The least populated class in y has only 1 member, which is too few. The minimum number of groups for any class cannot be less than 2.

- python src/training/evaluate.py --metrics_out data/results_composition_only.json -> rc=1
projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 225, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 149, in main
    train_df, val_df, test_df = stratified_split(df, random_state=args.seed)
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/split.py", line 51, in stratified_split
    train_val_idx, test_idx = next(sss_test.split(df, df["crystal_system"]))
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/sklearn/model_selection/_split.py", line 1841, in split
    for train, test in self._iter_indices(X, y, groups):
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/sklearn/model_selection/_split.py", line 2245, in _iter_indices
    raise ValueError(
ValueError: The least populated class in y has only 1 member, which is too few. The minimum number of groups for any class cannot be less than 2.

- python src/inference/predict.py --formula "Fe2O3" --out data/predictions.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/inference/predict.py", line 86, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/inference/predict.py", line 59, in main
    state = _load_latest_checkpoint()
            ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/inference/predict.py", line 32, in _load_latest_checkpoint
    raise FileNotFoundError("No outputs directory – cannot locate checkpoint")
FileNotFoundError: No outputs directory – cannot locate checkpoint

- python src/interpret/extract_embeddings.py --out outputs/node_embeddings.npy -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/extract_embeddings.py", line 89, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/extract_embeddings.py", line 60, in main
    raise FileNotFoundError("No GNN checkpoint files found")
FileNotFoundError: No GNN checkpoint files found

- python src/interpret/pca_correlation.py --report_out interpretability_report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/pca_correlation.py': [Errno 2] No such file or directory

- python -m pytest -q tests/ -> rc=2
odule>
    df = pd.read_csv(FIXTURE_PATH)
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py:1026: in read_csv
    return _read(filepath_or_buffer, kwds)
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py:620: in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py:1620: in __init__
    self._engine = self._make_engine(f, self.engine)
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py:1880: in _make_engine
    self.handles = get_handle(
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py:873: in get_handle
    handle = open(
E   FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/data/fixtures/tiny_materials.csv'
=========================== short test summary info ============================
ERROR tests/unit/test_split.py - FileNotFoundError: [Errno 2] No such file or...
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 3.11s


