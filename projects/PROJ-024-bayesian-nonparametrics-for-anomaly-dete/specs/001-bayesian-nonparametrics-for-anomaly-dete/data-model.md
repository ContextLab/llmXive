# Data Model: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Overview

This document defines the data structures, schemas, and file formats for the project. All data flows from `data/raw/` (generated or downloaded) to `data/processed/` (results).

## Entity Definitions

### TimeSeriesWindow
A slice of the time series used for local inference.
-   **Fields**:
    -   `window_id`: Integer (unique identifier).
    -   `start_idx`: Integer (start index in original series).
    -   `end_idx`: Integer (end index).
    -   `values`: Array[float] (normalized values, length=30).
    -   `has_anomaly`: Boolean (true if window overlaps with injected anomaly).

### PosteriorTrajectory
The time-series record of posterior means extracted from the DP-GMM.
-   **Fields**:
    -   `window_id`: Integer.
    -   `alpha_mean`: Float (posterior mean of concentration parameter).
    -   `alpha_deriv`: Float (first derivative of alpha).
    -   `pi_variance`: Float (variance of component weights).
    -   `converged`: Boolean (ADVI convergence status).
    -   `elbo_final`: Float (final Evidence Lower Bound).

### DetectionEvent
A record of a detected anomaly event.
-   **Fields**:
    -   `method`: String (e.g., "DPGMM", "GMM_3", "ARIMA").
    -   `injection_time`: Integer (ground truth).
    -   `detection_time`: Integer (first threshold crossing).
    -   `time_to_detection`: Integer (steps).
    -   `score`: Float (anomaly score at detection).

### SensitivityReport
A structured output of the threshold sensitivity analysis.
-   **Fields**:
    -   `threshold`: Float.
    -   `false_positive_rate`: Float.
    -   `false_negative_rate`: Float.
    -   `f1_score`: Float.

## File Formats

### Input: `data/raw/synthetic_timeseries.csv`
-   **Format**: CSV.
-   **Columns**: `timestamp`, `value`, `is_anomaly` (0/1).
-   **Encoding**: UTF-8.
-   **Constraints**: `value` normalized to mean=0, std=1. `is_anomaly` is ground truth.

### Output: `data/processed/posterior_trajectory.parquet`
-   **Format**: Parquet.
-   **Schema**: Matches `PosteriorTrajectory`.
-   **Partitioning**: By `dataset_id` (if multiple datasets used).

### Output: `data/processed/detection_events.json`
-   **Format**: JSON Lines (one event per line).
-   **Schema**: Matches `DetectionEvent`.

### Output: `data/processed/sensitivity_report.yaml`
-   **Format**: YAML.
-   **Schema**: List of `SensitivityReport` entries.

## Data Flow Diagram

1.  **Generator** -> `data/raw/synthetic_timeseries.csv`
2.  **Sliding Window** -> `TimeSeriesWindow` objects (in memory)
3.  **Inference (DPGMM/Baselines)** -> `PosteriorTrajectory` -> `data/processed/posterior_trajectory.parquet`
4.  **Detection Logic** -> `DetectionEvent` -> `data/processed/detection_events.json`
5.  **Analysis** -> `SensitivityReport` -> `data/processed/sensitivity_report.yaml`

## Constraints & Validation

-   **Normalization**: All input values MUST be normalized (mean=0, std=1) before inference (FR-001).
-   **Convergence**: Rows with `converged=False` are excluded from trajectory analysis (FR-009).
-   **Size**: Input datasets MUST have ≥1,000 observations (FR-001).
-   **Checksum**: All files in `data/raw/` must have a corresponding `.sha256` checksum file.
