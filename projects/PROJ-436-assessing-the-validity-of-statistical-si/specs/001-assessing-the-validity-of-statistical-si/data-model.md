# Data Model: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

## Overview
Defines the JSON‑Schema‑validated structures used throughout the pipeline. All files are stored under `data/processed/` as Parquet (iteration‑level) or JSON (aggregated) for easy validation against the contracts.

## Entities

### 1. SimulationConfig
Configuration for a single simulation condition.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | Identifier of the source dataset (e.g., `"rct_1"`). |
| `missingness_mechanism` | enum | `"MCAR"`, `"MAR"` or `"MNAR"`. |
| `missingness_rate` | number | Proportion of rows to mask (0.05 – 0.40). |
| `outcome_type` | enum | `"continuous"` or `"binary"` (drives test selection). |
| `seed` | integer | Random seed for reproducibility. |
| `n_iterations` | integer | Number of Monte‑Carlo repetitions (≥ 15000). |
| `analysis_methods` | list[enum] | Subset of `["CC","MI","IPW"]`. |

### 2. ErrorMetric
Result of a single Monte‑Carlo iteration (validated by `error_metric.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `config_id` | string | SHA‑256 hash of the associated `SimulationConfig`. |
| `iteration_id` | integer | 0‑based index of the iteration. |
| `method` | enum | `"CC"`, `"MI"` or `"IPW"`. |
| `p_value` | number | Two‑sided p‑value from the hypothesis test. |
| `rejected` | boolean | `true` if `p_value < 0.05`. |
| `imputation_stats` | object (optional) | Rubin’s pooled estimate, SE, and df (MI only). |

### 3. PValueDistribution
Per‑iteration p‑value record (validated by `p_value_distribution.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique identifier for the simulation run. |
| `dataset_id` | string | Source dataset identifier. |
| `mechanism` | enum | `"MCAR"`, `"MAR"` or `"MNAR"`. |
| `missing_rate` | number | Proportion of missing data. |
| `method` | enum | `"CC"`, `"MI"` or `"IPW"`. |
| `p_value` | number | Calculated p‑value (0 – 1). |
| `is_significant` | boolean | `true` if `p_value < 0.05`. |
| `seed` | integer | Random seed used for this iteration. |

### 4. ComparisonResult
Aggregated metrics for a given condition (one mechanism × rate × dataset) (validated by `comparison_result.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `config_hash` | string | SHA‑256 of the `SimulationConfig`. |
| `mechanism` | enum | `"MCAR"`, `"MAR"` or `"MNAR"`. |
| `missingness_rate` | float | Same as in `SimulationConfig`. |
| `method` | enum | `"CC"`, `"MI"` or `"IPW"`. |
| `empirical_type1_error` | float | Proportion of rejections across iterations. |
| `ks_p_value` | float | Kolmogorov‑Smirnov test p‑value vs. Uniform(0,1). |
| `tipping_point_flag` | boolean | `true` if error > 0.055 (no binomial test). |
| `cc_mi_ratio` | float (optional) | `error_CC / error_MI` (only for CC rows). |
| `mcnemar_p_value` | float (optional) | McNemar’s test p‑value comparing CC vs. MI/IPW. |
| `ratio_bootstrap_ci` | array[float] (optional) | 95 % CI for the error‑rate ratio (lower, upper). |
| `validated_tipping_point` | boolean (optional) | `true` if lower CI > 2 **and** `mcnemar_p_value` < 0.05. |
| `additional_notes` | string (optional) | Free‑form notes. |

### 5. SimulationOutput
Final report‑level object (validated by `simulation_output.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `condition_id` | string | Unique identifier for the simulation condition. |
| `dataset_id` | string | Source dataset identifier. |
| `mechanism` | enum | `"MCAR"`, `"MAR"` or `"MNAR"`. |
| `missing_rate` | number | Proportion of missing data. |
| `n_iterations` | integer | Number of Monte Carlo iterations. |
| `error_rate_CC` | number | Empirical Type I error rate for Complete‑Case analysis. |
| `error_rate_MI` | number | Empirical Type I error rate for Multiple Imputation. |
| `error_rate_IPW` | number | Empirical Type I error rate for Inverse Probability Weighting. |
| `ks_p_value_CC` | number | KS test p‑value for CC p‑value distribution. |
| `tipping_point_flag` | boolean | `true` if CC error > 0.055. |
| `cc_mi_ratio` | number | `error_rate_CC / error_rate_MI`. |
| `validated_tipping_point` | boolean | `true` if lower bootstrap CI > 2 **and** McNemar’s p < 0.05. |
| `validation_status` | enum | `"PASS"`, `"FLAGGED"` (e.g., N < 100) or `"SKIPPED"`. |
| `notes` | string (optional) | Additional commentary. |

## Data Flow
1. **Load** → `SimulationConfig` (JSON).  
2. **Preparation** → synthesize treatment/outcome if needed.  
3. **Simulation** → generate `ErrorMetric` rows **and** `PValueDistribution` records → stored as Parquet.  
4. **Aggregation** → compute `ComparisonResult` per condition → stored as JSON.  
5. **Final Reporting** → `SimulationOutput` → JSON + CSV summary + figures.

## File Layout
```text
data/
├── raw/
│   ├── rct_1.jsonl
│   ├── rct_2.csv
│   ├── mcar_0.parquet
│   ├── mcar_1.parquet
│   ├── mar_0.csv
│   ├── mar_1.parquet
│   └── mar_2.jsonl
├── processed/
│   ├── error_metrics.parquet          # All iteration‑level records
│   ├── p_value_distribution.parquet   # Per‑iteration p‑values
│   ├── comparison_results.json        # Aggregated per‑condition stats
│   ├── simulation_outputs.json        # Final report objects
│   └── tipping_points.csv             # Human‑readable table of flags
└── checksums/
    └── manifest.json                  # SHA‑256 for each raw file
```

---

