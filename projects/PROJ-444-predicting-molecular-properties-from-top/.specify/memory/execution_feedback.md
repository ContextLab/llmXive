# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/01_data_ingestion.py --source esol --url https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv`
  - script usage: `01_data_ingestion.py [-h] --url URL`
  - argparse error: `01_data_ingestion.py: error: unrecognized arguments: --source esol`
- run-book command: `python code/02_tda_computation.py --grid 10`
  - script usage: `02_tda_computation.py [-h] [--resolution RESOLUTION]`
  - argparse error: `02_tda_computation.py: error: unrecognized arguments: --grid 10`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/06_feature_importance.py; python code/06_diagnostics.py; python code/05_sensitivity_analysis.py --grids 10 20 30; 7 command(s) failed: python code/01_data_ingestion.py --source esol --url https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv (rc=2); python code/02_tda_computation.py --grid 10 (rc=2); python code/03_feature_engineering.py (rc=1); 5 declared deliverable(s) absent: data/processed/combined_features.csv; data/processed/filtered_esol.csv; data/processed/power_analysis_report.json

## Failing / missing run-book commands

- python code/01_data_ingestion.py --source esol --url https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv -> rc=2

usage: 01_data_ingestion.py [-h] --url URL
01_data_ingestion.py: error: unrecognized arguments: --source esol

- python code/02_tda_computation.py --grid 10 -> rc=2

usage: 02_tda_computation.py [-h] [--resolution RESOLUTION]
02_tda_computation.py: error: unrecognized arguments: --grid 10

- python code/03_feature_engineering.py -> rc=1
2026-10-19 06:32:52,226 - feature_engineering - INFO - Starting Feature Engineering (T004)...
2026-10-19 06:32:52,226 - feature_engineering - ERROR - Filtered dataset missing at /home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/data/processed/filtered_esol.csv. Run 01_data_ingestion.py first.


- python code/04_model_training.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/04_model_training.py", line 21, in <module>
    from sklearn.metrics import r2_score, rmse
ImportError: cannot import name 'rmse' from 'sklearn.metrics' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/lib/python3.11/site-packages/sklearn/metrics/__init__.py)

- python code/06_feature_importance.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/06_feature_importance.py': [Errno 2] No such file or directory

- python code/06_diagnostics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/06_diagnostics.py': [Errno 2] No such file or directory

- python code/05_sensitivity_analysis.py --grids 10 20 30 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/05_sensitivity_analysis.py': [Errno 2] No such file or directory

- python code/07_resource_monitor.py -> rc=1
2026-10-19 06:32:53,056 - ERROR - No command provided to monitor.


- python -m pytest tests/contract/ -> rc=1
est_t009_schemas.py::test_feature_matrix_schema_exists_and_valid
FAILED tests/contract/test_t009_schemas.py::test_model_metrics_schema_exists_and_valid
FAILED tests/contract/test_t009_schemas.py::test_all_schemas_are_valid_yaml
FAILED tests/contract/test_t016_features.py::test_tda_features_file_exists - ...
FAILED tests/contract/test_t016_features.py::test_traditional_descriptors_file_exists
FAILED tests/contract/test_tda_10x10.py::test_persistence_images_10x10_exists
FAILED tests/contract/test_tda_10x10_schema.py::test_file_exists - AssertionE...
FAILED tests/contract/test_tda_10x10_schema.py::test_schema_compliance - Asse...
FAILED tests/contract/test_tda_10x10_schema.py::test_no_nan_values - Assertio...
FAILED tests/contract/test_tda_10x10_schema.py::test_image_vector_length - As...
FAILED tests/contract/test_tda_10x10_schema.py::test_non_empty_dataset - Asse...
FAILED tests/contract/test_tda_10x10_schema.py::test_valid_molecules_count - ...
FAILED tests/contract/test_tda_schema.py::test_tda_schema_compliance - Assert...
FAILED tests/contract/test_tda_schema.py::test_traditional_descriptors_schema
======================== 16 failed, 10 skipped in 0.30s ========================


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
============================== 4 errors in 0.57s ===============================



## Declared deliverables still missing

- data/processed/combined_features.csv
- data/processed/filtered_esol.csv
- data/processed/power_analysis_report.json
- data/processed/scaffold_counts.json
- data/processed/splits.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/combined_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — IS a run-book command
    - `code/04_model_training.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/combined_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_esol.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
    - `code/02_tda_computation.py` — IS a run-book command
    - `code/03_feature_engineering.py` — IS a run-book command
    - `code/tests/test_feature_matrix.py` — NOT invoked by the run-book
    - `code/tests/test_tda_feature_matrix.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_esol.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scaffold_counts.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/scaffold_counts.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/splits.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
    - `code/04_model_training.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/splits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
