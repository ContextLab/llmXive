# Data Model: Quantifying the Impact of Data Cleaning

## Overview
The pipeline produces three primary JSON artifacts, each conforming to a strict schema (see `contracts/`).

### 1. Baseline Metrics (`data/processed/baseline_metrics.json`)
A list of records, one per dataset‑predictor pair.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | Unique identifier (e.g., HuggingFace repo name). |
| `predictor` | string | Column name used as independent variable. |
| `outcome` | string | Column name used as dependent variable (as defined in `dataset.schema.yaml`). |
| `test_type` | enum[`ttest`, `ols`] | Statistical test performed. |
| `p_value` | number (≥0, ≤1) | Two‑sided p‑value, **≥ 3‑decimal precision**. |
| `ci_lower` | number | 95 % confidence interval lower bound for effect size. |
| `ci_upper` | number | 95 % confidence interval upper bound for effect size. |
| `effect_size` | number | Cohen’s d for t‑tests or standardized β for OLS. |
| `bootstrap_iterations` | integer | Number of bootstrap resamples (≥ 1000). |
| `delta_ci_low` | number (optional) | Lower bound of bootstrap CI for *delta* vs. cleaned (filled later). |
| `delta_ci_high` | number (optional) | Upper bound of bootstrap CI for *delta* vs. cleaned (filled later). |
| `assumption_passed` | boolean (optional) | Whether all classical assumptions held (True) or a robust fallback was used (False). |

### 2. Cleaned Metrics (`data/processed/cleaned_metrics.json`)
Same schema as baseline, plus cleaning metadata.

| Additional Field | Type | Description |
|------------------|------|-------------|
| `cleaning_variant` | enum[`outlier`, `impute_mean`, `impute_median`, `impute_knn`, `recoding`] | Which cleaning step produced this dataset. |
| `outlier_k` | number (optional) | IQR multiplier used (only for `outlier`). |
| `rows_removed` | integer (optional) | Number of rows dropped by outlier detection. |
| `missing_before` | integer (optional) | Count of missing cells before imputation. |
| `missing_after` | integer (optional) | Count after imputation (should be eliminated). |
| `variance_reduction` | number (optional) | Percent reduction in outcome variance after cleaning (warn if ≥ 20 %). |
| `assumption_passed` | boolean (optional) | True if robust fallback not needed. |

### 3. Null FPR Metrics (`data/processed/null_fpr_metrics.json`)
Aggregated false‑positive‑rate per dataset and outlier threshold.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | Identifier of the original dataset. |
| `outlier_k` | number | IQR multiplier used for this permutation batch. |
| `fpr` | number (≥0, ≤1) | Proportion of tests with corrected `p < 0.05` across all permutations. |
| `num_permutations` | integer | Number of permutation datasets generated (≥ 1000). |
| `seed` | integer | Random seed used for permutation generation. |

All numeric fields will be serialized with at least three decimal places (e.g., a typical three‑decimal representation).

## Data Flow Diagram (conceptual)

```
data/raw/  --> data_loader.py --> raw DataFrames
   |
   v
analysis.py (baseline + assumption checks) --> baseline_metrics.json
   |
   v
cleaning.py (outlier, impute, recode) --> cleaned DataFrames + metadata
   |
   v
analysis.py (cleaned + assumption checks) --> cleaned_metrics.json
   |
   v
threshold sweep (k loop) --> additional rows in cleaned_metrics.json
   |
   v
permutation generator (shuffle outcome) --> null datasets
   |
   v
analysis.py (null) --> null_fpr_metrics.json
   |
   v
reporting.py (figures + summary) --> output/figures/
```

## Contract Validation Integration
* **Dataset ingestion** – Every raw dataset is validated against `contracts/dataset.schema.yaml` immediately after download.  
* **Baseline & cleaned analyses** – Each statistical result is first wrapped in an `analysis_result` object and validated against `contracts/analysis_result.schema.yaml`, then written to the appropriate metrics file which is subsequently validated against `baseline_metrics.schema.yaml` or `cleaned_metrics.schema.yaml`.  
* **Null FPR** – After permutation runs, the aggregated FPR record is validated against `contracts/null_fpr_metrics.schema.yaml`.  

These validation steps guarantee reproducibility, data hygiene, and single‑source‑of‑truth compliance as mandated by the Constitution.

## Statistical Sensitivity & Variance Estimation
All delta metrics are accompanied by bootstrap 95 % confidence intervals (≥ 1000 iterations). Sensitivity analyses across dataset size and missingness thresholds are logged in `data/processed/sensitivity_report.json`.
