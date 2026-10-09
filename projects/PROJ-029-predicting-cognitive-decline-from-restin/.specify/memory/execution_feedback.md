# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 command(s) failed: python code/01_download_and_filter.py (rc=1); python code/02_preprocess_and_parcellate.py (rc=1); python code/03_compute_graph_metrics.py (rc=5); 8 declared deliverable(s) absent: data/processed/decision_threshold_report.json; data/processed/eligible_subjects.csv; data/processed/graph_metrics.csv

## Failing / missing run-book commands

- python code/01_download_and_filter.py -> rc=1

ERROR: huggingface_hub is required for real data fetch.

- python code/02_preprocess_and_parcellate.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/02_preprocess_and_parcellate.py", line 31, in <module>
    from nilearn.input_data import NiftiLabelsMasker
ModuleNotFoundError: No module named 'nilearn.input_data'

- python code/03_compute_graph_metrics.py -> rc=5


- python code/04_train_model.py -> rc=3


- python code/05_evaluate_model.py -> rc=1
Error: Missing required file: data/processed/model.pkl


- python code/06_permutation_test.py -> rc=1


- python code/07_sensitivity_analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/07_sensitivity_analysis.py", line 142, in <module>
    @log_operation("decision_threshold_sweep")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable

- python code/08_collinearity_check.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/08_collinearity_check.py", line 81, in <module>
    @log_operation("collinearity_check")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable

- python -m pytest tests/unit/ -> rc=2
6: in <module>
    from validate_quickstart import run_script, check_artifacts, EXPECTED_ARTIFACTS
E   ImportError: cannot import name 'EXPECTED_ARTIFACTS' from 'validate_quickstart' (/home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/code/validate_quickstart.py)
=========================== short test summary info ============================
ERROR tests/unit/test_collinearity_check.py
ERROR tests/unit/test_compute_graph_metrics.py
ERROR tests/unit/test_compute_graph_metrics_parallel.py
ERROR tests/unit/test_config_env.py
ERROR tests/unit/test_download_and_filter.py
ERROR tests/unit/test_download_filter.py
ERROR tests/unit/test_graph_metrics.py - Failed: compute_subject_metrics not ...
ERROR tests/unit/test_graph_metrics_parallel.py
ERROR tests/unit/test_graph_metrics_performance.py
ERROR tests/unit/test_nested_cv.py
ERROR tests/unit/test_permutation_runtime.py
ERROR tests/unit/test_security_scan.py
ERROR tests/unit/test_train_model.py
ERROR tests/unit/test_validate_quickstart.py
!!!!!!!!!!!!!!!!!!! Interrupted: 14 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 14 errors in 2.40s ==============================


- python -m pytest tests/integration/ -> rc=2
on/test_ci_memory_profiler.py:20: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

tests/integration/test_ci_memory_profiler.py:106
  /home/runner/work/llmXive/llmXive/projects/PROJ-029-predicting-cognitive-decline-from-restin/tests/integration/test_ci_memory_profiler.py:106: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_compute_graph_metrics.py
ERROR tests/integration/test_filtering.py
ERROR tests/integration/test_graph_metrics_pipeline.py
ERROR tests/integration/test_model_training.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 4 errors in 0.62s =========================



## Declared deliverables still missing

- data/processed/decision_threshold_report.json
- data/processed/eligible_subjects.csv
- data/processed/graph_metrics.csv
- data/processed/label_sensitivity_report.json
- data/processed/labels.csv
- data/processed/performance_report.json
- data/processed/permutation_results.json
- data/processed/processed_subjects.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/decision_threshold_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/decision_threshold_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/eligible_subjects.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_download_and_filter.py` — IS a run-book command
    - `code/02_preprocess_and_parcellate.py` — IS a run-book command
    - `code/03_compute_graph_metrics.py` — IS a run-book command
    - `code/04_train_model.py` — IS a run-book command
    - `code/05_evaluate_model.py` — IS a run-book command
    - `code/06_permutation_test.py` — IS a run-book command
    - `code/07_sensitivity_analysis.py` — IS a run-book command
    - `code/code_04_train_model_wrapper.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/eligible_subjects.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graph_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_compute_graph_metrics.py` — IS a run-book command
    - `code/04_train_model.py` — IS a run-book command
    - `code/05_evaluate_model.py` — IS a run-book command
    - `code/06_permutation_test.py` — IS a run-book command
    - `code/07_sensitivity_analysis.py` — IS a run-book command
    - `code/08_collinearity_check.py` — IS a run-book command
    - `code/08_plasticity_feature_engineering.py` — NOT invoked by the run-book
    - `code/12_memory_profiler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graph_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/label_sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/07_sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/label_sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/labels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_data_gate.py` — NOT invoked by the run-book
    - `code/02_preprocess_and_parcellate.py` — IS a run-book command
    - `code/04_train_model.py` — IS a run-book command
    - `code/05_evaluate_model.py` — IS a run-book command
    - `code/06_permutation_test.py` — IS a run-book command
    - `code/07_sensitivity_analysis.py` — IS a run-book command
    - `code/09_generate_report.py` — IS a run-book command
    - `code/11_external_outcome_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/labels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_evaluate_model.py` — IS a run-book command
    - `code/09_generate_report.py` — IS a run-book command
    - `code/10_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/permutation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/06_permutation_test.py` — IS a run-book command
    - `code/09_generate_report.py` — IS a run-book command
    - `code/10_verify_success_criteria.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/permutation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/processed_subjects.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocess_and_parcellate.py` — IS a run-book command
    - `code/03_compute_graph_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/processed_subjects.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
