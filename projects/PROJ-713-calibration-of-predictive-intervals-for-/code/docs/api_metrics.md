# Metrics API Documentation

This document provides the API reference for the evaluation metrics implemented in `code/metrics/`.
These metrics are designed to assess the calibration and accuracy of predictive intervals.

---

## Coverage Metrics

**File**: `code/metrics/coverage.py`

**Description**:
Calculates empirical coverage rates and deviations against nominal confidence levels.

### Functions

- `compute_coverage(actual: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float`:
 Calculates the proportion of actual values falling within the predicted interval.
 - `actual`: Ground truth values.
 - `lower`: Lower bounds of the intervals.
 - `upper`: Upper bounds of the intervals.
 - **Returns**: Float between 0 and 1.

- `compute_coverage_deviation(empirical: float, nominal: float) -> float`:
 Calculates the absolute difference between empirical and nominal coverage.
 - **Returns**: Absolute deviation.

- `aggregate_coverage_results(results: List[Dict]) -> pd.DataFrame`:
 Aggregates coverage results from multiple series/models into a single DataFrame.

- `coverage_to_dataframe(results: Dict) -> pd.DataFrame`:
 Converts raw coverage results dictionary to a pandas DataFrame for export.

---

## Probability Integral Transform (PIT) Metrics

**File**: `code/metrics/pit.py`

**Description**:
Computes PIT values and tests for uniformity (calibration) using the Ljung-Box test.
**Note**: Kolmogorov-Smirnov test is explicitly NOT used per specification (FR-004).

### Functions

- `calculate_pit(forecast_dist: np.ndarray, actual: float) -> float`:
 Computes the PIT value for a single observation given a forecast distribution (samples).
 - `forecast_dist`: Array of samples from the predictive distribution.
 - `actual`: The observed value.
 - **Returns**: PIT value in [0, 1].

- `generate_pit_histogram(pit_values: np.ndarray, bins: int = 20) -> Tuple[np.ndarray, np.ndarray]`:
 Generates histogram data for PIT values to visualize uniformity.
 - **Returns**: (bin_edges, counts).

- `ljung_box_test(pit_values: np.ndarray, lags: int = 10) -> Tuple[float, float]`:
 Performs the Ljung-Box test on PIT values to detect autocorrelation (deviation from uniformity).
 - **Returns**: (Ljung-Box statistic, p-value).

- `compute_pit_metrics(pit_values: np.ndarray) -> Dict[str, Any]`:
 Aggregates PIT metrics including mean, variance, and Ljung-Box test results.

---

## Continuous Ranked Probability Score (CRPS)

**File**: `code/metrics/crps.py`

**Description**:
Calculates the CRPS using `properscoring`, compatible with both Gaussian and Empirical CDF intervals.

### Functions

- `compute_crps(forecast_samples: np.ndarray, actual: float) -> float`:
 Computes the CRPS for a single observation.
 - `forecast_samples`: Array of samples from the predictive distribution.
 - `actual`: The observed value.
 - **Returns**: CRPS score (lower is better).

- `compute_crps_for_series(forecast_samples: np.ndarray, actual_series: np.ndarray) -> float`:
 Computes the mean CRPS over a series of forecasts.

- `aggregate_crps_results(results: List[Dict]) -> pd.DataFrame`:
 Aggregates CRPS results from multiple series/models.

- `crps_to_dataframe(results: Dict) -> pd.DataFrame`:
 Converts raw CRPS results dictionary to a pandas DataFrame.

---

## Usage Example

```python
from metrics.coverage import compute_coverage
from metrics.pit import calculate_pit, ljung_box_test
from metrics.crps import compute_crps
import numpy as np

# Coverage
actual = np.array([10, 12, 11])
lower = np.array([8, 9, 10])
upper = np.array([12, 15, 13])
coverage = compute_coverage(actual, lower, upper)

# PIT
pit_vals = [calculate_pit(np.random.normal(10, 1, 100), 10.5) for _ in range(50)]
lb_stat, lb_pval = ljung_box_test(np.array(pit_vals))

# CRPS
samples = np.random.normal(10, 1, 1000)
crps_score = compute_crps(samples, 10.5)
```
