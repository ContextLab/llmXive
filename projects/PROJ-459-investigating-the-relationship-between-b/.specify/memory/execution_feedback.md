# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py --step download_and_validate (rc=1); python -m pytest tests/contract/ (rc=2); python -m pytest tests/unit/ (rc=2); 1 declared deliverable(s) absent: data/derived/final_results.csv

## Failing / missing run-book commands

- python code/main.py --step download_and_validate -> rc=1
/ds000030
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 243, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 220, in main
    step_download_and_validate(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 70, in step_download_and_validate
    check_data_integrity(output_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/validate.py", line 200, in check_data_integrity
    participants_path = check_participants_file(data_dir)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/validate.py", line 41, in check_participants_file
    raise DataValidationError(
data.validate.DataValidationError: participants.tsv not found in /home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/data/raw/ds000030

- python -m pytest tests/contract/ -> rc=2
igrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    @validator("r")

code/data/models.py:154
  /home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/models.py:154: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    @validator("p_raw", "p_adj")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/contract/test_data_validation.py
ERROR tests/contract/test_metric_schema.py - pydantic.errors.PydanticUserErro...
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 7 warnings, 2 errors in 0.48s =========================


- python -m pytest tests/unit/ -> rc=2
dev/2.14/migration/
    @validator("r")

code/data/models.py:154
  /home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/models.py:154: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    @validator("p_raw", "p_adj")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_config.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_metrics.py - NameError: name 'Any' is not defined
ERROR tests/unit/test_sensitivity_report.py - pydantic.errors.PydanticUserErr...
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_stats_null_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 7 warnings, 7 errors in 0.68s =========================



## Declared deliverables still missing

- data/derived/final_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/final_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/final_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
