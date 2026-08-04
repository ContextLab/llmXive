# Data Model: Evaluating Robustness of Statistical Methods to Non-Independence

## Overview

This document defines the data structures for the project, including raw inputs, processed time series, synthetic data, and analysis results. All data is stored in `data/` and `results/` directories.

## Entities

### 1. TimeSeries (Raw & Processed)

Represents a single time series dataset.

| Attribute | Type | Description |
|-----------|------|-------------|
| `source` | str | Dataset source (e.g., "NOAA", "Yahoo", "Energy") |
| `series_id` | str | Unique identifier for the series |
| `raw_values` | list[float] | Original time series values |
| `processed_values` | list[float] | Stationary/detrended values (NOT differenced if long-memory) |
| `missing_count` | int | Number of missing values before interpolation |
| `stationarity_status` | dict | `{"adf_p": float, "differencing_count": int, "detrended": bool, "method": "unit_root"|"long_memory"}` |
| `acf_lag_20` | list[float] | Autocorrelation up to lag 20 |
| `hurst_exponent` | float | Estimated Hurst exponent (via DFA) |
| `spectral_peak_ratio` | float | Spectral density peak ratio |
| `n_eff` | float | Effective Sample Size |

**File Path**: `data/processed/{series_id}_processed.csv`

### 2. SyntheticData

Represents a generated time series with known parameters.

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | str | "fGn" or "ARFIMA" |
| `hurst` | float | True Hurst exponent (0.5, 0.7, 0.8, 0.9) |
| `mean` | float | True mean (0.0) |
| `length` | int | Number of points (100, 500, 1k, 5k, 10k) |
| `values` | list[float] | Generated values |
| `theoretical_vif` | float | Theoretical Variance Inflation Factor |
| `theoretical_n_eff` | float | Theoretical Effective Sample Size |

**File Path**: `data/processed/synthetic_{model_type}_H{hurst}_N{length}.csv`

### 3. TestResult

Represents the outcome of a single hypothesis test.

| Attribute | Type | Description |
|-----------|------|-------------|
| `test_type` | str | "t_test" or "f_test" |
| `p_value` | float | Calculated p-value |
| `rejection` | bool | `True` if `p_value < 0.05` |
| `dataset_id` | str | ID of the series tested |
| `iteration` | int | Monte Carlo iteration number |
| `hurst_estimated` | float | Estimated H (for real data) or True H (for synthetic) |
| `n_eff` | float | Effective sample size used |

**File Path**: `results/test_results_{dataset_id}.csv`

### 4. ErrorRateSummary

Aggregates results for a dataset or synthetic configuration.

| Attribute | Type | Description |
|-----------|------|-------------|
| `dataset_id` | str | ID of the dataset (real or synthetic) |
| `nominal_alpha` | float | 0.05 |
| `observed_error_rate` | float | Proportion of rejections |
| `shuffled_null_distribution` | list[float] | P-values from shuffled versions ([deferred] per series) |
| `regression_slope` | float | Slope of error rate vs. H (from non-linear model) |
| `regression_p_value` | float | P-value of the slope |
| `vif` | float | Variance Inflation Factor |
| `n_eff` | float | Effective Sample Size |
| `hurst_target` | float | Target H (for synthetic) or Estimated H (for real) |
| `length_target` | int | Target N (for synthetic) or Actual N (for real) |

**File Path**: `results/error_rate_summary.csv`

## Data Flow

1. **Ingestion**: Raw data downloaded to `data/raw/`.
2. **Preprocessing**: `data/raw/` → `data/processed/` (stationary, metrics, **shuffled nulls**).
3. **Synthesis**: `data/processed/` (synthetic) generated with known parameters and **N-variation**.
4. **Testing**: `results/test_results_*.csv` generated from hypothesis tests.
5. **Aggregation**: `results/error_rate_summary.csv` compiled from test results.
6. **Visualization**: Figures generated from `results/error_rate_summary.csv` and `data/processed/`.

## Constraints

- **Immutability**: Raw data in `data/raw/` is never modified.
- **Checksums**: All raw files checksummed (SHA-256) and recorded in `state/projects/PROJ-369-evaluating-the-robustness-of-statistical.yaml`.
- **PII**: No personally identifying information allowed.
- **Shuffling**: [deferred] shuffled versions per series are generated and stored in `data/processed/{series_id}_shuffled_nulls.csv`.