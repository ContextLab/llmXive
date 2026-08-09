# Data Model: Evaluating Calibration of Probabilistic Weather Forecasts

## Overview
This document defines the data structures, schemas, and relationships for the weather forecast calibration project. It ensures data hygiene, reproducibility, and contract validation for the implementation.

## Entity Definitions

### 1. Forecast Record
Represents a single ensemble forecast instance.
- **Attributes**:
  - `grid_id`: Unique identifier for the geographic grid point.
  - `lead_time`: Integer hours ahead of the forecast date.
  - `forecast_date`: ISO 8601 date of the forecast issuance.
  - `probability_value`: Float (0.0 to 1.0) representing the forecast probability of the event.
  - `raw_ensemble_mean`: Float, mean of the raw ensemble members.
- **Constraints**: `probability_value` must be in [0, 1]. `lead_time` > 0.

### 2. Observation Record
Represents the ground truth for a specific grid and date.
- **Attributes**:
  - `grid_id`: Matches `ForecastRecord.grid_id`.
  - `observation_date`: ISO 8601 date of the observation (aligned to forecast + lead_time).
  - `event_occurred`: Binary (0 or 1) indicating if the event occurred.
  - `event_value`: Float, continuous value (e.g., temperature or precipitation amount).
- **Constraints**: `event_occurred` in {0, 1}.

### 3. Calibration Metric
Represents a computed statistic for a specific method, lead time, and variable.
- **Attributes**:
  - `metric_name`: String (e.g., "Brier", "CRPS", "PIT_KS").
  - `lead_time`: Integer.
  - `method`: String (e.g., "raw", "isotonic", "bayesian").
  - `variable`: String (e.g., "precipitation", "temperature").
  - `value`: Float.
  - `confidence_interval`: String or Tuple (e.g., "(0.12, 0.15)").
  - `convergence_status`: String ("Converged", "Unconverged", "N/A").

### 4. Recalibrator Model
Represents a fitted post-processing function.
- **Attributes**:
  - `method_type`: String (e.g., "isotonic", "bayesian").
  - `lead_time`: Integer.
  - `parameters`: JSON/Blob containing coefficients or knots.
  - `training_sample_size`: Integer.
  - `fitted_date`: ISO 8601 timestamp.

## Data Flow

1.  **Raw Ingestion**: `data/raw/subseasonal_rodeo.parquet` (or similar) contains raw forecasts and observations.
2.  **Alignment**: `src/align.py` joins forecasts and observations on `grid_id`, `lead_time`, and `date`. Records with missing values are discarded. Output: `data/processed/aligned_data.parquet`.
3. **Splitting**: `src/align.py` splits `aligned_data.parquet` chronologically into `train` ([deferred]) and `test` ([deferred]).
4.  **Model Fitting**:
    - `src/recalibrate_isotonic.py` fits models on `train`, outputs `results_isotonic.csv`.
    - `src/recalibrate_bayesian.py` fits models on a **stratified random sample** of `train`, outputs `results_bayesian.csv`.
5.  **Evaluation**: `src/metrics.py` computes metrics on `test` set for all methods.
6.  **Comparison**: `src/compare.py` performs statistical tests and outputs summary tables.

## Storage Strategy

- **Raw Data**: `data/raw/` (Checksummed, read-only).
- **Processed Data**: `data/processed/` (Aligned, split, derived features).
- **Results**: `results/` (CSVs, PNGs).
- **Models**: `models/` (Serialized pickle/joblib files for Isotonic, `pymc` trace files for Bayesian).

## Validation Rules

- **Completeness**: No `NaN` in `probability_value` or `event_occurred` after alignment.
- **Range**: `probability_value` ∈ [0, 1].
- **Uniqueness**: `(grid_id, lead_time, forecast_date)` is unique in `ForecastRecord`.
- **Convergence**: `convergence_status` must be "Converged" for Bayesian results to be considered valid for SC-006.