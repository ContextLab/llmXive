# Data Model: Evaluating Calibration of Probabilistic Weather Forecasts

## Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to final results. All data is processed in `pandas` DataFrames or saved as Parquet/CSV.

## Entity Definitions

### 1. Raw Forecast Record
Represents a single ensemble forecast instance.
- `grid_id`: Integer (Grid point identifier).
- `lead_time`: Integer (Hours/Days ahead).
- `forecast_date`: Datetime (Date the forecast was issued).
- `probability_value`: Float (Continuous probability 0.0–1.0). **CRITICAL**: Must exist for Brier/CRPS.
- `raw_ensemble_mean`: Float (Mean of ensemble members).

### 2. Observation Record
Represents ground truth.
- `grid_id`: Integer.
- `observation_date`: Datetime (Date of observation).
- `event_occurred`: Binary (0/1, derived from thresholding `event_value`).
- `event_value`: Float (Continuous measurement, e.g., mm rain or °C).

### 3. Aligned Record
The joined dataset used for analysis.
- `grid_id`, `lead_time`, `forecast_date` (mapped to `observation_date`).
- `probability_value` (from forecast).
- `event_occurred` (from observation).
- `method`: String ('raw', 'isotonic', 'bayesian').
- `calibrated_probability`: Float (Output of recalibration).

### 4. Calibration Metric
Aggregated results.
- `metric_name`: String ('Brier', 'CRPS', 'ReliabilitySlope', 'PIT_KS_Pval').
- `lead_time`: Integer.
- `variable`: String ('precip', 'temp').
- `method`: String ('raw', 'isotonic', 'bayesian').
- `value`: Float.
- `confidence_interval_low`: Float.
- `confidence_interval_high`: Float.
- `convergence_status`: String ('Converged', 'Unconverged', 'Timeout').

## Data Flow

1.  **Ingestion**: `download.py` fetches raw files.
2.  **Gate Check**: Verify `probability_value` column exists.
3.  **Alignment**: Join on `grid_id`, `lead_time`, and `date`. Drop NaNs.
4. **Split**: Time-based split ([deferred] train, [deferred] test).
5.  **Processing**:
    - **Baseline**: Compute metrics on train/test.
    - **Isotonic**: Fit on train, predict on test.
    - **Bayesian**: Sample on train, predict on test.
6.  **Aggregation**: Metrics grouped by `lead_time`, `variable`, `method`.
7.  **Output**: `results_*.csv` files.

## Storage Constraints

- **Raw Data**: Stored in `data/raw/` with checksums.
- **Processed Data**: Stored in `data/processed/aligned.parquet`.
- **Results**: Stored in `results/` as CSVs and `results/figures/` as PNGs.
- **Memory**: Streaming used if dataset > 7GB. Otherwise, load into RAM.
