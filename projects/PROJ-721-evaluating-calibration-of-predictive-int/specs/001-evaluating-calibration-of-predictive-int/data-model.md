# Data Model: Evaluating Calibration of Predictive Intervals in Time Series Forecasting

## 1. Entity Definitions

### 1.1 TimeSeries
Represents a single time series from the M4 dataset.
- **id**: Unique string identifier (e.g., "M1001").
- **frequency**: String (Yearly, Quarterly, Monthly, Weekly, Daily, Hourly).
- **seasonality**: Boolean (True/False).
- **values**: List of float32 (historical observations).
- **test_values**: List of float32 (held-out test observations).
- **trend_strength**: Float (derived variance ratio) or Null.
- **trend_group**: String ('high', 'low', 'null').

### 1.2 ForecastResult
Represents the output of a single model for a single series.
- **series_id**: String (FK to TimeSeries).
- **model_name**: String (ARIMA, ETS, Prophet, LightGBM).
- **horizon**: Integer (1-12).
- **point_forecast**: Float.
- **lower_bound_80**: Float.
- **upper_bound_80**: Float.
- **lower_bound_95**: Float.
- **upper_bound_95**: Float.
- **actual_value**: Float (for the specific horizon step).
- **is_covered_80**: Boolean.
- **is_covered_95**: Boolean.

### 1.3 CalibrationMetric
Aggregated statistics per model, horizon, and group.
- **model_name**: String.
- **horizon**: Integer.
- **group_type**: String (e.g., "seasonality", "trend").
- **group_value**: String (e.g., "Yes", "High").
- **nominal_coverage_80**: Float (0.80).
- **empirical_coverage_80**: Float.
- **deviation_80**: Float.
- **nominal_coverage_95**: Float (0.95).
- **empirical_coverage_95**: Float.
- **deviation_95**: Float.
- **interval_score_80**: Float.
- **interval_score_95**: Float.
- **p_value_raw**: Float.
- **p_value_adj**: Float (BY corrected).
- **is_significant**: Boolean.
- **bootstrap_p_value_diff**: Float (p-value from paired bootstrap test of difference).
- **bootstrap_ci_lower_diff**: Float (Lower bound of 95% CI for coverage difference).
- **bootstrap_ci_upper_diff**: Float (Upper bound of 95% CI for coverage difference).

### 1.4 RecalibrationResult
Metrics after applying adaptive conformal prediction (per-series level).
- **series_id**: String.
- **model_name**: String.
- **horizon**: Integer.
- **original_coverage_80**: Float.
- **recalibrated_coverage_80**: Float.
- **improvement_80**: Float.
- **original_coverage_95**: Float.
- **recalibrated_coverage_95**: Float.
- **improvement_95**: Float.

## 2. Data Flow

1.  **Ingest**: `data/raw/m4.csv` → `TimeSeries` objects (filtered to a subset).
2.  **Preprocess**: Calculate `trend_strength` → `TimeSeries` enriched.
3.  **Model**: `TimeSeries` + `model_name` → `ForecastResult` (loop over models, horizons).
4.  **Evaluate**: `ForecastResult` → `CalibrationMetric` (aggregate).
5.  **Recalibrate**: `ForecastResult` (if deviation > 2% in any subgroup) → `RecalibrationResult`.
6.  **Output**: `CalibrationMetric`, `RecalibrationResult` → `results/coverage.csv`, `results/recalibration.csv`.

## 3. Constraints & Validations

- **TimeSeries**: `values` length must be ≥ 20 (minimum for STL + train/test split).
- **ForecastResult**: `lower_bound` < `point_forecast` < `upper_bound`.
- **CalibrationMetric**: `empirical_coverage` must be in [0, 1].
- **RecalibrationResult**: `improvement` = `recalibrated` - `original`.