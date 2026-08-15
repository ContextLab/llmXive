# Data Model: Evaluating Calibration of Probabilistic Weather Forecasts

## Overview
This document defines the data structures used throughout the pipeline. It ensures that all transformations are traceable and that the data conforms to the schema defined in the `contracts/` directory.

## Entity Definitions

### Forecast Record
Represents a single ensemble forecast instance.
- **Attributes**:
  - `grid_id` (int): Unique identifier for the grid point.
  - `lead_time` (int): Forecast lead time in hours (e.g., 24, 48).
  - `forecast_date` (datetime): Date and time of the forecast issue.
  - `probability_value` (float): Probability of the event (0.0 to 1.0).
  - `raw_ensemble_mean` (float): Mean of the ensemble members (optional, for reference).

### Observation Record
Represents the ground truth event.
- **Attributes**:
  - `grid_id` (int): Unique identifier for the grid point (matches Forecast Record).
  - `observation_date` (datetime): Date and time of the observation (matches forecast_date + lead_time).
  - `event_occurred` (bool): Binary indicator (1 if event occurred, 0 otherwise).
  - `event_value` (float): Continuous value for the event (e.g., temperature, precipitation amount).

### Calibration Metric
Represents a computed statistic.
- **Attributes**:
  - `metric_name` (str): Name of the metric (e.g., "Brier", "CRPS", "PIT_KS").
  - `lead_time` (int): Lead time for which the metric was computed.
  - `variable` (str): Variable name (e.g., "precipitation", "temperature").
  - `method` (str): Method used (e.g., "raw", "isotonic", "bayesian").
  - `value` (float): The computed metric value.
  - `confidence_interval` (str): JSON string representing the 95% CI (e.g., "[0.1, 0.2]").

### Recalibrator Model
Represents a fitted post-processing function.
- **Attributes**:
  - `method_type` (str): Type of model (e.g., "isotonic", "bayesian").
  - `lead_time` (int): Lead time for which the model was fitted.
  - `variable` (str): Variable name.
  - `parameters` (dict): Model parameters (e.g., knots for isotonic, coefficients for Bayesian).
  - `training_sample_size` (int): Number of samples used for training.

## Data Flow
1. **Raw Data**: Downloaded from SubseasonalRodeo (or fallback).
2. **Aligned Data**: Merged Forecast and Observation records by `grid_id`, `lead_time`, and `date`. Missing values are dropped.
3. **Train/Test Split**: Chronological split (70/30).
4. **Baseline Metrics**: Computed on the full dataset (or test set, depending on spec).
5. **Recalibrated Metrics**: Computed on the test set after applying the recalibration model.
6. **Comparison Metrics**: Computed by comparing Baseline and Recalibrated metrics.

## Storage Format
- **Raw Data**: Parquet or CSV (preserved with checksum).
- **Aligned Data**: Parquet (optimized for columnar access).
- **Results**: CSV (one row per metric, method, lead time, variable).
- **Diagrams**: PNG (kernel-smoothed reliability diagrams, PIT histograms).
