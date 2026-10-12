# Data Model: Calibration of Predictive Intervals for Time‑Series Forecasts

## Overview
Defines the canonical data structures that flow through the pipeline. All files are immutable under `data/raw/`; derived artifacts live under `data/processed/` and `results/`.

## Entities

### TimeSeries
| Attribute | Type | Description |
|-----------|------|-------------|
| `series_id` | `str` | Unique identifier (e.g., `M4-1001`, `UCI-E1`). |
| `timestamp` | `datetime[]` | Ordered timestamps. |
| `value` | `float[]` | Observations. |
| `frequency` | `str` | Temporal granularity (`hourly`, `daily`, `weekly`, `monthly`, `yearly`). |
| `train_values` | `float[]` | First [deferred] of `value`. |
| `test_values` | `float[]` | Last [deferred] of `value`. |

### PredictiveInterval
| Attribute | Type | Description |
|-----------|------|-------------|
| `series_id` | `str` | Foreign key to `TimeSeries`. |
| `model` | `str` | `ARIMA`, `Prophet`, or `LSTM`. |
| `horizon` | `int` | Forecast step (1‑step ahead, 2‑step, …). |
| `nominal_level` | `float` | 0.80 or 0.95. |
| `lower_bound` | `float` | Lower predictive bound. |
| `upper_bound` | `float` | Upper predictive bound. |

### CalibrationMetric
| Attribute | Type | Description |
|-----------|------|-------------|
| `series_id` | `str` | |
| `model` | `str` | |
| `nominal_level` | `float` | |
| `empirical_coverage` | `float` | Proportion of test points inside the interval. |
| `coverage_deviation` | `float` | `empirical_coverage - nominal_level`. |
| `pit_p_value_ks` | `float` | KS‑test p‑value (Constitution VI). |
| `pit_p_value_lb` | `float` | Ljung‑Box p‑value (Spec FR‑004). |
| `crps_score` | `float` | Continuous Ranked Probability Score. |

### SignificanceTestResult
| Attribute | Type | Description |
|-----------|------|-------------|
| `model_a` | `str` | |
| `model_b` | `str` | |
| `metric` | `str` | e.g., `coverage_deviation`. |
| `p_value` | `float` | Paired bootstrap p‑value. |
| `is_significant` | `bool` | `p_value < 0.05`. |

## File Formats

### `results/coverage.csv`
| series_id | model | nominal_level | empirical_coverage | coverage_deviation |
|-----------|-------|---------------|--------------------|--------------------|

### `results/distributional_metrics.csv`
| series_id | model | pit_p_value_ks | pit_p_value_lb | crps_score |

### `results/significance_test.csv`
| model_a | model_b | metric | p_value | is_significant |

### `results/conformal_results.csv`
| series_id | model | nominal_level | empirical_coverage_before | empirical_coverage_after | improvement_delta |

### `data/processed/split_metadata.json`
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
1. **Load** (`code/data/loader.py`) → streaming `TimeSeries`.  
2. **Split** (`code/data/splitter.py`) → `train_values` / `test_values`.  
3. **Fit** (`code/models/*.py`) → forecasts & intervals.  
4. **Evaluate** (`code/metrics/*.py`) → `CalibrationMetric`.  
5. **Aggregate** (`code/evaluation/runner.py`) → CSVs in `results/`.  

---
