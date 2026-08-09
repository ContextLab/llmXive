# API Reference

## Utility Modules

### `utils/config_loader.py`
- `load_config()`: Load and return the configuration from `code/config.yaml`.
- `validate_ivt_config()`: Validate that either I-VT or I-DT parameters are present.
- `get_validated_config()`: Return a validated configuration object.

### `utils/data_loading.py`
- `fetch_eye_tracking_data()`: Download the raw dataset from the configured URL.
- `compute_sha256()`: Compute SHA-256 checksum of a file.
- `validate_eye_tracking_schema()`: Verify the downloaded file contains required columns.

### `utils/fixation_detection.py`
- `detect_fixations_ivt()`: Apply I-VT fixation detection algorithm.
- `detect_fixations_idt()`: Apply I-DT fixation detection algorithm.
- `process_gaze_data()`: Process raw gaze data and return fixation events.

### `utils/roi_mapping.py`
- `is_point_in_roi()`: Check if a gaze point falls within a defined ROI.
- `map_gaze_to_rois()`: Assign ROI labels to all gaze points.

## Data Processing Scripts

### `01_extract_empirical_outcome.py`
- `extract_outcomes()`: Extract `belief_rating` and `headline_text` from raw data.
- `verify_schema()`: Validate that required columns exist.

### `02_preprocess_gaze.py`
- `preprocess_gaze_data()`: Apply fixation detection, ROI mapping, and filtering.
- `handle_edge_cases()`: Manage missing ROIs and zero-fixation cases.

### `03_valence_calculation.py`
- `calculate_nrc_coverage()`: Compute NRC lexicon coverage for headlines.
- `get_nrc_valence()`: Calculate valence using NRC lexicon.
- `get_vader_valence()`: Calculate valence using VADER lexicon.

### `04_data_merge.py`
- `merge_datasets()`: Join gaze, empirical, and valence datasets.
- `apply_outlier_capping()`: Cap `cognitive_reflection_score` at 1st and 99th percentiles.

### `05_regression_analysis.py`
- `run_mixed_effects_regression()`: Fit the three-way interaction model.
- `apply_multiple_comparison_correction()`: Apply Holm-Bonferroni correction.

## Robustness Modules

### `robustness_runner.py`
- `run_robustness_regression()`: Execute regression with custom fixation threshold.

### `robustness_sweep.py`
- `run_sweep()`: Iterate over fixation thresholds and collect results.

### `robustness_stability_check.py`
- `analyze_stability()`: Verify consistency of effect direction and significance.

## Output Schemas

### `data/derived/empirical_outcomes.csv`
- `participant_id`, `headline_id`, `belief_rating`, `headline_text`

### `data/derived/preprocessed_gaze.csv`
- `participant_id`, `headline_id`, `fixation_duration`, `roi_type`

### `data/derived/valence_scores.csv`
- `headline_id`, `valence_score`

### `data/derived/merged_dataset_full.csv`
- All columns from above plus `cognitive_reflection_score`, `headline_length`, `total_fixation_duration`

### `data/derived/regression_results.csv`
- `term`, `coefficient`, `std_error`, `p_value`, `p_adj`, `ci_lower`, `ci_upper`

### `output/causal_framing_statement.txt`
- Human-readable summary of findings with dynamic effect sizes and significance levels.