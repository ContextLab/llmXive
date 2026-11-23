# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py --task acquisition (rc=1); python code/main.py (rc=1); python -m pytest tests/ -v (rc=2); 4 declared deliverable(s) absent: data/processed/cleaned_dataset.csv; data/processed/model_results.json; data/processed/model_results_summary.csv

## Failing / missing run-book commands

- python code/main.py --task acquisition -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-160-investigating-the-impact-of-early-life-s/code/main.py", line 30, in <module>
    from code.analysis.aggregate_robustness import main as aggregate_robustness_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-160-investigating-the-impact-of-early-life-s/code/analysis/aggregate_robustness.py", line 95, in <module>
    sens_results: List[Dict[str, Any]],
                  ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-160-investigating-the-impact-of-early-life-s/code/main.py", line 30, in <module>
    from code.analysis.aggregate_robustness import main as aggregate_robustness_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-160-investigating-the-impact-of-early-life-s/code/analysis/aggregate_robustness.py", line 95, in <module>
    sens_results: List[Dict[str, Any]],
                  ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

- python -m pytest tests/ -v -> rc=2
dules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_results_associational.py:9: in <module>
    from code.analysis.results import StatisticalModel, AnalysisResult, extract_model_results, save_analysis_results
E   ImportError: cannot import name 'extract_model_results' from 'code.analysis.results' (/home/runner/work/llmXive/llmXive/projects/PROJ-160-investigating-the-impact-of-early-life-s/code/analysis/results.py)
=========================== short test summary info ============================
ERROR tests/integration/test_acquisition.py - NameError: name 'List' is not d...
ERROR tests/integration/test_robustness.py
ERROR tests/setup/test_project_init.py
ERROR tests/unit/test_logging.py
ERROR tests/unit/test_modeling.py
ERROR tests/unit/test_preprocessing.py
ERROR tests/unit/test_preprocessing_t015.py
ERROR tests/unit/test_results_associational.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 8 errors in 1.25s ===============================



## Declared deliverables still missing

- data/processed/cleaned_dataset.csv
- data/processed/model_results.json
- data/processed/model_results_summary.csv
- data/processed/robustness_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/modeling.py` — NOT invoked by the run-book
    - `code/analysis/robustness.py` — NOT invoked by the run-book
    - `code/analysis/save_results.py` — NOT invoked by the run-book
    - `code/data/generate_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/data/streaming_loader.py` — NOT invoked by the run-book
    - `code/validation/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_robustness.py` — NOT invoked by the run-book
    - `code/analysis/modeling.py` — NOT invoked by the run-book
    - `code/analysis/save_results.py` — NOT invoked by the run-book
    - `code/validation/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/save_results.py` — NOT invoked by the run-book
    - `code/validation/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_robustness.py` — NOT invoked by the run-book
    - `code/analysis/robustness.py` — NOT invoked by the run-book
    - `code/validation/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
