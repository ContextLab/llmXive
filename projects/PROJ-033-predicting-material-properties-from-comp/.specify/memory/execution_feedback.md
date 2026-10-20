# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/interpret/pca_correlation.py --report_out interpretability_report.md; 5 command(s) failed: python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 (rc=1); python src/training/evaluate.py --metrics_out data/results_composition_only.json (rc=1); python src/inference/predict.py --formula "Fe2O3" --out data/predictions.json (rc=1)

## Failing / missing run-book commands

- python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/train_gnn.py", line 173, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/train_gnn.py", line 117, in main
    loss = loss_fn(pred_bg, target[:, 0]) + loss_fn(pred_h, target[:, 1])
                            ~~~~~~^^^^^^
IndexError: too many indices for tensor of dimension 1

- python src/training/evaluate.py --metrics_out data/results_composition_only.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 225, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 159, in main
    gnn_model = _train_gnn(
                ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 90, in _train_gnn
    loss = loss_fn(pred_bg, target[:, 0]) + loss_fn(pred_h, target[:, 1])
                            ~~~~~~^^^^^^
IndexError: too many indices for tensor of dimension 1

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

- python -m pytest -q tests/ -> rc=1
 assert on_disk["rows_kept"] == len(VALID_ROWS)
E       AssertionError: assert 8 == 9
E        +  where 9 = len([('m01', 'Fe2O3', 2.0, 6.0, 'hexagonal'), ('m02', 'SiO2', 5.0, 8.0, 'hexagonal'), ('m03', 'Al2O3', 4.5, 12.0, 'trigona...('m04', 'TiO2', 3.0, 9.0, 'tetragonal'), ('m05', 'ZnO', 3.2, 5.0, 'hexagonal'), ('m06', 'NiO', 2.5, 7.0, 'cubic'), ...])

tests/unit/test_loader.py:135: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  src.data.loader:loader.py:153 Unknown element(s) ['Fa', 'X'] in formula 'FakeX' – skipping material
WARNING  src.data.loader:loader.py:297 Chunk 1: skipping 1 rows with unknown elements
=========================== short test summary info ============================
FAILED tests/contract/test_dataset_schema.py::test_crystal_system_enum_is_seven_systems
FAILED tests/unit/test_loader.py::test_loader_filters_rows - AssertionError: ...
FAILED tests/unit/test_loader.py::test_zero_band_gap_metals_retained - assert...
FAILED tests/unit/test_loader.py::test_outlier_removal_logged - AssertionErro...
FAILED tests/unit/test_loader.py::test_ram_limit_assertion - AssertionError: ...
5 failed, 22 passed in 3.20s


