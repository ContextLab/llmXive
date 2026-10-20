# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/interpret/pca_correlation.py --report_out interpretability_report.md; 6 command(s) failed: python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv (rc=1); python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 (rc=1); python src/training/evaluate.py --metrics_out data/results_composition_only.json (rc=1)

## Failing / missing run-book commands

- python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv -> rc=1
/loader.py", line 127, in load_and_clean
    sample = pd.read_csv(input_path, nrows=0)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/materials.csv'

- python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 -> rc=1
om-comp/src/training/train_gnn.py", line 65, in main
    df = pd.read_csv(args.data)
         ^^^^^^^^^^^^^^^^^^^^^^
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
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/materials_processed.csv'

- python src/training/evaluate.py --metrics_out data/results_composition_only.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 24, in <module>
    from src.models.rf_baseline import train_rf
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/models/rf_baseline.py", line 14, in <module>
    from pymatgen.core import Composition
ModuleNotFoundError: No module named 'pymatgen'

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
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/extract_embeddings.py", line 36, in main
    raise FileNotFoundError(f"Processed data not found at {data_path}")
FileNotFoundError: Processed data not found at data/processed/materials_processed.csv

- python src/interpret/pca_correlation.py --report_out interpretability_report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/pca_correlation.py': [Errno 2] No such file or directory

- python -m pytest -q tests/ -> rc=1
folds
        assert folds1 == folds2
    
        # Each fold should preserve crystal‑system proportions (approximately)
        for fold in folds1:
            # training portion of a fold is 80 % of the original train set (16 rows)
            # → 12 or 13 rows depending on rounding, but the ratio should stay ~1:1
            train_counts = pd.Series(fold["train"]).map(
                lambda mid: "cubic" if mid.startswith("cubic_") else "hexagonal"
            ).value_counts()
            # Because the original train set is perfectly balanced, each fold's train
            # portion must also be balanced.
>           assert train_counts["cubic"] == train_counts["hexagonal"]
E           assert 6 == 7

tests/unit/test_split.py:82: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_dataset_schema.py::test_crystal_system_enum_is_seven_systems
FAILED tests/unit/test_graph_builder.py::test_self_loops_and_symmetry - asser...
FAILED tests/unit/test_loader.py::test_loader_filters_rows - assert 3 == 1
FAILED tests/unit/test_split.py::test_generate_cv_folds_is_stratified_and_reproducible
4 failed, 10 passed in 1.93s


