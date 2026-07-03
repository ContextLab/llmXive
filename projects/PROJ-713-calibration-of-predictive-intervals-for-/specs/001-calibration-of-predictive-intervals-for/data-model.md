# Data Model: Calibration of Predictive Intervals for Time‑Series Forecasts

## 1. Conceptual Entities

### TimeSeries
A single univariate time series.
-   `series_id`: Unique identifier (string).
-   `frequency`: Temporal frequency (e.g., "hourly", "daily").
-   `train_data`: Array of floats (values).
-   `train_timestamps`: Array of timestamps (optional).
-   `test_data`: Array of floats (values).
-   `test_timestamps`: Array of timestamps (optional).

### PredictiveInterval
The output of a model for a specific horizon.
-   `model_name`: String (e.g., "ARIMA", "Prophet", "LSTM").
-   `series_id`: String.
-   `forecast_horizon`: Integer.
-   `nominal_level`: Float (0.80 or 0.95).
-   `lower_bound`: Float.
-   `upper_bound`: Float.
-   `point_forecast`: Float.

### CalibrationMetric
Aggregated performance for a model on a series.
-   `series_id`: String.
-   `model_name`: String.
-   `nominal_level`: Float.
-   `empirical_coverage`: Float (0.0 to 1.0).
-   `coverage_deviation`: Float (empirical - nominal).
-   `pit_mean`: Float (should be ~0.5).
-   `pit_ljung_box_pvalue`: Float.
-   `crps_score`: Float.

### BootstrapResult
Result of statistical significance testing.
-   `comparison`: String (e.g., "ARIMA vs Prophet").
-   `metric`: String (e.g., "coverage_deviation").
-   `p_value`: Float.
-   `significant`: Boolean (p < 0.05).

## 2. File Formats

### Input: Raw Time Series (CSV/Parquet)
-   Columns: `timestamp`, `value`, `series_id` (if multivariate).

### Output: Results Summary (CSV)
-   Columns: `series_id`, `model_name`, `nominal_level`, `empirical_coverage`, `coverage_deviation`, `pit_pvalue`, `crps_score`.

### Output: PIT Histogram Data (JSON)
-   Structure: `{ "series_id": "...", "model": "...", "bins": [...], "counts": [...] }`.

## 3. Data Flow

1.  **Ingestion**: `data_loader` reads raw files -> `TimeSeries` objects.
2.  **Split**: `TimeSeries` split into `train` and `test` (80/20).
3.  **Training**: Models ingest `train` -> produce `PredictiveInterval` for `test`.
4.  **Evaluation**: `metrics` module ingests `test` + `PredictiveInterval` -> produces `CalibrationMetric`.
5.  **Aggregation**: `evaluation` module aggregates `CalibrationMetric` -> `BootstrapResult`.
