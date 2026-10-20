# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv (rc=1); python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 (rc=1); python src/training/evaluate.py --metrics_out data/results_composition_only.json (rc=1)

## Failing / missing run-book commands

- python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv -> rc=1
ome/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/apply.py", line 1063, in apply_standard
    results, res_index = self.apply_series_generator()
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/apply.py", line 1081, in apply_series_generator
    results[i] = self.func(v, *self.args, **self.kwargs)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/data/loader.py", line 191, in <lambda>
    {k: _to_native(row[k]) for k in required_columns}, schema
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/data/loader.py", line 191, in <dictcomp>
    {k: _to_native(row[k]) for k in required_columns}, schema
        ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/data/loader.py", line 58, in _to_native
    if isinstance(value, (np.generic,)):
                          ^^
NameError: name 'np' is not defined

- python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/train_gnn.py", line 178, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/train_gnn.py", line 139, in main
    avg_val_loss = sum(val_losses) / len(val_losses)
                   ~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~
ZeroDivisionError: division by zero

- python src/training/evaluate.py --metrics_out data/results_composition_only.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 233, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 167, in main
    gnn_model = _train_gnn(
                ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py", line 108, in _train_gnn
    val_loss = sum(val_losses) / len(val_losses)
               ~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~
ZeroDivisionError: division by zero

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

- python src/interpret/pca_correlation.py --report_out interpretability_report.md -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/pca_correlation.py", line 68, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/pca_correlation.py", line 36, in main
    raise FileNotFoundError(f"Embeddings file not found at {embeddings_path}")
FileNotFoundError: Embeddings file not found at outputs/node_embeddings.npy

- python -m pytest -q tests/ -> rc=1
      agg_obj = self
        if subset is not None:
            # subset needs to be list
            if not is_list_like(subset):
                subset = [subset]
            ax = self._get_axis(agg_axis)
            indices = ax.get_indexer_for(subset)
            check = indices == -1
            if check.any():
>               raise KeyError(np.array(subset)[check].tolist())
E               KeyError: ['hardness']

/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py:6670: KeyError
=========================== short test summary info ============================
FAILED tests/contract/test_dataset_schema.py::test_crystal_system_enum_is_seven_systems
FAILED tests/unit/test_loader.py::test_loader_filters_rows - NameError: name ...
FAILED tests/unit/test_loader.py::test_zero_band_gap_metals_retained - NameEr...
FAILED tests/unit/test_loader.py::test_outlier_removal_logged - NameError: na...
FAILED tests/unit/test_loader.py::test_unknown_element_warning - NameError: n...
FAILED tests/unit/test_loader.py::test_ram_limit_assertion - NameError: name ...
FAILED tests/unit/test_loader.py::test_missing_required_column_raises - KeyEr...
7 failed, 20 passed in 4.03s


