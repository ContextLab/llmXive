# API Documentation: Metrics

This document provides the API reference for the evaluation metrics implemented in `code/metrics/`.
These metrics are used to assess the calibration of predictive intervals.

## Coverage Metrics

**Module**: `code/metrics/coverage.py`

Functions to compute empirical coverage rates and deviations.

### Functions

#### `compute_coverage(actual: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float`
Computes the empirical coverage rate.
- **Parameters**:
 - `actual`: True values.
 - `lower`: Lower bounds of the interval.
 - `upper`: Upper bounds of the interval.
- **Returns**: Coverage rate (0.0 to 1.0).

#### `compute_coverage_deviation(empirical: float, nominal: float) -> float`
Computes the deviation between empirical and nominal coverage.
- **Parameters**:
 - `empirical`: Observed coverage rate.
 - `nominal`: Expected coverage rate (e.g., 0.95).
- **Returns**: Absolute deviation.

#### `aggregate_coverage_results(results: List[Dict]) -> pd.DataFrame`
Aggregates coverage results from multiple series/models.

#### `coverage_to_dataframe(results: Dict) -> pd.DataFrame`
Converts coverage results dictionary to a pandas DataFrame.

---

## Probability Integral Transform (PIT) Metrics

**Module**: `code/metrics/pit.py`

Functions to calculate PIT, generate histograms, and perform uniformity tests.

### Functions

#### `calculate_pit(actual: float, forecast_dist: np.ndarray) -> float`
Calculates the PIT value for a single observation.
- **Parameters**:
 - `actual`: The true value.
 - `forecast_dist`: Array of samples from the predictive distribution.
- **Returns**: PIT value (0.0 to 1.0).

#### `generate_pit_histogram(pit_values: np.ndarray, bins: int = 20) -> Tuple[np.ndarray, np.ndarray]`
Generates histogram data for PIT values.
- **Returns**: Tuple of (counts, bin_edges).

#### `ljung_box_test(pit_values: np.ndarray, lags: int = 10) -> float`
Performs the Ljung-Box test for uniformity (autocorrelation check) on PIT values.
- **Note**: Uses Ljung-Box instead of Kolmogorov-Smirnov per FR-004.
- **Returns**: p-value.

#### `compute_pit_metrics(pit_values: np.ndarray) -> Dict[str, float]`
Computes all PIT-related metrics (mean, variance, Ljung-Box p-value).

#### `pit_metrics_to_dataframe(results: Dict) -> pd.DataFrame`
Converts PIT results to a DataFrame.

---

## Continuous Ranked Probability Score (CRPS)

**Module**: `code/metrics/crps.py`

Functions to calculate CRPS using `properscoring`.

### Functions

#### `compute_crps(actual: float, forecast_samples: np.ndarray) -> float`
Calculates the CRPS for a single observation.
- **Parameters**:
 - `actual`: True value.
 - `forecast_samples`: Array of samples from the predictive distribution.
- **Returns**: CRPS scalar.

#### `compute_crps_for_series(actual_series: np.ndarray, forecast_samples: np.ndarray) -> float`
Calculates the average CRPS for a series.

#### `aggregate_crps_results(results: List[Dict]) -> pd.DataFrame`
Aggregates CRPS results from multiple series/models.

#### `crps_to_dataframe(results: Dict) -> pd.DataFrame`
Converts CRPS results to a DataFrame.

---

## Usage Example

```python
from metrics.coverage import compute_coverage
from metrics.pit import ljung_box_test, calculate_pit
from metrics.crps import compute_crps
import numpy as np

# Coverage Example
actual = np.array([10, 12, 11, 13])
lower = np.array([8, 10, 9, 11])
upper = np.array([12, 14, 13, 15])
coverage = compute_coverage(actual, lower, upper)
print(f"Coverage: {coverage}")

# PIT Example
pit_val = calculate_pit(10.5, np.array([9, 10, 11, 12]))
pit_values = np.array([pit_val, 0.5, 0.3, 0.7])
p_value = ljung_box_test(pit_values)
print(f"Ljung-Box p-value: {p_value}")

# CRPS Example
crps = compute_crps(10.5, np.array([9, 10, 11, 12]))
print(f"CRPS: {crps}")
```