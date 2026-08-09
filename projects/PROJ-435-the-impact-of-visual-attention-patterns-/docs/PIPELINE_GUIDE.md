# Pipeline Execution Guide

## Overview
This document describes the step-by-step execution of the analysis pipeline, including dependencies, expected outputs, and troubleshooting tips.

## Execution Order
The pipeline must be executed in the following order:

1. **T005**: Fetch and validate raw data
 - Script: `code/utils/data_loading.py`
 - Output: `data/raw/eye_tracking_raw.parquet`
 - State: `state/data_hashes.json`

2. **T004**: Validate dataset schema
 - Script: `code/utils/validate_dataset_schema.py`
 - Input: `data/raw/eye_tracking_raw.parquet`
 - Output: `state/schema_validation.json`

3. **T004b**: Extract empirical outcomes
 - Script: `code/01_extract_empirical_outcome.py`
 - Input: `data/raw/eye_tracking_raw.parquet`
 - Output: `data/derived/empirical_outcomes.csv`

4. **T018**: Preprocess gaze data
 - Script: `code/02_preprocess_gaze.py`
 - Input: `data/raw/eye_tracking_raw.parquet`
 - Output: `data/derived/preprocessed_gaze.csv`, `output/exclusion_log.txt`

5. **T007**: Generate data quality report
 - Script: `code/02_data_quality_report.py`
 - Input: `output/exclusion_log.txt`, `data/derived/preprocessed_gaze.csv`
 - Output: `output/data_quality_report.csv`

6. **T021**: Calculate valence scores
 - Script: `code/03_valence_calculation.py`
 - Input: `data/derived/empirical_outcomes.csv`
 - Output: `data/derived/valence_scores.csv`
 - State: `state/runtime_events.json` (if lexicon switch occurs)

7. **T023**: Merge datasets
 - Script: `code/04_data_merge.py`
 - Input: `data/derived/preprocessed_gaze.csv`, `data/derived/empirical_outcomes.csv`, `data/derived/valence_scores.csv`
 - Output: `data/derived/merged_dataset_full.csv`

8. **T024**: Regression analysis
 - Script: `code/05_regression_analysis.py`
 - Input: `data/derived/merged_dataset_full.csv`
 - Output: `data/derived/regression_results.csv`

9. **T017**: Measure runtime
 - Script: `code/06_measure_runtime.py`
 - Output: `state/runtime_metrics.json`

10. **T028**: Generate causal framing statement
 - Script: `code/07_generate_causal_framing.py`
 - Input: `data/derived/regression_results.csv`
 - Output: `output/causal_framing_statement.txt`

11. **T033**: Robustness sweep (optional)
 - Script: `code/robustness_sweep.py`
 - Input: `data/derived/merged_dataset_full.csv`, `code/robustness_runner.py`
 - Output: `data/derived/robustness_report.csv`

12. **T039**: Stability check
 - Script: `code/robustness_stability_check.py`
 - Input: `data/derived/robustness_report.csv`
 - Output: `output/stability_check.json`

## Troubleshooting
- **Schema validation fails**: Check that `data/raw/eye_tracking_raw.parquet` contains required columns (`headline_text`, `belief_rating`, `cognitive_reflection_score`, `fixation_duration`) and ROI definitions.
- **Valence calculation fails**: Ensure NRC lexicon is accessible; if coverage < 50%, the script will automatically switch to VADER.
- **Regression model fails**: Verify that `merged_dataset_full.csv` contains all required columns and that outlier capping has been applied.
- **Runtime exceeds limit**: The pipeline is designed to complete within 300 minutes. If exceeded, check for infinite loops or inefficient operations in preprocessing steps.

## Logging
All scripts log to `output/pipeline.log`. Critical events are also logged to `output/exclusion_log.txt` and `state/runtime_events.json`.
