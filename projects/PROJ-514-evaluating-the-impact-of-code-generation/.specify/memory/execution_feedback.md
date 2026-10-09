# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/main.py --step collect; python code/main.py --step analyze; python code/main.py --step analyze_stats; 2 command(s) failed: python -m pytest tests/unit/ -v (rc=2); python -m pytest tests/contract/ -v (rc=2); 7 declared deliverable(s) absent: data/intermediate/analysis_results.json; data/intermediate/sensitivity_analysis_report.json; data/intermediate/stat_results.json

## Failing / missing run-book commands

- python code/main.py --step collect -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step analyze -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step analyze_stats -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step report -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -v -> rc=2
_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_validators.py:15: in <module>
    from utils.validators import (
code/utils/__init__.py:4: in <module>
    from .config import (
E   ImportError: cannot import name 'Config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/utils/config.py)
=========================== short test summary info ============================
ERROR tests/unit/test_data_models.py
ERROR tests/unit/test_pmd_utils.py
ERROR tests/unit/test_pmd_wrapper.py
ERROR tests/unit/test_setup_data_dirs.py
ERROR tests/unit/test_validators.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 0.49s ===============================


- python -m pytest tests/contract/ -v -> rc=2
t_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
code/.venv/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/contract/test_static_analysis_interface.py:26: in <module>
    from utils.data_models import SmellMetric
code/utils/__init__.py:4: in <module>
    from .config import (
E   ImportError: cannot import name 'Config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/utils/config.py)
=========================== short test summary info ============================
ERROR tests/contract/test_llm_generation.py
ERROR tests/contract/test_permutation_test_interface.py
ERROR tests/contract/test_static_analysis_interface.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 0.23s ===============================



## Declared deliverables still missing

- data/intermediate/analysis_results.json
- data/intermediate/sensitivity_analysis_report.json
- data/intermediate/stat_results.json
- data/intermediate/tasks.json
- data/processed/smell_metrics.csv
- data/raw/api_logs.json
- data/raw/manifest.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/intermediate/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_static_analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/02_static_analysis/parse_results.py` — NOT invoked by the run-book
    - `code/02_static_analysis/tool_validity_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/intermediate/sensitivity_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_statistical_analysis/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/sensitivity_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/intermediate/stat_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_statistical_analysis/compare_distributions.py` — NOT invoked by the run-book
    - `code/03_statistical_analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/04_reporting/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/stat_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/intermediate/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_collection/generate_llm_samples.py` — NOT invoked by the run-book
    - `code/setup_project_structure.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/smell_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_static_analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/03_statistical_analysis/compare_distributions.py` — NOT invoked by the run-book
    - `code/03_statistical_analysis/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/smell_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/api_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_collection/fetch_human_samples.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/api_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_collection/export_manifest.py` — NOT invoked by the run-book
    - `code/02_static_analysis/parse_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
