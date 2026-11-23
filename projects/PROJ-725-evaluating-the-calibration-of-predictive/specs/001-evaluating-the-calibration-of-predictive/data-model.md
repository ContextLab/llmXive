# Data Model: Evaluating the Calibration of Predictive Uncertainty Intervals

## 1. Overview

This document defines the data structures, schemas, and flow for the calibration evaluation pipeline. All data is stored in `data/` (raw/processed) and results in `artifacts/`.

## 2. Data Flow

1.  **Raw Ingestion**: Datasets downloaded from verified HF URLs -> `data/raw/{dataset_id}.csv|parquet`.
2.  **Preprocessing**: Cleaned, split, and validated -> `data/processed/{dataset_id}_split.parquet`.
3.  **Model Execution**: Intervals generated -> `artifacts/intervals/{dataset_id}_{method}.parquet`.
4.  **Aggregation**: Metrics computed -> `artifacts/metrics/{dataset_id}.json`.
5.  **Final Report**: All metrics merged -> `artifacts/final_results.csv`.

## 3. Schema Definitions

### 3.1. Input Dataset Schema (Processed)
*Source: `data/processed/{id}_split.parquet`*

| Field | Type | Description |
| :--- | :--- | :--- |
| `split` | `str` | "train" or "test" |
| `features` | `list[float]` | Flattened feature vector |
| `target` | `float` | True continuous target value |
| `row_id` | `int` | Original row index (for traceability) |

### 3.2. Prediction Interval Schema
*Source: `artifacts/intervals/{dataset_id}_{method}.parquet`*

| Field | Type | Description |
| :--- | :--- | :--- |
| `dataset_id` | `str` | Identifier of the source dataset |
| `method` | `str` | Name of the UQ method (e.g., "QuantileRegression") |
| `row_id` | `int` | Matches input `row_id` |
| `lower_bound` | `float` | Lower bound of the interval |
| `upper_bound` | `float` | Upper bound of the interval |
| `target` | `float` | True target value |
| `covered` | `bool` | `True` if `lower <= target <= upper` |
| `width` | `float` | `upper - lower` |
| `variance_bin` | `str` | "low", "medium", "high" (derived from variance model) |

### 3.3. Metrics Aggregation Schema
*Source: `artifacts/metrics/{dataset_id}.json`*

| Field | Type | Description |
| :--- | :--- | :--- |
| `dataset_id` | `str` | Dataset identifier |
| `method` | `str` | Method name |
| `nominal_coverage` | `float` | Target (e.g., 0.90) |
| `empirical_coverage` | `float` | Proportion of `covered=True` |
| `coverage_deviation` | `float` | `empirical - nominal` |
| `mis_calibrated` | `bool` | `True` if deviation > threshold (default 0.02) |
| `binomial_p_value` | `float` | p-value from binomial test |
| `interval_score` | `float` | Mean Interval Score |
| `avg_width` | `float` | Mean interval width |
| `stratified_coverage` | `dict` | Map of `variance_bin` -> `empirical_coverage` |

## 4. Constraints & Invariants

- **Non-Negative Width**: `upper_bound >= lower_bound` for all rows.
- **Coverage Range**: `0.0 <= empirical_coverage <= 1.0`.
- **Traceability**: Every result row in `final_results.csv` must link to a specific `dataset_id` and `method`.
- **Checksum**: All raw files must have a SHA256 hash recorded in `state.yaml`.
