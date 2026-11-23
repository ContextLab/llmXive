# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/experiment/experiment.py --mode mock --participants 3 (rc=1); python code/generation/doc_pipeline.py  --repo  --commit abc123def456  --output data/processed/docs/repo_docs.md (rc=1); python code/analysis/stats_runner.py  --input data/processed/task_logs_anon.json  --output data/processed/analysis_results.json (rc=1); 10 declared deliverable(s) absent: data/processed/centered_covariates.json; data/processed/cleaned_dataset.csv; data/processed/validation_report.json

## Failing / missing run-book commands

- python code/experiment/experiment.py --mode mock --participants 3 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/experiment/experiment.py", line 24, in <module>
    from data_collection import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/data_collection.py", line 17, in <module>
    logging.FileHandler('data/logs/data_collection.log')
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/data/logs/data_collection.log'
- python code/generation/doc_pipeline.py  --repo  --commit abc123def456  --output data/processed/docs/repo_docs.md -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/generation/doc_pipeline.py", line 36, in <module>
    logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'doc_pipeline.log'))
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/logs/doc_pipeline.log'
- python code/analysis/stats_runner.py  --input data/processed/task_logs_anon.json  --output data/processed/analysis_results.json -> rc=1
    2026-08-18 13:23:40,403 - ERROR - Secondary path execution failed: Input data file not found: data/processed/task_logs_anon.json. Ensure T032 (cleaning pipeline) has run.
- python code/utils/logging.py --track  --command "python code/analysis/stats_runner.py..." -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/utils/logging.py", line 15, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/utils/logging.py", line 21, in <module>
    from code.utils.monitor import ActiveMonitor
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/utils/monitor.py", line 10, in <module>
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ^^^^^^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'basicConfig' (most likely due to a circular import)

## Declared deliverables still missing

- data/processed/centered_covariates.json
- data/processed/cleaned_dataset.csv
- data/processed/validation_report.json
- data/raw/doc_quality_scores.json
- data/raw/participant_logs.json
- data/raw/repo_covariates.json
- data/raw/repo_matching_report.json
- data/raw/repo_metrics.json
- data/raw/repo_selection_rubric.json
- data/reports/sensitivity_decision_tree_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/centered_covariates.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/ancova_strategy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/centered_covariates.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/run_cleaning_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/ancova_strategy.py` — NOT invoked by the run-book
    - `code/analysis/stats_runner.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_schema_validation.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/run_cleaning_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/doc_quality_scores.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_doc_quality_rubric.py` — NOT invoked by the run-book
    - `code/analysis/ancova_strategy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/doc_quality_scores.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/participant_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_schema_validation.py` — NOT invoked by the run-book
    - `code/data_collection.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/run_cleaning_pipeline.py` — NOT invoked by the run-book
    - `code/experiment/experiment.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/participant_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_covariates.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_covariate_collection.py` — NOT invoked by the run-book
    - `code/analysis/ancova_strategy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/repo_covariates.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_matching_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_matching_report.py` — NOT invoked by the run-book
    - `code/run_covariate_collection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/repo_matching_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_metrics_collection.py` — NOT invoked by the run-book
    - `code/run_matching_report.py` — NOT invoked by the run-book
    - `code/run_rubric_and_metrics.py` — NOT invoked by the run-book
    - `code/repo_metrics_runner.py` — NOT invoked by the run-book
    - `code/run_covariate_collection.py` — NOT invoked by the run-book
    - `code/analysis/ancova_strategy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/repo_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_selection_rubric.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_rubric_and_metrics.py` — NOT invoked by the run-book
    - `code/repo_metrics_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/repo_selection_rubric.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/reports/sensitivity_decision_tree_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats_runner.py` — IS a run-book command
  Make ONE of these WRITE `data/reports/sensitivity_decision_tree_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
