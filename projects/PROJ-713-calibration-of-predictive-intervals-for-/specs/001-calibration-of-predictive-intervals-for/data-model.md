# Data Model: Calibration of Predictive Intervals for Time‑Series Forecasts

## Overview

This document defines the data structures used for loading, processing, and evaluating time-series forecasts. All data flows through the `data/raw/` (immutable) and `data/processed/` (derived) directories.

## Entities

### TimeSeries
A single univariate time series.
*   **Attributes**:
    *   `series_id` (str): Unique identifier (e.g., "M4-1001", "UCI-E1").
    *   `timestamp` (datetime): Sequence of timestamps.
    *   `value` (float): Sequence of observed values.
    *   `frequency` (str): e.g., "D", "M", "Y".
*   **Split**:
 * `train_values` (float): First **[deferred]** of `value`.
 * `test_values` (float): Last **[deferred]** of `value`.

### PredictiveInterval
A tuple representing the forecast interval for a specific horizon.
*   **Attributes**:
    *   `series_id` (str)
    *   `model` (str): "ARIMA", "Prophet", "LSTM".
    *   `horizon` (int): Forecast step index.
    *   `nominal_level` (float): e.g., 0.80, 0.95.
    *   `lower_bound` (float)
    *   `upper_bound` (float)

### CalibrationMetric
Aggregated performance metrics for a model-series pair.
*   **Attributes**:
    *   `series_id` (str)
    *   `model` (str)
    *   `nominal_level` (float)
    *   `empirical_coverage` (float): Proportion of test values within bounds.
    *   `coverage_deviation` (float): `empirical_coverage - nominal_level`.
    *   `pit_p_value` (float): Ljung-Box test p-value for PIT uniformity.
    *   `crps_score` (float): Continuous Ranked Probability Score.

### SignificanceTestResult
Result of a paired bootstrap test between two models.
*   **Attributes**:
    *   `model_a` (str)
    *   `model_b` (str)
    *   `metric` (str): e.g., "coverage_deviation".
    *   `p_value` (float)
    *   `is_significant` (bool): `p_value < 0.05`.

## File Formats

### CSV: `results/coverage.csv`
| series_id | model | nominal_level | empirical_coverage | coverage_deviation |
| :--- | :--- | :--- | :--- | :--- |
| M4-1001 | ARIMA | 0.95 | 0.92 | -0.03 |

### CSV: `results/distributional_metrics.csv`
| series_id | model | pit_p_value | crps_score |
| :--- | :--- | :--- | :--- |
| M4-1001 | ARIMA | 0.45 | 0.12 |

### CSV: `results/significance_test.csv`
| model_a | model_b | metric | p_value | is_significant |
| :--- | :--- | :--- | :--- | :--- |
| ARIMA | Prophet | coverage_deviation | 0.03 | True |

### JSON: `data/processed/split_metadata.json`
Records the split points for reproducibility.
```json
{
  "series_id": "M4-1001",
  "total_length": 100,
  "train_length": 80,
  "test_length": 20,
  "split_index": 80
}
```

## Data Flow
1.  **Load**: `loader.py` reads raw CSVs -> yields `TimeSeries` objects (streaming).
2.  **Split**: `splitter.py` divides `TimeSeries` -> `train`/`test` sets (80/20).
3.  **Fit**: `models/*.py` train on `train` -> generate `PredictiveInterval` for `test`.
4.  **Evaluate**: `metrics/*.py` compare `PredictiveInterval` vs `test_values` -> `CalibrationMetric`.
5.  **Aggregate**: `evaluation/runner.py` collects metrics -> writes CSVs.