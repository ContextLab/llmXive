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
================================ ERRORS ====================================
___________ ERROR collecting tests/contract/test_data_validation.py ____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/tests/contract/test_data_validation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_data_validation.py:13: in <module>
    from data.validate import check_behavioral_variables, DataValidationError
E   ImportError: cannot import name 'check_behavioral_variables' from 'data.validate' (/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/data/validate.py)
=========================== short test summary info ============================
ERROR tests/contract/test_data_validation.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.60s ===============================


- python -m pytest tests/unit/ -> rc=2
.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_stats_null_validation.py:4: in <module>
    from analysis.stats import run_null_distribution_validation
code/analysis/stats.py:3: in <module>
    from scipy.stats import spearmanr, power
E   ImportError: cannot import name 'power' from 'scipy.stats' (/home/runner/work/llmXive/llmXive/projects/PROJ-459-investigating-the-relationship-between-b/code/.venv/lib/python3.11/site-packages/scipy/stats/__init__.py)
=========================== short test summary info ============================
ERROR tests/unit/test_atlas.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_metrics.py - NameError: name 'Any' is not defined
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_stats_null_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 0.84s ===============================



## Declared deliverables still missing

- data/derived/final_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/final_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/final_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
