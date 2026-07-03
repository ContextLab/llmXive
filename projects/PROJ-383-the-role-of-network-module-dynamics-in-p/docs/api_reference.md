# API Reference: Network Module Dynamics Pipeline

This document provides a reference for the core modules and functions used in the pipeline.

## Ingestion Module

### `code/ingestion/download_hcp.py`

Handles downloading data from OpenNeuro ds001734.

- `get_dataset_files()`: Retrieves the list of available files from the dataset.
- `filter_subject_files(files, subject_ids)`: Filters files for specific subjects.
- `download_file(url, dest_path)`: Downloads a single file.
- `download_subject_data(subject_id, dest_dir)`: Downloads all data for a subject.
- `main()`: Entry point for the script.

### `code/ingestion/preprocess.py`

Handles motion scrubbing, regression, and subject exclusion.

- `calculate_mean_fd(fd_series)`: Computes mean Framewise Displacement.
- `check_subject_exclusion(subject_id, mean_fd, threshold)`: Determines if a subject should be excluded.
- `process_subject_exclusions(subjects, threshold)`: Processes a list of subjects, logging exclusions.
- `scrub_and_regression(timeseries, motion_params, fd_series)`: Scrubs high-motion time points and regresses out motion.
- `calculate_fd_series(motion_params)`: Calculates the FD time series from motion parameters.
- `main()`: Entry point for the script.

### `code/ingestion/consolidate_data.py`

Merges processed fMRI data with behavioral scores.

- `load_scrubbed_timeseries(path)`: Loads cleaned time series.
- `load_behavioral_scores(path)`: Loads 2-back accuracy scores.
- `load_motion_params(path)`: Loads motion parameters for reference.
- `merge_datasets(timeseries_df, behavior_df)`: Combines datasets on subject ID.
- `validate_consolidated_data(df)`: Ensures data integrity.
- `main()`: Entry point.

### `code/ingestion/validate_source.py`

Validates the availability of the OpenNeuro dataset.

- `check_dataset_availability(dataset_id)`: Checks if a dataset exists on OpenNeuro.
- `verify_dataset_structure(dataset_id)`: Verifies expected file structure.
- `validate_source(dataset_id)`: Main validation logic.
- `main()`: Entry point; exits with error if validation fails.

### `code/ingestion/logging_integration.py`

Manages logging for ingestion events.

- `log_missing_behavioral_scores(subject_id)`: Logs subjects missing behavior data.
- `log_excessive_motion(subject_id, fd)`: Logs subjects excluded for motion.
- `log_subject_processing(subject_id, status)`: Logs processing status.
- `get_exclusion_summary()`: Returns a summary of exclusions.
- `main()`: Entry point.

## Analysis Module

### `code/analysis/dynamic_connectivity.py`

Computes sliding window connectivity and flexibility metrics.

- `load_scrubbed_timeseries(path)`: Loads preprocessed time series.
- `generate_sliding_windows(timeseries, window_size, step_size)`: Creates sliding windows.
- `compute_correlation_matrix(window_data)`: Computes functional connectivity matrix for a window.
- `compute_dynamic_connectivity(timeseries, window_size, step_size)`: Computes connectivity over all windows.
- `compute_flexibility_metric(partitions)`: Calculates node switching probability (flexibility).
- `process_subject_dynamic_connectivity(subject_id, timeseries, window_size, step_size)`: Full pipeline for one subject.
- `save_dynamic_connectivity_results(subject_id, flexibility, partitions, output_path)`: Saves results.
- `main()`: Entry point.

### `code/analysis/output_flexibility_scores.py`

Aggregates and outputs flexibility scores.

- `load_subject_flexibility_results(subject_id, base_path)`: Loads results for a subject.
- `aggregate_flexibility_scores(results_dict)`: Combines results into a single dataframe.
- `save_flexibility_scores(df, output_path)`: Saves to Parquet.
- `get_available_subjects(base_path)`: Lists subjects with results.
- `main()`: Entry point.

### `code/analysis/statistics.py`

Performs statistical testing.

- `load_flexibility_scores(path)`: Loads flexibility scores.
- `load_behavioral_scores(path)`: Loads behavioral data.
- `merge_analysis_data(flex_df, behavior_df, motion_df)`: Merges for analysis.
- `compute_partial_spearman_correlation(x, y, z)`: Computes partial correlation controlling for motion.
- `run_permutation_test(x, y, z, n_permutations)`: Runs permutation test for significance.
- `save_results(stats_dict, output_path)`: Saves results to JSON.
- `main()`: Entry point.

### `code/analysis/sensitivity_analysis.py`

Tests robustness across window lengths.

- `load_behavioral_scores(path)`: Loads behavior data.
- `compute_flexibility_for_window_length(window_len)`: Runs full flexibility pipeline for a specific window.
- `calculate_correlation_with_behavior(flex_scores, behavior_scores)`: Computes correlation.
- `run_sensitivity_analysis(window_lengths)`: Runs analysis for multiple window lengths.
- `main()`: Entry point.

## Results Module

### `code/results/generate_report.py`

Generates the final statistical report.

- `load_json_file(path)`: Loads a JSON file.
- `generate_statistical_report(stats, sensitivity)`: Creates the report dictionary.
- `main()`: Entry point.

### `code/results/generate_plots.py`

Generates visualizations.

- `load_statistics_results(path)`: Loads stats results.
- `load_sensitivity_results(path)`: Loads sensitivity results.
- `plot_null_distribution(null_dist, p_value)`: Plots permutation null distribution.
- `plot_sensitivity_analysis(results)`: Plots sensitivity across window lengths.
- `main()`: Entry point.

## Utilities

### `code/utils/config.py`

- `set_all_seeds(seed)`: Sets random seeds for reproducibility.

### `code/utils/memory_monitor.py`

- `get_current_rss_bytes()`: Current RAM usage.
- `get_peak_rss_bytes()`: Peak RAM usage.
- `check_memory_limit(limit_gb)`: Checks if limit is exceeded.
- `enforce_memory_limit(limit_gb)`: Raises error if limit exceeded.
- `memory_guard(limit_gb)`: Context manager for memory enforcement.

### `code/utils/logging_config.py`

- `setup_logging(log_dir)`: Initializes logging infrastructure.
- `log_subject_exclusion(subject_id, reason)`: Logs exclusion.
- `log_memory_usage(rss, peak)`: Logs memory metrics.
