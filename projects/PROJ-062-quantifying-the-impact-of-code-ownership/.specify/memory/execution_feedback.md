# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/contract/ (rc=1); 3 declared deliverable(s) absent: data/results/final_report.json; data/results/sensitivity_pvalue.csv; data/results/sensitivity_rho.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-062-quantifying-the-impact-of-code-ownership/code/main.py", line 16, in <module>
    from utils.memory_utils import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-062-quantifying-the-impact-of-code-ownership/code/utils/memory_utils.py", line 13, in <module>
    import psutil
ModuleNotFoundError: No module named 'psutil'

- python -m pytest tests/contract/ -> rc=1
.exists

tests/contract/test_data_schema.py:28: AssertionError
=========================== short test summary info ============================
ERROR tests/contract/test_data_schema.py::test_ownership_schema_has_required_fields
ERROR tests/contract/test_data_schema.py::test_ownership_schema_field_types
ERROR tests/contract/test_data_schema.py::test_ownership_schema_has_required_constraint
ERROR tests/contract/test_data_schema.py::test_output_schema_structure - Asse...
ERROR tests/contract/test_data_schema.py::test_output_schema_contains_metrics
ERROR tests/contract/test_data_schema.py::test_sample_ownership_data_validates
ERROR tests/contract/test_data_schema.py::test_sample_output_data_validates
ERROR tests/contract/test_data_schema.py::test_schema_files_are_valid_yaml - ...
ERROR tests/contract/test_data_schema.py::test_ownership_schema_has_description
ERROR tests/contract/test_data_schema.py::test_output_schema_has_description
ERROR tests/contract/test_data_schema.py::test_ownership_schema_properties_have_descriptions
ERROR tests/contract/test_data_schema.py::test_schema_versioning - AssertionE...
============================== 12 errors in 0.11s ==============================



## Declared deliverables still missing

- data/results/final_report.json
- data/results/sensitivity_pvalue.csv
- data/results/sensitivity_rho.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/verify_associational_framing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_pvalue.csv` is declared but was NOT written. Scripts referencing it:
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_pvalue.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_rho.csv` is declared but was NOT written. Scripts referencing it:
    - `code/statistical_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_rho.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
