# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/06_feature_importance.py; python code/06_diagnostics.py; 9 command(s) failed: python code/01_data_ingestion.py --source lipophilicity (rc=1); python code/00_checksum_verify.py (rc=1); python code/02_tda_computation.py --grid 10 (rc=1); 7 declared deliverable(s) absent: data/processed/combined_features.csv; data/processed/filtered_lipophilicity.csv; data/processed/power_analysis_report.json

## Failing / missing run-book commands

- python code/01_data_ingestion.py --source lipophilicity -> rc=1
2026-10-23 19:09:21,252 - data_ingestion - ERROR - Raw Lipophilicity file not found at data/raw/lipophilicity.csv. Run 01_download_lipophilicity.py first.


- python code/00_checksum_verify.py -> rc=1

Missing file for checksum verification: data/raw/esol.csv
Missing file for checksum verification: data/raw/lipophilicity.csv
Checksum verification failed.

- python code/02_tda_computation.py --grid 10 -> rc=1
2026-10-23 19:09:21,933 - ERROR - Input file not found: data/processed/filtered_esol.csv


- python code/03_feature_engineering.py -> rc=1
2026-10-23 19:09:22,464 - feature_engineering - INFO - Starting Feature Engineering (T004)...
2026-10-23 19:09:22,465 - feature_engineering - ERROR - Filtered dataset missing at /home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/data/processed/filtered_esol.csv. Run 01_data_ingestion.py first.


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
2026-10-23 19:09:24,297 - INFO - === Sensitivity Analysis (Task T007, FR-006) ===
2026-10-23 19:09:24,297 - INFO - Grid resolutions: [10, 20, 30]

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
2026-10-23 19:09:24,486 - ERROR - No command provided to monitor.


- python -m pytest tests/contract/ -> rc=1
_t009_schemas.py::test_dataset_schema_exists_and_valid
FAILED tests/contract/test_t009_schemas.py::test_feature_matrix_schema_exists_and_valid
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
FAILED tests/contract/test_tda_schema.py::test_tda_schema_compliance - FileNo...
======================== 18 failed, 10 skipped in 1.00s ========================


- python -m pytest tests/unit/ -> rc=2
r-properties-from-top/code/__init__.py)
_________ ERROR collecting tests/unit/test_persistence_utils_sparse.py _________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/tests/unit/test_persistence_utils_sparse.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_persistence_utils_sparse.py:15: in <module>
    from utils.persistence_utils import (
E   ImportError: cannot import name 'check_memory_requirement' from 'utils.persistence_utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/utils/persistence_utils.py)
=========================== short test summary info ============================
ERROR tests/unit/test_data_ingestion.py
ERROR tests/unit/test_persistence_utils_sparse.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.73s ===============================



## Declared deliverables still missing

- data/processed/combined_features.csv
- data/processed/filtered_lipophilicity.csv
- data/processed/power_analysis_report.json
- data/processed/splits.json
- data/processed/topological_features_10x10.csv
- data/processed/traditional_features.csv
- data/raw/lipophilicity.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `deepchem` to the project's `requirements.txt` and `pip install deepchem`.
- **Verified**: this loads **4200** real records with fields: smiles, logP.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import deepchem as dc
# Load the Lipophilicity (Lipo) dataset with a simple featurizer
tasks, (train, valid, test), transformers = dc.molnet.load_lipo(featurizer='ECFP')
# Count total records across all splits
total = len(train) + len(valid) + len(test)
print(f"RECORDS={total}")
# The dataset provides SMILES strings as ids and experimental logP values as targets
fields = ['smiles', 'logP']
print('FIELDS=' + ','.join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/combined_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — IS a run-book command
    - `code/04_model_training.py` — IS a run-book command
    - `code/05_sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/combined_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_lipophilicity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/filtered_lipophilicity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/splits.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
    - `code/01_download_lipophilicity.py` — NOT invoked by the run-book
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
- `data/raw/lipophilicity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
    - `code/01_download_lipophilicity.py` — NOT invoked by the run-book
    - `code/generate_esol_raw.py` — NOT invoked by the run-book
    - `code/tests/test_dataset_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/lipophilicity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
