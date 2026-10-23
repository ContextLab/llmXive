# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/persistence_images_10x10.csv, data/processed/power_analysis_report.json, data/processed/scaffold_counts.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/persistence_images_10x10.csv, data/processed/power_analysis_report.json, data/processed/scaffold_counts.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/06_feature_importance.py; python code/06_diagnostics.py; 7 command(s) failed: python code/01_data_ingestion.py --source lipophilicity (rc=1); python code/03_feature_engineering.py (rc=1); python code/04_model_training.py (rc=1); 3 declared deliverable(s) absent: data/processed/combined_features.csv; data/processed/filtered_lipophilicity.csv; data/processed/traditional_features.csv

## Failing / missing run-book commands

- python code/01_data_ingestion.py --source lipophilicity -> rc=1
e parsing: <rdkit.Chem.rdchem.Mol
[17:33:20] SMILES Parse Error: check for mistakes around position 1:
[17:33:20] <rdkit.Chem.rdchem.Mol
[17:33:20] ^
[17:33:20] SMILES Parse Error: Failed parsing SMILES '<rdkit.Chem.rdchem.Mol' for input: '<rdkit.Chem.rdchem.Mol'
[17:33:20] SMILES Parse Error: syntax error while parsing: <rdkit.Chem.rdchem.Mol
[17:33:20] SMILES Parse Error: check for mistakes around position 1:
[17:33:20] <rdkit.Chem.rdchem.Mol
[17:33:20] ^
[17:33:20] SMILES Parse Error: Failed parsing SMILES '<rdkit.Chem.rdchem.Mol' for input: '<rdkit.Chem.rdchem.Mol'
[17:33:20] SMILES Parse Error: syntax error while parsing: <rdkit.Chem.rdchem.Mol
[17:33:20] SMILES Parse Error: check for mistakes around position 1:
[17:33:20] <rdkit.Chem.rdchem.Mol
[17:33:20] ^
[17:33:20] SMILES Parse Error: Failed parsing SMILES '<rdkit.Chem.rdchem.Mol' for input: '<rdkit.Chem.rdchem.Mol'
[17:33:20] SMILES Parse Error: syntax error while parsing: <rdkit.Chem.rdchem.Mol
[17:33:20] SMILES Parse Error: check for mistakes around position 1:
[17:33:20] <rdkit.Chem.rdchem.Mol
[17:33:20] ^
[17:33:20] SMILES Parse Error: Failed parsing SMILES '<rdkit.Chem.rdchem.Mol' for input: '<rdkit.Chem.rdchem.Mol'

- python code/03_feature_engineering.py -> rc=1
led: 'molecule_id'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/03_feature_engineering.py", line 291, in main
    run_feature_engineering()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/03_feature_engineering.py", line 221, in run_feature_engineering
    df_trad = compute_traditional_descriptors(df_filtered, valid_ids, logger)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/03_feature_engineering.py", line 122, in compute_traditional_descriptors
    out["molecule_id"] = out["molecule_id"].astype(str)
                         ~~~^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 4102, in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/indexes/range.py", line 417, in get_loc
    raise KeyError(key)
KeyError: 'molecule_id'


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
2026-10-23 17:33:25,007 - INFO - === Sensitivity Analysis (Task T007, FR-006) ===
2026-10-23 17:33:25,007 - INFO - Grid resolutions: [10, 20, 30]

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
2026-10-23 17:33:25,167 - ERROR - No command provided to monitor.


- python -m pytest tests/contract/ -> rc=1
t_persistence_images_10x10_non_negative __________________
tests/contract/test_tda_10x10.py:65: in test_persistence_images_10x10_non_negative
    pytest.fail("No image columns found.")
E   Failed: No image columns found.
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
=================== 10 failed, 12 passed, 6 skipped in 1.17s ===================


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
============================== 2 errors in 0.63s ===============================



## Declared deliverables still missing

- data/processed/combined_features.csv
- data/processed/filtered_lipophilicity.csv
- data/processed/traditional_features.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `deepchem` to the project's `requirements.txt` and `pip install deepchem`.
- **Verified**: this loads **1128** real records with fields: smiles, exp.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import deepchem as dc

tasks, datasets, transformers = dc.molnet.load_delaney(featurizer='ECFP', split='random')
train, valid, test = datasets

def _count(ds):
    if hasattr(ds, 'X') and hasattr(ds.X, 'shape'):
        return ds.X.shape[0]
    return len(ds)

total = sum(_count(ds) for ds in (train, valid, test))
print(f"RECORDS={total}")

fields = []
if any(hasattr(ds, 'ids') and ds.ids is not None for ds in (train, valid, test)):
    fields.append('smiles')
if tasks:
    fields.append('exp')
print(f"FIELDS={','.join(fields)}")
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
- `data/processed/traditional_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — IS a run-book command
    - `code/04_model_training.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/traditional_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
