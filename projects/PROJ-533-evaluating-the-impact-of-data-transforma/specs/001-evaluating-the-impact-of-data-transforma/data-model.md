# Data Model: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Overview

This document defines the data structures used throughout the project, ensuring consistency between download, transformation, simulation, and aggregation phases. All data is stored in CSV, JSON, or Parquet formats with checksums preserved.

## Entities

### Dataset
Represents a public data source from UCI/OpenML.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| dataset_id | str | Unique identifier (e.g., `uci_har`, `openml_123`) | Primary key |
| source_url | str | Canonical URL of dataset | Must be verified or documented |
| sample_size | int | Number of rows | ≥30 |
| num_continuous | int | Number of continuous variables | ≥1 |
| num_groups | int | Number of group levels | ≥2 |
| shapiro_p | float | Shapiro-Wilk p-value | <0.05 for inclusion |
| missing_rate | float | Proportion of missing values | ≤0.10 for inclusion |
| checksum | str | SHA-256 hash of raw file | Non-empty |
| included | bool | Whether dataset passed filtering | True/False |

**Source**: `data/datasets.csv`

### Transformation
Represents one of three transformation methods applied to a variable.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| dataset_id | str | Foreign key to Dataset | |
| variable_name | str | Name of transformed variable | |
| method | str | Box-Cox, Yeo-Johnson, or rank-based | Enum |
| lambda_param | float | Optimized λ (for Box-Cox/Yeo-Johnson) | Null for rank-based |
| transformed_values | list | Transformed data | Non-empty |
| success | bool | Whether transformation succeeded | True/False |
| log_message | str | Intervention log (e.g., log-shift applied) | Optional |

**Source**: `data/processed/transformations/{dataset_id}_{method}.csv`

### TestResult
Represents outcome of a statistical test under a specific transformation.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| result_id | str | Unique identifier | Primary key |
| dataset_id | str | Foreign key to Dataset | |
| method | str | Transformation method | Enum |
| test_type | str | t-test, ANOVA, or Mann-Whitney U | Enum |
| p_value | float | P-value from test | 0.0–1.0 |
| significant | bool | p < α (default 0.05) | True/False |
| condition | str | null or alternative | Enum |
| effect_size | float | Cohen's d (for simulated data) | Null for real-world |
| iteration | int | Simulation iteration number | 1–1000 |
| seed | int | Random seed used | 42 (fixed) |

**Source**: `results/type1_error/{dataset_id}.csv`, `results/power/{effect_size}.csv`

### AggregatedResult
Summary of Type I error or power across datasets.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| method | str | Transformation method | Enum |
| test_type | str | t-test or ANOVA | Enum |
| metric | str | type1_error or power | Enum |
| mean | float | Mean estimate | |
| ci_lower | float | 95% bootstrap CI lower bound | |
| ci_upper | float | 95% bootstrap CI upper bound | |
| n_datasets | int | Number of datasets aggregated | ≥50 |
| alpha | float | Significance threshold used | 0.01, 0.05, or 0.1 |

**Source**: `results/aggregated/summary.csv`

## Data Flow

1. **Download**: `download_datasets.py` → `data/raw/` + `data/datasets.csv`
2. **Filter**: `filter_datasets.py` → `data/processed/filtered/` + update `datasets.csv`
3. **Transform**: `apply_transformations.py` → `data/processed/transformations/`
4. **Simulate Null**: `simulate_null.py` → `results/type1_error/`
5. **Simulate Power**: `simulate_power.py` → `results/power/`
6. **Aggregate**: `aggregate_results.py` → `results/aggregated/` + plots

## Integrity Constraints

- **Checksums**: All raw files checksummed and recorded in `data/checksums.csv` (FR-010).
- **Seeds**: Random seed 42 stored in `results/simulation_seeds.txt` (Constitution Principle VII).
- **Imputation**: Missing values imputed per variable; rate logged; >10% excluded.
- **Transformation Failures**: Logged with variable name and reason; skipped if irrecoverable.
