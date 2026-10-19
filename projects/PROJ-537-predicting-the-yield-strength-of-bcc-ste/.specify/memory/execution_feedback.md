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
3 passed, 1 skipped, 11 errors in 0.43s



## Declared deliverables still missing

- data/results/output.json

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
