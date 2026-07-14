# API Reference

This document lists the public interfaces for the core modules.

## `code/download.py`

- `load_config()`: Loads configuration from `config.yaml`.
- `main()`: Entry point for downloading Sleep-EDF data.

## `code/preprocess.py`

- `bandpass_filter(data, lowcut, highcut, fs)`: Applies Butterworth bandpass filter.
- `compute_kurtosis(data)`: Computes kurtosis for artifact detection.
- `compute_high_freq_power(data, fs)`: Computes high-frequency power.
- `remove_ica_artifacts(raw, threshold)`: Removes ICA components exceeding thresholds.
- `epoch_data(raw, events, tmin, tmax)`: Segments data into epochs.
- `validate_no_nan(data)`: Checks for NaN values.

## `code/metrics.py`

- `compute_waking_connectivity(epochs, freq_band)`: Computes coherence matrix.
- `validate_connectivity_matrix(matrix)`: Ensures symmetry and range [0,1].
- `compute_centralities(matrix)`: Returns degree, betweenness, eigenvector centrality.
- `compute_pli(epochs)`: Calculates Phase Lag Index.
- `aggregate_pli_to_global(pli_dict)`: Averages PLI per sleep stage.
- `calculate_vif(metrics_df)`: Computes Variance Inflation Factor.

## `code/analysis.py`

- `run_lme_analysis(df)`: Runs Linear Mixed-Effects model.
- `apply_benjamini_hochberg(p_values)`: Applies FDR correction.
- `run_shapiro_wilk(residuals)`: Performs normality test.
- `generate_analysis_report(results)`: Creates JSON report.

## `code/report.py`

- `load_analysis_results(path)`: Loads JSON results.
- `calculate_temporal_proximity(night_ids)`: Checks if waking/sleep data are from same night.
- `generate_report(results, temporal_flag)`: Creates final report dictionary.
- `save_report(report, path)`: Saves report to Markdown/JSON.
