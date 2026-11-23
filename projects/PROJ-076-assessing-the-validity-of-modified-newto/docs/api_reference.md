# API Reference

This document outlines the public API for the `code/` module.

## Data Ingestion

### `code/download.py`
- `fetch_with_retry(url, retries=3)`: Fetches a URL with exponential backoff.
- `download_file(url, dest_path)`: Downloads a file to the specified path.
- `download_sparc_data(output_dir)`: Orchestrates the download of the full SPARC dataset.

### `code/preprocess.py`
- `parse_sparc_file(file_path)`: Parses a single SPARC galaxy file into a DataFrame.
- `apply_quality_filters(df)`: Filters galaxies based on inclination uncertainty and data point count.
- `main()`: Entry point for the preprocessing pipeline.

## Modeling

### `code/models/mond.py`
- `mond_simple(r, M_L, a0=1.2e-10)`: Calculates the MOND "simple" acceleration profile.
- `mond_simple_velocity(r, M_L, a0=1.2e-10)`: Calculates the circular velocity for the MOND model.

### `code/models/nfw.py`
- `nfw_circular_velocity(r, vs, rs)`: Calculates the NFW circular velocity.
- `nfw_with_baryons(r, M_L, vs, rs)`: Combines NFW halo with baryonic disk/bulge components.

## Fitting & Analysis

### `code/fit.py`
- `fit_mond_galaxy(data)`: Fits the MOND model to a single galaxy.
- `fit_nfw_galaxy(data)`: Fits the NFW model to a single galaxy.
- `fit_all_galaxies(input_csv, output_csv)`: Iterates over all galaxies and saves results.

### `code/metrics.py`
- `calculate_reduced_chi2(residuals, dof)`: Computes reduced chi-squared.
- `calculate_aic(ll, k)`: Computes Akaike Information Criterion.
- `calculate_bic(ll, k, n)`: Computes Bayesian Information Criterion.

### `code/residuals.py`
- `calculate_residuals(observed, predicted)`: Computes residuals.
- `block_bootstrap_permutation_test(residuals_mond, residuals_nfw, n_boot=10000)`: Performs the permutation test.
- `holm_bonferroni_correction(p_values)`: Applies Holm-Bonferroni correction to a list of p-values.

## Reporting

### `code/generate_verdict.py`
- `evaluate_verdict(p_value)`: Returns a string verdict based on the p-value threshold.
- `generate_verdict_report(stats_df, output_path)`: Generates the final `analysis_verdict.md`.