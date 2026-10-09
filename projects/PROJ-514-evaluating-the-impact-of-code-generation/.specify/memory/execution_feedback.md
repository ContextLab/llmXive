# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/main.py --step collect; python code/main.py --step analyze; python code/main.py --step analyze_stats; 2 command(s) failed: python -m pytest tests/unit/ -v (rc=2); python -m pytest tests/contract/ -v (rc=1); 7 declared deliverable(s) absent: data/intermediate/analysis_results.json; data/intermediate/sensitivity_analysis_report.json; data/intermediate/stat_results.json

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
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation/code/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-514-evaluating-the-impact-of-code-generation
configfile: pyproject.toml
plugins: platformdirs-4.12.4
collecting ... collected 72 items / 1 error

==================================== ERRORS ====================================
_____________ ERROR collecting tests/unit/test_setup_data_dirs.py ______________
tests/unit/test_setup_data_dirs.py:41: in <module>
    REQUIRED_DIRS = setup_module.REQUIRED_DIRS
E   AttributeError: module 'setup_data_dirs' has no attribute 'REQUIRED_DIRS'
=========================== short test summary info ============================
ERROR tests/unit/test_setup_data_dirs.py - AttributeError: module 'setup_data_dirs' has no attribute 'REQUIRED_DIRS'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.19s ===============================


- python -m pytest tests/contract/ -v -> rc=1
'
FAILED tests/contract/test_permutation_test_interface.py::test_bonferroni_correction - ModuleNotFoundError: No module named 'code_03_statistical_analysis_compare_distributions'
FAILED tests/contract/test_permutation_test_interface.py::test_confidence_interval - ModuleNotFoundError: No module named 'code_03_statistical_analysis_compare_distributions'
FAILED tests/contract/test_repo_selection.py::TestRepositorySelectionLogic::test_validate_criteria_age_fail - NameError: name 'timezone' is not defined
FAILED tests/contract/test_repo_selection.py::TestRepositorySelectionLogic::test_validate_criteria_stars_fail - NameError: name 'timezone' is not defined
FAILED tests/contract/test_repo_selection.py::TestRepositorySelectionLogic::test_validate_criteria_pass - NameError: name 'timezone' is not defined
FAILED tests/contract/test_repo_selection.py::TestRealOrMockImplementation::test_integration_select_repositories_meets_criteria - NameError: name 'timezone' is not defined
FAILED tests/contract/test_static_analysis_interface.py::test_interface_requires_valid_pmd_config - NameError: name 'List' is not defined
=================== 12 failed, 20 passed, 7 skipped in 0.26s ===================



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
    - `code/setup_project_structure.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
