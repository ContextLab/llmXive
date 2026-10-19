# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/esol.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/esol.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/06_feature_importance.py; python code/06_diagnostics.py; 8 command(s) failed: python code/01_data_ingestion.py --source esol --url https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv (rc=1); python code/02_tda_computation.py --grid 10 (rc=1); python code/03_feature_engineering.py (rc=1); 7 declared deliverable(s) absent: data/processed/combined_features.csv; data/processed/filtered_esol.csv; data/processed/power_analysis_report.json

## Failing / missing run-book commands

- python code/01_data_ingestion.py --source esol --url https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv -> rc=1
2026-10-19 08:13:44,862 - data_ingestion - INFO - Downloading ESOL dataset from https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv
2026-10-19 08:13:45,221 - data_ingestion - INFO - Download complete (data/raw/esol.csv, 96699 bytes)
2026-10-19 08:13:45,221 - data_ingestion - INFO - Adding string ``molecule_id`` column to raw dataset (if missing).
2026-10-19 08:13:45,231 - data_ingestion - INFO - ``molecule_id`` column added.
2026-10-19 08:13:45,232 - data_ingestion - INFO - Checksum recorded in data/checksums.txt
2026-10-19 08:13:45,234 - data_ingestion - ERROR - Required target column 'logP' not found after renaming.


- python code/02_tda_computation.py --grid 10 -> rc=1
Error: Expected filtered dataset at /home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/data/processed/filtered_esol.csv


- python code/03_feature_engineering.py -> rc=1
2026-10-19 08:13:46,410 - feature_engineering - INFO - Starting Feature Engineering (T004)...
2026-10-19 08:13:46,410 - feature_engineering - ERROR - Filtered dataset missing at /home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/data/processed/filtered_esol.csv. Run 01_data_ingestion.py first.


- python code/04_model_training.py -> rc=1
jects/PROJ-444-predicting-molecular-properties-from-top/code/04_model_training.py", line 235, in run_model_training
    raise FileNotFoundError(f"Missing {features_path} – run T004 first.")
FileNotFoundError: Missing /home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/data/processed/combined_features.csv – run T004 first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/04_model_training.py", line 400, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/04_model_training.py", line 387, in main
    report = run_model_training(logger)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/04_model_training.py", line 235, in run_model_training
    raise FileNotFoundError(f"Missing {features_path} – run T004 first.")
FileNotFoundError: Missing /home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/data/processed/combined_features.csv – run T004 first.

- python code/06_feature_importance.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/06_feature_importance.py': [Errno 2] No such file or directory

- python code/06_diagnostics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/06_diagnostics.py': [Errno 2] No such file or directory

- python code/05_sensitivity_analysis.py --grids 10 20 30 -> rc=1
2026-10-19 08:13:48,369 - INFO - === Sensitivity Analysis (Task T007, FR-006) ===
2026-10-19 08:13:48,369 - INFO - Grid resolutions: [10, 20, 30]

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/05_sensitivity_analysis.py", line 293, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/05_sensitivity_analysis.py", line 165, in main
    base = load_base_frame()
           ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/05_sensitivity_analysis.py", line 80, in load_base_frame
    raise FileNotFoundError(f"Missing {path} - run T004 first.")
FileNotFoundError: Missing /home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/data/processed/combined_features.csv - run T004 first.

- python code/07_resource_monitor.py -> rc=1
2026-10-19 08:13:48,564 - ERROR - No command provided to monitor.


- python -m pytest tests/contract/ -> rc=1
est_t009_schemas.py::test_feature_matrix_schema_exists_and_valid
FAILED tests/contract/test_t009_schemas.py::test_model_metrics_schema_exists_and_valid
FAILED tests/contract/test_t009_schemas.py::test_all_schemas_are_valid_yaml
FAILED tests/contract/test_t016_features.py::test_tda_features_file_exists - ...
FAILED tests/contract/test_t016_features.py::test_traditional_descriptors_file_exists
FAILED tests/contract/test_tda_10x10.py::test_persistence_images_10x10_exists
FAILED tests/contract/test_tda_10x10_schema.py::test_file_exists - AssertionE...
FAILED tests/contract/test_tda_10x10_schema.py::test_schema_compliance - File...
FAILED tests/contract/test_tda_10x10_schema.py::test_no_nan_values - FileNotF...
FAILED tests/contract/test_tda_10x10_schema.py::test_image_vector_length - Fi...
FAILED tests/contract/test_tda_10x10_schema.py::test_molecule_id_is_string - ...
FAILED tests/contract/test_tda_10x10_schema.py::test_valid_molecules_count - ...
FAILED tests/contract/test_tda_schema.py::test_tda_schema_compliance - Assert...
FAILED tests/contract/test_tda_schema.py::test_traditional_descriptors_schema
======================== 16 failed, 10 skipped in 0.74s ========================


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
============================== 4 errors in 0.78s ===============================



## Declared deliverables still missing

- data/processed/combined_features.csv
- data/processed/filtered_esol.csv
- data/processed/power_analysis_report.json
- data/processed/scaffold_counts.json
- data/processed/splits.json
- data/processed/topological_features_10x10.csv
- data/processed/traditional_features.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/combined_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — IS a run-book command
    - `code/04_model_training.py` — IS a run-book command
    - `code/05_sensitivity_analysis.py` — IS a run-book command
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
    - `code/05_sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/splits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/topological_features_10x10.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — IS a run-book command
    - `code/tests/test_feature_matrix.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/topological_features_10x10.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/traditional_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — IS a run-book command
    - `code/04_model_training.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/traditional_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
