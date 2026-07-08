# Data Model: Evaluating the Sensitivity of Regression Models to Outlier Removal Strategies

## Overview

This document defines the data structures used in the pipeline. All data is processed in memory using `pandas` DataFrames and serialized to JSON/CSV for reporting.

## Key Entities

### 1. Dataset
Represents a single UCI regression dataset.

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | UCI dataset identifier (e.g., "california_housing"). |
| `raw_data` | DataFrame | Unmodified dataset after download. |
| `preprocessed_data` | DataFrame | Data after imputation and encoding. |
| `target_variable` | str | Name of the target column. |
| `continuous_features` | List[str] | Columns used for IQR/Z-score outlier detection. |
| `categorical_features` | List[str] | Columns one-hot encoded. |

### 2. RegressionResult
Output of an OLS fit.

| Field | Type | Description |
|-------|------|-------------|
| `strategy` | str | "Raw", "IQR", "Z-Score", "Cooks". |
| `dataset_name` | str | Source dataset. |
| `coefficients` | Dict[str, float] | Map of feature name to coefficient. |
| `p_values` | Dict[str, float] | Map of feature name to p-value. |
| `r_squared` | float | Model R². |
| `rmse` | float | Root Mean Squared Error. |
| `vif_flags` | Dict[str, int] | Map of feature name to VIF (if > 5). |
| `status` | str | "Success", "Data Loss", "Skipped". |

### 3. SensitivityReport
Aggregated comparison results.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_name` | str | Source dataset. |
| `metric_changes` | Dict | `{"r2_delta": float, "rmse_delta": float, "coef_deltas": Dict[str, float]}`. |
| `statistical_test_results` | Dict | `{"wilcoxon_p_value": float, "t_test_p_value": float, "test_statistic": float}`. |
| `sweep_results` | List[Dict] | Results for IQR multipliers {1.0, 1.25, ...}. |

## Data Flow

1.  **Input**: UCI Dataset ID (string).
2.  **Download**: `ucimlrepo` fetches raw CSV/Parquet.
3.  **Preprocess**: Impute missing, encode categoricals.
4.  **Baseline Fit**: OLS on raw data.
5.  **Outlier Detection**: Apply IQR/Z-score (Union logic) / Cook's.
6.  **Clean Fit**: OLS on cleaned data.
7.  **Compare**: Calculate deltas (R², RMSE, coefficients).
8.  **Aggregate**: Wilcoxon Signed-Rank and Paired t-test across multiple datasets.
9.  **Output**: JSON report + PDF visualization.