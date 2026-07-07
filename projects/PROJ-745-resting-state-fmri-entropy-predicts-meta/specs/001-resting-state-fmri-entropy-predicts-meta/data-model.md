# Data Model: Resting-State fMRI Entropy Predicts Metacognitive Accuracy

## Overview

This document defines the data schemas for the project, ensuring traceability from raw data to final statistical outputs. All data artifacts adhere to the Constitution's Data Hygiene and Single Source of Truth principles. **The file `data/processed/results/regression_output.csv` is the Single Source of Truth (SSoT) for final paper statistics.**

## Raw Data Schemas

### HCP Subject Metadata

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `subject_id` | string | Unique HCP subject identifier (e.g., "100106") | HCP Release |
| `age` | integer | Age in years | HCP Behavioral |
| `sex` | string | "M" or "F" | HCP Behavioral |
| `mean_fd` | float | Mean Framewise Displacement (mm) | Preprocessing Output |

### Behavioral Trial Data

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `subject_id` | string | Unique HCP subject identifier | HCP Behavioral |
| `trial_id` | integer | Trial number | HCP Behavioral |
| `stimulus` | string | Stimulus type (e.g., "grating") | HCP Behavioral |
| `response` | integer | Subject response (0/1) | HCP Behavioral |
| `confidence` | integer | Confidence rating (1-4) | HCP Behavioral |

## Derived Data Schemas

### Parcellated Time Series

| Field | Type | Description | Dimensions |
|-------|------|-------------|------------|
| `subject_id` | string | Unique HCP subject identifier | (N_subjects,) |
| `parcel_id` | integer | Parcel index (0-399) | (N_subjects, 400) |
| `timepoint` | integer | Time index | (N_subjects, 400, 1200) |
| `bold_signal` | float | Preprocessed BOLD signal | (N_subjects, 400, 1200) |

### Entropy Metrics

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `subject_id` | string | Unique HCP subject identifier | MSE Calculation |
| `mse_scale_1` | float | MSE at scale τ=1 | `nolds` |
| `mse_scale_2` | float | MSE at scale τ=2 | `nolds` |
| `mse_scale_3` | float | MSE at scale τ=3 | `nolds` |
| `mse_scale_4` | float | MSE at scale τ=4 | `nolds` |
| `mse_scale_5` | float | MSE at scale τ=5 | `nolds` |
| `whole_brain_entropy` | float | **Arithmetic mean** of MSE across scales and parcels | Aggregation |

### Metacognitive Metrics

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `subject_id` | string | Unique HCP subject identifier | Meta-d′ Calculation |
| `d_prime` | float | Sensitivity (d′) | Type 2 SDT |
| `meta_d_prime` | float | Metacognitive sensitivity (meta-d′) | Type 2 SDT |
| `meta_efficiency` | float | Ratio (meta-d′/d′) | Aggregation |
| `n_trials` | integer | Number of valid trials | Behavioral Data |
| `missing_confidence_pct` | float | Percentage of missing confidence ratings | Validation |

### Regression Output (SSoT)

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `predictor` | string | Predictor name (e.g., "whole_brain_entropy") | Regression Model |
| `coefficient` | float | Regression coefficient (beta) | `scikit-learn` |
| `std_error` | float | Standard error of coefficient | `scikit-learn` |
| `p_value` | float | Raw p-value | `scikit-learn` |
| `p_value_bonferroni` | float | Bonferroni-corrected p-value | Correction |
| `r_squared` | float | Model R-squared | `scikit-learn` |
| `ci_lower` | float | Bootstrap CI Lower Bound | Bootstrapping |
| `ci_upper` | float | Bootstrap CI Upper Bound | Bootstrapping |

### Sensitivity Analysis Output

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `r_value` | float | Tolerance parameter r | Sensitivity Sweep |
| `coefficient` | float | Regression coefficient at r | Regression Model |
| `p_value` | float | p-value at r | Regression Model |
| `direction` | string | "positive" or "negative" (sign of beta) | Aggregation |

## Data Flow

1.  **Raw**: HCP fMRI (NIfTI) and Behavioral (CSV/Parquet) → `data/raw/`
2.  **Preprocessed**: Parcellated time series → `data/processed/timeseries/`
3.  **Metrics**: Entropy and Meta-d′ → `data/processed/metrics/`
4.  **Analysis**: Regression and Sensitivity → `data/processed/results/` (**SSoT**: `regression_output.csv`)

## Data Hygiene

- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/`.
- **Immutability**: Raw data is never modified. Derived files are written to new filenames.
- **PII**: No personally identifiable information is stored. Subject IDs are anonymized.