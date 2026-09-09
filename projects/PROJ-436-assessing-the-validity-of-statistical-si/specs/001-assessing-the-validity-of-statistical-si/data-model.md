# Data Model: Assessing the Validity of Statistical Significance in RCTs with Missing Data

## Overview

This document defines the data structures, schemas, and storage formats for the simulation engine. All data is stored in `data/` (raw/derived) and `results/` (outputs).

## Data Entities

### 1. SimulationConfig
Defines the parameters for a single simulation run.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | `str` | Identifier for the source dataset (e.g., "malawi-proxy"). |
| `mechanism` | `str` | One of `MCAR`, `MAR`, `MNAR`. |
| `missing_rate` | `float` | Proportion of missing data (e.g., 0.10). |
| `method` | `str` | One of `CC`, `MI`, `IPW`. |
| `outcome_type` | `str` | `continuous` or `binary`. |
| `seed` | `int` | Random seed for reproducibility. |

### 2. ErrorMetric
Result of a single simulation iteration.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `str` | Unique identifier for the run. |
| `p_value` | `float` | Calculated p-value. |
| `is_significant` | `bool` | `True` if $p < 0.05$. |
| `method` | `str` | Analysis method used. |
| `missing_rate` | `float` | Applied missingness rate. |
| `mechanism` | `str` | Missingness mechanism. |

### 3. PowerMetric
Result of a single power analysis iteration (alternative hypothesis).

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `str` | Unique identifier for the run. |
| `p_value` | `float` | Calculated p-value. |
| `is_significant` | `bool` | `True` if $p < 0.05$. |
| `method` | `str` | Analysis method used. |
| `effect_size` | `float` | True effect size used (e.g., 0.5). |

### 4. ComparisonResult
Aggregated results for a specific condition (dataset, mechanism, rate).

| Field | Type | Description |
|-------|------|-------------|
| `condition_id` | `str` | Composite key of dataset, mechanism, rate. |
| `n_iterations` | `int` | Number of Monte Carlo iterations (sufficient for convergence). |
| `error_rate_CC` | `float` | Empirical Type I error for CC. |
| `error_rate_MI` | `float` | Empirical Type I error for MI. |
| `error_rate_IPW` | `float` | Empirical Type I error for IPW. |
| `binomial_p_CC` | `float` | P-value from Binomial test for CC. |
| `adjusted_p_CC` | `float` | BH-adjusted p-value for CC. |
| `tipping_point_flag` | `bool` | `True` if `error_rate_CC` > 0.055 AND `adjusted_p_CC` < 0.05. |
| `cc_mi_ratio` | `float` | Ratio of CC error to MI error. |
| `validated_tipping_point` | `bool` | `True` if `cc_mi_ratio` > 2.0. |
| `validation_status` | `str` | Status of data validity check (e.g., "PASS", "FLAGGED"). |

## File Formats

### Raw Data (`data/raw/`)
- **Format**: Parquet or CSV (original format).
- **Naming**: `{source_name}_{checksum_sha256}.parquet`
- **Constraint**: Immutable.

### Derived Data (`data/derived/`)
- **Format**: Parquet.
- **Content**: Permutated treatment, synthetic outcome (if needed), and missingness masks.
- **Naming**: `{source_name}_permuted_{checksum_sha256}.parquet`

### Simulation Outputs (`results/simulation_outputs/`)
- **Format**: CSV.
- **Files**:
  - `error_rates.csv`: Aggregated results (ComparisonResult).
  - `p_values.csv`: Multiple p-values per condition (ErrorMetric).
  - `power_rates.csv`: Power analysis results (PowerMetric).
  - `tipping_points.json`: Identified thresholds.

## Data Flow

1. **Download**: `data_loader.py` fetches from verified URLs -> `data/raw/`.
2. **Permute**: `main.py` permutes treatment -> `data/derived/`.
3. **Validate**: `data_loader.py` checks covariate-outcome correlation for MAR validity.
4. **Simulate**: `missingness.py` generates masks -> In-memory.
5. **Analyze**: `analysis.py` computes p-values -> `results/`.
6. **Aggregate**: `metrics.py` calculates error rates, applies BH correction, and computes ratios -> `results/`.
7. **Validate**: `metrics.py` validates output against `contracts/` schemas before writing.