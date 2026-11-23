# API Reference

## `code/data/download.py`
- `download_dataset()`: Downloads the dataset using `openneuro-cli`.

## `code/data/preprocess.py`
- `preprocess_fmriprep()`: Wraps fMRIPrep execution.
- `extract_behavioral_metrics()`: Parses metadata for motor scores.
- `calculate_retention_rate()`: Computes subject retention.
- `check_power()`: Validates sample size against thresholds.

## `code/analysis/centrality.py`
- `load_connectivity_matrix()`: Loads precomputed connectivity matrices.
- `compute_centrality_metrics()`: Calculates degree, betweenness, eigenvector.
- `calculate_mean_fd()`: Computes average Framewise Displacement.
- `run_centrality_analysis()`: Orchestrates the centrality pipeline.

## `code/analysis/regression.py`
- `load_behavioral_data()`: Loads subject scores.
- `fit_linear_regression()`: Fits the primary model.
- `generate_scatter_plot()`: Creates visualization of results.
- `run_regression_analysis()`: Orchestrates the regression pipeline.

## `code/analysis/validation.py`
- `run_freedman_lane_permutation()`: Executes the permutation test.
- `run_cross_validation()`: Performs k-fold CV.
- `save_permutation_results()`: Saves empirical p-values.

## `code/utils/config.py`
- `get_config()`: Retrieves the global configuration object.
- `get_dataset_config()`, `get_preprocessing_config()`, etc.: Access specific config sections.

## `code/utils/metrics.py`
- `generate_report()`: Creates the final reproducibility report.
- `calculate_artifact_checksums()`: Verifies data integrity.
- `load_validation_metrics()`: Loads validation results for reporting.
