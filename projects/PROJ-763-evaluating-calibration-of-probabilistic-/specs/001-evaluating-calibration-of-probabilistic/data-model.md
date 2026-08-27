# Data Model: Evaluating Calibration of Probabilistic Weather Forecasts

## Overview

This document defines the data structures, schemas, and flow for the calibration evaluation pipeline. All data is processed in `pandas` DataFrames or `pyarrow` tables, with intermediate results stored as Parquet for efficiency and final results as CSV for readability.

## Key Entities

### 1. Forecast Record
Represents a single ensemble forecast instance.
*   **Attributes**:
    *   `grid_id` (int): Unique identifier for the geographic grid point.
    *   `lead_time` (int): Forecast lead time in hours (e.g., 24, 48, 72).
    *   `season` (str): Season category (e.g., "Winter", "Summer") derived from `forecast_date`.
    *   `forecast_date` (datetime): Date the forecast was issued.
    *   `probability_value` (float): The raw ensemble-derived probability of the event (0.0 - 1.0). **CRITICAL**: Required for Brier/CRPS.
    *   `raw_ensemble_mean` (float): Mean of the ensemble members (used for reference).
    *   `variable` (str): Target variable (e.g., "precip", "temp").

### 2. Observation Record
Represents the ground truth event.
*   **Attributes**:
    *   `grid_id` (int): Matches `ForecastRecord.grid_id`.
    *   `observation_date` (datetime): Date of the event.
    *   `event_occurred` (bool): Binary indicator (1 if event occurred, 0 otherwise).
    *   `event_value` (float): Continuous value (e.g., mm of rain, degrees C).

### 3. Calibration Metric
Represents a computed statistic.
*   **Attributes**:
    *   `metric_name` (str): "Brier", "CRPS", "PIT_KS".
    *   `lead_time` (int): The lead time for this metric.
    *   `variable` (str): The variable (precip/temp).
    *   `method` (str): "raw", "isotonic", "bayesian".
    *   `value` (float): The computed score.
    *   `confidence_interval` (str): "95% CI: [lower, upper]".
    *   `test_type` (str): "DM", "Wilcoxon", "Bootstrap", "N/A".
    *   `p_value` (float): The p-value of the statistical test.
    *   `convergence_status` (str): "Converged", "Unconverged", "Timeout", "Excluded", "N/A".
    *   `prior_dominance_flag` (bool): True if Flat Prior outperforms Physics Prior.

### 4. Recalibrator Model
Represents a fitted post-processing function.
*   **Attributes**:
    *   `method_type` (str): "Isotonic", "Bayesian".
    *   `lead_time` (int): Lead time for this model.
    *   `season` (str): Season for this model (if applicable).
    *   `parameters` (dict): Serialized model parameters (e.g., knots for isotonic, coefficients for Bayesian).
    *   `training_sample_size` (int): Number of samples used for training.
    *   `pooling_strategy` (str): "None", "Adjacent_Lead", "Adjacent_Season", "Global_Fit", "Insufficient_Data".
    *   `fallback_reason` (str): Reason for fallback (e.g., "Low_Sample", "Timeout").

## Data Flow

1.  **Raw Ingestion**:
    *   Source: Hugging Face (SubseasonalRodeo or NOAA/GFS).
    *   Format: Parquet/CSV/ZIP.
    *   Gate: Check for `probability_value` or `ensemble_members`.
2.  **Autocorrelation Estimation**:
    *   Calculate ACF of forecast errors.
    *   Output: `data/processed/autocorr_metadata.json`.
3.  **Alignment**:
    *   Join `ForecastRecord` and `ObservationRecord` on `grid_id`, `lead_time`, `forecast_date`/`observation_date`.
    *   Output: `data/processed/aligned_data.parquet`.
4.  **Splitting**:
    *   Blocked split (Time-based) into Train/Test using `effective_autocorrelation_length`.
    *   Output: `data/processed/train.parquet`, `data/processed/test.parquet`.
5.  **Metric Calculation**:
    *   Input: Aligned data.
    *   Output: `results/results_baseline.csv`.
6.  **Recalibration**:
    *   Input: Train/Test splits.
    *   Process: Isotonic/Bayesian fitting.
    *   Output: `results/results_isotonic.csv`, `results/results_bayesian.csv`.
7.  **Visualization**:
    *   Input: Metric results.
    *   Output: `results/figures/*.png`.

## Storage Strategy

*   **Raw Data**: Stored in `data/raw/` with checksums. Read-only.
*   **Processed Data**: Stored in `data/processed/`. Parquet format for fast I/O.
*   **Results**: Stored in `results/`. CSV for metrics, PNG for figures.
*   **Logs**: `logs/pipeline.log` for runtime errors and convergence status.