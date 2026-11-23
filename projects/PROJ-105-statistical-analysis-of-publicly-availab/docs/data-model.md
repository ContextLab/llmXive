# Data Model: Flight Delay Statistical Analysis

This document defines the core entities, data schemas, and file formats used throughout the `PROJ-105` statistical analysis pipeline.

## 1. Core Entities

### 1.1 DelayRecord
Represents a single flight delay observation after preprocessing.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `flight_date` | `YYYY-MM-DD` | Date of the flight | Required |
| `carrier` | `str` | Airline carrier code (e.g., 'AA') | 2-4 chars |
| `total_delay` | `float` | Sum of arrival and departure delays | >= 0 |
| `arr_delay` | `float` | Arrival delay in minutes | >= 0 |
| `dep_delay` | `float` | Departure delay in minutes | >= 0 |
| `is_anomaly` | `bool` | Flag if delay > 1440 minutes | False if valid |
| `is_data_error` | `bool` | Flag if delay > 10000 minutes | False if valid |

### 1.2 DistributionModel
Represents a fitted statistical distribution and its parameters.

| Field | Type | Description |
|:--- |:--- |:--- |
| `name` | `str` | Distribution name (e.g., 'Pareto', 'Gamma') |
| `parameters` | `dict` | MLE estimated parameters (e.g., `{'alpha': 2.1, 'x_min': 45.0}`) |
| `metrics` | `dict` | Goodness-of-fit metrics (AIC, BIC, KS, AD) |
| `converged` | `bool` | Whether the optimizer converged successfully |

### 1.3 TailIndexEstimate
Result of the Hill estimator analysis.

| Field | Type | Description |
|:--- |:--- |:--- |
| `alpha` | `float` | Estimated tail index (1/alpha is the power law exponent) |
| `x_min` | `float` | Threshold used for estimation |
| `k` | `int` | Number of upper order statistics used |
| `stability_score` | `float` | Variance of the sliding window estimate |

## 2. File Formats

### 2.1 Raw Input: `data/raw/bts_YYYY.csv`
Original CSV downloaded from the Bureau of Transportation Statistics (BTS).
- **Source**: `
- **Format**: CSV with headers.
- **Key Columns**: `ArrDelay`, `DepDelay`, `Carrier`, `FlightDate`.

### 2.2 Cleaned Data: `data/processed/cleaned_delays.csv`
Preprocessed dataset ready for modeling.
- **Format**: CSV.
- **Columns**: `flight_date`, `carrier`, `total_delay`, `arr_delay`, `dep_delay`, `is_anomaly`, `is_data_error`.
- **Filtering**: Rows with `is_data_error=True` are excluded from primary analysis but retained in the file with flags.

### 2.3 Summary Report: `data/results/summary_report.json`
High-level statistics of the data processing pipeline.
```json
{
 "total_records": 123456,
 "valid_records": 120000,
 "retention_rate": 0.972,
 "anomaly_count": 150,
 "error_count": 5,
 "runtime_seconds": 120.5
}
```

### 2.4 Model Comparison: `data/results/model_comparison.json`
Metrics for all fitted distributions on the tail subset.
```json
{
 "x_min": 45.0,
 "models": [
 {
 "name": "Pareto",
 "parameters": {"alpha": 2.15},
 "metrics": {"aic": 1200.5, "bic": 1205.2, "ks": 0.02, "ad": 0.15}
 },
...
 ]
}
```

### 2.5 Validation Status: `data/results/validation_status.json`
Pass/Fail status for all success criteria (SC-001 to SC-011).
```json
{
 "SC-001_retention_rate": "PASS",
 "SC-002_model_count": "PASS",
 "SC-003_hill_index": "PASS",
...
}
```

## 3. Data Flow

1. **Ingest**: `data_loader.py` downloads raw BTS CSV.
2. **Preprocess**: `preprocessing.py` cleans, filters, and generates `cleaned_delays.csv`.
3. **Fit**: `models.py` estimates parameters and generates `model_comparison.json`.
4. **Diagnose**: `diagnostics.py` runs Hill estimator and bootstrap tests, generating `tail_index_estimate.json` and `bootstrap_gof.json`.
5. **Validate**: `validation.py` checks all criteria and outputs `validation_status.json`.
