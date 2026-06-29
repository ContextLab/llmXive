# API Reference

This document provides a reference for the core modules in the `code/` directory.

## `code/config.py`

Manages project configuration and credentials.

- `get_hcp_credentials()`: Returns a tuple `(username, password)`.
- `get_config()`: Returns the full configuration dictionary.
- `validate_config()`: Validates that required configuration keys are present.

## `code/models.py`

Defines data structures used throughout the pipeline.

- `Subject`: Dataclass representing a participant (id, age, sex, motor_score, fd).
- `ConnectivityMatrix`: Dataclass for 400x400 correlation matrices.
- `NetworkMetric`: Dataclass for individual graph metrics.
- `CorrelationResult`: Dataclass for statistical test results.

## `code/data/download.py`

Handles HCP data acquisition.

- `get_subject_list_with_behavioral_data()`: Fetches subjects with valid behavioral scores.
- `fetch_subject_data(subject_id)`: Downloads NIfTI files for a specific subject.
- `download_pipeline(subjects)`: Orchestrates batch downloading.

## `code/data/preprocess.py`

Implements fMRI preprocessing steps.

- `correct_motion(input_path, output_path)`: Motion correction using FSL `mcflirt`.
- `slice_time_correction_and_normalization(input_path, output_path)`: Slice-time correction and normalization using AFNI.
- `smooth_image(input_path, output_path, fwhm)`: Spatial smoothing.
- `calculate_tsnr(nifti_path)`: Computes temporal signal-to-noise ratio.
- `validate_motion_parameters(nifti_path)`: Checks motion parameters against thresholds.

## `code/data/metrics.py`

Extracts network metrics from fMRI data.

- `download_schaefer_atlas()`: Downloads the Schaefer 400-parcel atlas.
- `extract_time_series(nifti_path, atlas_path)`: Extracts ROI time-series.
- `calculate_connectivity_matrix(time_series)`: Computes Pearson correlation matrix.
- `calculate_graph_metrics(matrix)`: Computes Modularity, Global Efficiency, etc.
- `aggregate_node_metrics(metrics)`: Averages node-level metrics to subject-level scalars.

## `code/analysis/correlations.py`

Performs statistical analysis.

- `run_correlation_analysis(data)`: Runs Spearman/Pearson correlations with FD covariate.
- `apply_fdr_correction(p_values)`: Applies Benjamini-Hochberg correction.
- `calculate_batch_size(n_subjects)`: Determines optimal batch size for memory constraints.

## `code/analysis/power.py`

Power analysis utilities.

- `calculate_detectable_effect_size(n, power=0.8, alpha=0.05)`: Computes minimum detectable r.
- `generate_power_analysis_report(results)`: Formats power analysis for the report.

## `code/viz/scatter.py`

Generates scatter plots.

- `generate_scatter_plot(x, y, r, p, q, output_path)`: Creates a scatter plot with regression line and annotations.

## `code/viz/network.py`

Generates network diagrams.

- `generate_network_diagram(correlation_matrix, significant_edges, output_path)`: Visualizes brain network with module coloring.

## `code/report/generate.py`

Assembles the final report.

- `load_template()`: Loads the Markdown report template.
- `generate_report(correlation_results, power_analysis, plots)`: Renders the final Markdown/PDF report.
