# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/main.py --step download_and_validate (rc=1); python code/main.py --step preprocess (rc=1); python code/main.py --step compute_metrics (rc=1); 1 declared deliverable(s) absent: data/derived/final_results.csv

## Failing / missing run-book commands

- python code/main.py --step download_and_validate -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 20, in <module>
    from data.preprocess import run_fmriprep, extract_time_series
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/preprocess.py", line 20, in <module>
    from utils.env_config import check_memory_limit, set_runtime_cap
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/utils/env_config.py", line 140, in <module>
    def get_env_config() -> Dict[str, any]:
                            ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/main.py --step preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 20, in <module>
    from data.preprocess import run_fmriprep, extract_time_series
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/preprocess.py", line 20, in <module>
    from utils.env_config import check_memory_limit, set_runtime_cap
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/utils/env_config.py", line 140, in <module>
    def get_env_config() -> Dict[str, any]:
                            ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/main.py --step compute_metrics -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 20, in <module>
    from data.preprocess import run_fmriprep, extract_time_series
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/preprocess.py", line 20, in <module>
    from utils.env_config import check_memory_limit, set_runtime_cap
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/utils/env_config.py", line 140, in <module>
    def get_env_config() -> Dict[str, any]:
                            ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/main.py --step analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 20, in <module>
    from data.preprocess import run_fmriprep, extract_time_series
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/preprocess.py", line 20, in <module>
    from utils.env_config import check_memory_limit, set_runtime_cap
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/utils/env_config.py", line 140, in <module>
    def get_env_config() -> Dict[str, any]:
                            ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/main.py --step visualize -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/main.py", line 20, in <module>
    from data.preprocess import run_fmriprep, extract_time_series
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/preprocess.py", line 20, in <module>
    from utils.env_config import check_memory_limit, set_runtime_cap
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/utils/env_config.py", line 140, in <module>
    def get_env_config() -> Dict[str, any]:
                            ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

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
======================== 7 warnings, 2 errors in 0.49s =========================


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
======================== 7 warnings, 7 errors in 0.72s =========================



## Declared deliverables still missing

- data/derived/final_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/final_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/final_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
