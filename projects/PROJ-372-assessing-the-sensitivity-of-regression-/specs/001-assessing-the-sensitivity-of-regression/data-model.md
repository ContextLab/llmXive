# Data Model: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Overview

This document defines the internal data structures and schemas for the project. The data flow is:
1.  **Raw Data**: Downloaded from verified sources.
2.  **Profile**: Global metrics per dataset.
3.  **Stability Results**: Coefficient distributions per subset.
4.  **Meta-Analysis**: Final regression output.

## Entity Definitions

### 1. DatasetProfile
Represents the static properties of a single input dataset.
- `dataset_id`: Unique string identifier (e.g., "uci_har_01").
- `source_url`: The verified URL used.
- `n_rows`: Total rows.
- `n_predictors`: Number of numerical predictors.
- `condition_number`: Float (Condition number of $X^TX$).
- `bp_statistic`: Float (Breusch-Pagan $\chi^2$).
- `bp_p_value`: Float.
- `max_cooks_distance`: Float.
- `violation_severity`: String ("Low", "Medium", "High", or "Unknown").
- `checksum`: String (MD5 hash).

### 2. StabilityResult
Represents the outcome of the resampling phase for a specific dataset and tier.
- `dataset_id`: String.
- `sample_size_percent`: Float (e.g., 50.0).
- `sample_size_n`: Int.
- `n_valid_fits`: Int (Number of successful OLS fits out of 200).
- `coefficient_std_devs`: Dict mapping predictor name to Float (Empirical SD).
- `singularity_count`: Int.

### 3. MetaAnalysisResult
Represents the final regression model.
- `interaction_coefficient`: Float.
- `interaction_p_value`: Float.
- `r_squared`: Float.
- `sensitivity_sweep`: List of results for different BP thresholds.

## Storage Format

All intermediate and final results will be stored in JSON for portability and human readability.
- `data/profiles.json`: Array of `DatasetProfile`.
- `data/stability_results.json`: Array of `StabilityResult`.
- `artifacts/meta_analysis.json`: Single `MetaAnalysisResult`.
