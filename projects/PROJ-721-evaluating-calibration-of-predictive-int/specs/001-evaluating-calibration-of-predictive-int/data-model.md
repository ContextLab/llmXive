# Data Model: Evaluating Calibration of Predictive Intervals

## Overview

This document defines the data structures used throughout the project. All data flows from the raw M4 dataset through preprocessing, modeling, and evaluation, resulting in structured CSV and JSON outputs.

## Entities

### TimeSeries
Represents a single time series from the M4 dataset.

*   **id**: Unique identifier (string).
*   **frequency**: Seasonal frequency (integer, e.g., 12 for monthly).
*   **seasonality**: Binary indicator (string: "Yes", "No").
*   **observations**: List of floats (historical data).
*   **train_split**: Integer (index where training ends).
*   **test_split**: Integer (index where test begins).
*   **trend_strength**: Float (variance ratio from STL).
*   **trend_category**: String ("High", "Low").

### ForecastResult
Represents the output of a single model for a single time series.

*   **series_id**: Reference to `TimeSeries.id`.
*   **model_name**: String ("ARIMA", "ETS", "Prophet", "LightGBM").
*   **horizon**: Integer (1 to 12).
*   **point_forecast**: Float.
*   **lower_bound_80**: Float.
*   **upper_bound_80**: Float.
*   **lower_bound_95**: Float.
*   **upper_bound_95**: Float.
*   **actual_value**: Float (ground truth for the horizon).

### CalibrationMetric
Aggregated statistics for a specific model, horizon, and subgroup.

*   **model_name**: String.
*   **horizon**: Integer.
*   **nominal_coverage_80**: Float (0.80).
*   **empirical_coverage_80**: Float.
*   **deviation_80**: Float.
*   **nominal_coverage_95**: Float (0.95).
*   **empirical_coverage_95**: Float.
*   **deviation_95**: Float.
*   **subgroup_seasonality**: String.
*   **subgroup_trend**: String.
*   **n_series**: Integer (count of series in subgroup).
*   **p_value_raw**: Float.
*   **p_value_fdr**: Float.

## Data Flow

1.  **Raw**: `M4-Data.zip` (CSV files) -> `data/raw/`.
2.  **Processed**: `TimeSeries` objects -> `data/processed/time_series.jsonl`.
3.  **Forecasts**: `ForecastResult` objects -> `results/forecasts.csv`.
4.  **Metrics**: `CalibrationMetric` objects -> `results/calibration_metrics.csv`.

## Constraints

*   **Immutability**: Raw data is never modified.
*   **Checksums**: All files in `data/` are checksummed.
*   **Schema Validation**: All outputs must pass the YAML schema validation defined in `contracts/`.
