# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/download.py --validate (rc=1); python code/preprocess.py (rc=1); python code/features.py (rc=1); 8 declared deliverable(s) absent: data/analysis/complexity_metrics.csv; data/analysis/raw_correlation_results.csv; data/analysis/resource_usage.json

## Failing / missing run-book commands

- python code/download.py --validate -> rc=1
2026-10-14 16:33:51,327 - download - INFO - Checking metadata availability at https://physionet.org/api/files/sleep-edfx/1.0.0/...
2026-10-14 16:33:52,483 - download - ERROR - HTTP error checking metadata: 404 Not Found
2026-10-14 16:33:52,484 - download - ERROR - Metadata check failed. Aborting.


- python code/preprocess.py -> rc=1


- python code/features.py -> rc=1


- python code/analysis.py -> rc=1
2026-10-14 16:33:53,334 - __main__ - INFO - Starting analysis pipeline.
2026-10-14 16:33:53,334 - __main__ - INFO - Starting input validation for analysis pipeline.
2026-10-14 16:33:53,334 - __main__ - ERROR - CRITICAL: Required data files are missing. Analysis cannot proceed.
Missing files:
  - cleaned_eeg_dir: data/processed/cleaned_eeg/
  - complexity_metrics: data/analysis/complexity_metrics.csv
  - fatigue_scores: data/processed/fatigue_scores.csv

Available files:


CRITICAL: Required data files are missing. Analysis cannot proceed.
Missing files:
  - cleaned_eeg_dir: data/processed/cleaned_eeg/
  - complexity_metrics: data/analysis/complexity_metrics.csv
  - fatigue_scores: data/processed/fatigue_scores.csv

Available files:


- python -m pytest tests/ -v -> rc=2
rt test summary info ============================
ERROR tests/test_features.py
ERROR tests/test_t012_preprocess.py
ERROR tests/integration/test_analysis.py
ERROR tests/integration/test_features.py
ERROR tests/integration/test_features_integration.py
ERROR tests/integration/test_preprocess.py
ERROR tests/integration/test_preprocess_artifacts.py
ERROR tests/unit/test_analysis.py
ERROR tests/unit/test_analysis_mode_failures.py
ERROR tests/unit/test_artifact_rejection.py
ERROR tests/unit/test_delta_scores.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_download_validation.py
ERROR tests/unit/test_edge_cases.py
ERROR tests/unit/test_edge_cases_integration.py
ERROR tests/unit/test_features_lzc.py
ERROR tests/unit/test_logging.py
ERROR tests/unit/test_missing_data.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_preprocess_artifacts.py
ERROR tests/unit/test_report.py
ERROR tests/unit/test_segment_length_validation.py
ERROR tests/unit/test_t014_segment_validation.py
ERROR tests/unit/test_validation_gate.py
!!!!!!!!!!!!!!!!!!! Interrupted: 24 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 5 warnings, 24 errors in 0.86s ========================



## Declared deliverables still missing

- data/analysis/complexity_metrics.csv
- data/analysis/raw_correlation_results.csv
- data/analysis/resource_usage.json
- data/analysis/vif_valid_predictors.json
- data/processed/exclusion_log.csv
- data/processed/fatigue_scores.csv
- data/processed/validation_report.json
- data/raw/download_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/complexity_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/collinearity.py` — NOT invoked by the run-book
    - `code/features.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/complexity_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/raw_correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/benjamini_hochberg.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/raw_correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/resource_usage.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/monitor.py` — NOT invoked by the run-book
    - `code/verify_memory.py` — NOT invoked by the run-book
    - `code/verify_runtime.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/resource_usage.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/vif_valid_predictors.json` is declared but was NOT written. Scripts referencing it:
    - `code/collinearity.py` — NOT invoked by the run-book
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/vif_valid_predictors.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/utils/logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/fatigue_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/extract_fatigue.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/fatigue_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/check_sample_size.py` — NOT invoked by the run-book
    - `code/download.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/download_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/check_sample_size.py` — NOT invoked by the run-book
    - `code/create_sample_verification.py` — NOT invoked by the run-book
    - `code/download.py` — IS a run-book command
    - `code/extract_fatigue.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/download_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
