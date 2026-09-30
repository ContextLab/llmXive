# Data Model: Evaluating Calibration of Probabilistic Weather Forecasts

## Overview
This document defines the data entities, schemas, and relationships required for the calibration evaluation pipeline. All data flows from raw dataset → aligned dataset → recalibrated forecasts → metrics → results.

## Key Entities

### Forecast Record
Represents a single ensemble forecast instance.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `grid_id` | str | Unique identifier for geographic grid point | Yes |
| `lead_time` | int | Forecast lead time (hours or days) | Yes |
| `forecast_date` | datetime | Date/time of forecast issuance | Yes |
| `probability_value` | float | Continuous probability of event (0.0–1.0) | Yes |
| `raw_ensemble_mean` | float | Mean of ensemble members | No |
| `ensemble_members` | list[float] | Individual ensemble member values | No |

### Observation Record
Represents ground truth event for a grid point and date.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `grid_id` | str | Unique identifier for geographic grid point | Yes |
| `observation_date` | datetime | Date/time of observation | Yes |
| `event_occurred` | bool | Binary indicator of event occurrence | Yes |
| `event_value` | float | Continuous value (e.g., precipitation amount, temperature) | No |
| `variable` | str | Variable name (e.g., "precipitation", "temperature") | Yes |

### Calibration Metric
Represents a computed calibration statistic.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `metric_name` | str | Name of metric (e.g., "Brier", "CRPS") | Yes |
| `lead_time` | int | Lead time for this metric | Yes |
| `variable` | str | Variable name | Yes |
| `method` | str | Method used (e.g., "raw", "isotonic", "bayesian", "bayesian_fallback") | Yes |
| `value` | float | Computed metric value | Yes |
| `confidence_interval` | tuple[float, float] | 95% CI (lower, upper) | No |
| `sample_size` | int | Number of samples used | Yes |

### Recalibrator Model
Represents a fitted post-processing function.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `method_type` | str | Recalibration method (e.g., "isotonic", "bayesian") | Yes |
| `lead_time` | int | Lead time for this model | Yes |
| `variable` | str | Variable name | Yes |
| `parameters` | dict | Model parameters (e.g., isotonic knots, Bayesian coefficients) | Yes |
| `training_sample_size` | int | Number of training samples | Yes |
| `convergence_status` | str | "converged", "unconverged", "timeout" (for Bayesian) | No |

## Data Flow

1. **Raw Dataset**: Downloaded from source (SubseasonalRodeo or NOAA GFS); contains forecast and observation records.
2. **Aligned Dataset**: Filtered and joined by `grid_id`, `lead_time`, `forecast_date`/`observation_date`; missing values discarded.
3. **Recalibrated Forecasts**: Output of isotonic/Bayesian models applied to test split.
4. **Metrics**: Brier, CRPS, reliability diagrams, PIT histograms computed per lead time and variable.
5. **Results**: Aggregated CSVs and logs with all metrics and test results.

## File Formats

- **CSV**: Standard CSV for metrics (`results_baseline.csv`, `results_isotonic.csv`, `results_bayesian.csv`, `results_fallback.csv`).
- **PNG**: Reliability diagrams and PIT histograms (`reliability_diagram_raw.png`, etc.).
- **JSON**: Convergence diagnostics (`convergence_diagnostics.json`).
- **TXT**: Logs (`pipeline.log`, `sensitivity_analysis_log.csv`).

## Constraints

- **No In-Place Modification**: Raw data preserved; derivations written to new files.
- **Checksums**: SHA256 recorded for all raw data files.
- **Streaming**: For large datasets, use `streaming=True` to avoid memory overflow.
- **Sampling**: If full dataset exceeds disk limits, take fixed-seed random sample; log power limitation.
