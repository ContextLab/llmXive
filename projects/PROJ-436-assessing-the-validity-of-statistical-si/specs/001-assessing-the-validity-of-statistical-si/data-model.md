# Data Model: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

## Overview

This document defines the data structures used for configuration, simulation execution, and result aggregation. All data is stored in Parquet (for efficiency) or JSON (for configuration) formats.

## Entities

### 1. SimulationConfig
Defines the parameters for a single simulation run.

| Field | Type | Description |
| :--- | :--- | :--- |
| `dataset_id` | string | Identifier for the source dataset (e.g., "openml_42803"). |
| `missingness_mechanism` | enum | One of: `MCAR`, `MAR`, `MNAR`. |
| `missingness_rate` | float | Proportion of data to remove (e.g., 0.05, 0.10). |
| `outcome_type` | enum | `continuous` or `binary`. Determines test selection. |
| `seed` | integer | Random seed for reproducibility. |
| `n_iterations` | integer | Number of Monte Carlo iterations (default 2000). |
| `analysis_methods` | list[enum] | List of methods to run: `CC`, `MI`, `IPW`. |

### 2. ErrorMetric
Result of a single simulation iteration.

| Field | Type | Description |
| :--- | :--- | :--- |
| `config_id` | string | Hash of the `SimulationConfig`. |
| `iteration_id` | integer | Index of the iteration (0 to n-1). |
| `method` | enum | The analysis method used (CC, MI, IPW). |
| `p_value` | float | The p-value obtained from the hypothesis test. |
| `rejected` | boolean | True if `p_value < 0.05`. |
| `imputation_stats` | dict | Optional: Rubin's rules stats for MI (if applicable). |

### 3. ComparisonResult
Aggregated results for a specific condition (mechanism + rate + dataset).

| Field | Type | Description |
| :--- | :--- | :--- |
| `config_hash` | string | Unique hash of the condition. |
| `mechanism` | enum | MCAR, MAR, or MNAR. |
| `missingness_rate` | float | The rate used. |
| `method` | enum | CC, MI, or IPW. |
| `empirical_type1_error` | float | Proportion of rejections (sum(rejected) / n_iterations). |
| `binomial_p_value` | float | P-value from Binomial test against nominal 0.05. |
| `fdr_corrected_q` | float | FDR-corrected q-value across all conditions. |
| `tipping_point_flag` | boolean | True if this condition exceeds the threshold (10% relative increase) AND FDR-corrected p < 0.05. |

## Data Flow

1. **Input**: `SimulationConfig` (from `config.py`).
2. **Process**: `data_loader` fetches data -> `simulation` permutes treatment and masks -> `analysis` computes p-values.
3. **Output**: `ErrorMetric` records written to `data/processed/error_metrics.parquet`.
4. **Aggregate**: `metrics.py` aggregates `ErrorMetric` into `ComparisonResult` and writes to `data/processed/comparison_results.json`.

## File Structure

```text
data/
├── raw/
│   └── {dataset_name}.csv (or .parquet)
├── processed/
│   ├── error_metrics.parquet       # Granular iteration results
│   ├── comparison_results.json     # Aggregated statistics
│   └── tipping_points.csv          # Identified thresholds
└── checksums/
    └── manifest.json               # SHA256 of raw files
```