# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/run_all.py (rc=1); python -m pytest -q tests/contract/ (rc=1); 1 declared deliverable(s) absent: data/results/output.json

## Failing / missing run-book commands

- python code/run_all.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste/code/run_all.py", line 46, in <module>
    from config import ensure_dirs, CONFIG
ImportError: cannot import name 'ensure_dirs' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste/config.py)

- python -m pytest -q tests/contract/ -> rc=1
/test_merged_schema.py:43: AttributeError
=========================== short test summary info ============================
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_file_exists
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_required_columns_present
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_no_null_yield_strength
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_no_null_shear_modulus
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_positive_yield_strength
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_positive_shear_modulus
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_minimum_row_count
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_composition_columns_format
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_data_types
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_bcc_filter_applied
ERROR tests/contract/test_merged_schema.py::TestMergedDatasetSchema::test_schema_conformity
3 passed, 1 skipped, 11 errors in 0.44s



## Declared deliverables still missing

- data/results/output.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `matminer` to the project's `requirements.txt` and `pip install matminer`.
- **Verified**: this loads **1181** real records with fields: material_id, formula, nsites, space_group, volume, structure, elastic_anisotropy, G_Reuss, G_VRH, G_Voigt, K_Reuss, K_VRH, K_Voigt, poisson_ratio, compliance_tensor, elastic_tensor, elastic_tensor_original, cif, kpoint_density, poscar.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
from matminer.datasets import load_dataset

df = load_dataset("elastic_tensor_2015")
print(f"RECORDS={len(df)}")
if not df.empty:
    print("FIELDS=" + ",".join(df.columns))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/output.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/ingestion/fetch_dft.py` — NOT invoked by the run-book
    - `code/ingestion/fetch_experimental.py` — NOT invoked by the run-book
    - `code/ingestion/finalize_dataset.py` — NOT invoked by the run-book
    - `code/ingestion/generate_checksums.py` — NOT invoked by the run-book
    - `code/ingestion/merge_and_filter.py` — NOT invoked by the run-book
    - `code/ingestion/update_state.py` — NOT invoked by the run-book
    - `code/interpretability/bootstrap_stability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/output.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
