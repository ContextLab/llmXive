# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/06_feature_importance.py; python code/06_diagnostics.py; 3 command(s) failed: python code/07_resource_monitor.py (rc=1); python -m pytest tests/contract/ (rc=1); python -m pytest tests/unit/ (rc=2)

## Failing / missing run-book commands

- python code/06_feature_importance.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/06_feature_importance.py': [Errno 2] No such file or directory

- python code/06_diagnostics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/06_diagnostics.py': [Errno 2] No such file or directory

- python code/07_resource_monitor.py -> rc=1
2026-10-19 09:13:56,188 - ERROR - No command provided to monitor.


- python -m pytest tests/contract/ -> rc=1
osixPath('data/processed/traditional_descriptors.csv').exists
=========================== short test summary info ============================
FAILED tests/contract/test_metrics_schema.py::test_metrics_schema_compliance
FAILED tests/contract/test_t009_schemas.py::test_dataset_schema_exists_and_valid
FAILED tests/contract/test_t009_schemas.py::test_feature_matrix_schema_exists_and_valid
FAILED tests/contract/test_t009_schemas.py::test_model_metrics_schema_exists_and_valid
FAILED tests/contract/test_t009_schemas.py::test_all_schemas_are_valid_yaml
FAILED tests/contract/test_t016_features.py::test_tda_features_file_exists - ...
FAILED tests/contract/test_t016_features.py::test_traditional_descriptors_file_exists
FAILED tests/contract/test_tda_10x10.py::test_persistence_images_10x10_schema
FAILED tests/contract/test_tda_10x10.py::test_persistence_images_10x10_no_nan
FAILED tests/contract/test_tda_10x10.py::test_persistence_images_10x10_non_negative
FAILED tests/contract/test_tda_schema.py::test_tda_schema_compliance - Assert...
FAILED tests/contract/test_tda_schema.py::test_traditional_descriptors_schema
=================== 12 failed, 8 passed, 6 skipped in 0.76s ====================


- python -m pytest tests/unit/ -> rc=2
or while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/tests/unit/test_t015_edge_cases.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_t015_edge_cases.py:11: in <module>
    from utils.graph_builder import log_invalid_smiles, setup_invalid_smiles_logger, is_valid_molecule
E   ImportError: cannot import name 'log_invalid_smiles' from 'utils.graph_builder' (/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/tests/unit/../../code/utils/graph_builder.py)
=========================== short test summary info ============================
ERROR tests/unit/test_data_ingestion.py
ERROR tests/unit/test_persistence_utils.py
ERROR tests/unit/test_persistence_utils_sparse.py
ERROR tests/unit/test_t015_edge_cases.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.65s ===============================


