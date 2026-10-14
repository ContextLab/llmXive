# Data Model: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

## Overview
Defines the JSON‑Schema‑validated structures used throughout the pipeline. All files are stored under `data/processed/` as Parquet (iteration‑level) or JSON (aggregated) for easy validation against the contracts.

## Entities

### 1. SimulationConfig
Configuration for a single simulation condition.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | Identifier of the source dataset (e.g., `"mcar_parquet_0"`). |
| `missingness_mechanism` | enum | `"MCAR"`, `"MAR"` or `"MNAR"` (or `"TD-MCAR"`, `"TD-MAR"`, `"TD-MNAR"` for treatment‑dependent variants). |
| `missingness_rate` | float | Proportion of rows to mask (0.05 – 0.40). |
| `outcome_type` | enum | `"continuous"` or `"binary"` (drives test selection). |
| `seed` | integer | Random seed for reproducibility. |
| `n_iterations` | integer | Number of Monte‑Carlo repetitions (default 2000). |
| `analysis_methods` | list[enum] | Subset of `["CC","MI","IPW"]`. |

### 2. ErrorMetric
Result of a single Monte‑Carlo iteration (validated by `error_metric.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `config_id` | string | Hash of the associated `SimulationConfig`. |
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
| `mechanism` | enum | `"MCAR"`, `"MAR"` or `"MNAR"` (or TD‑variants). |
| `missing_rate` | number | Proportion of missing data. |
| `method` | enum | `"CC"`, `"MI"` or `"IPW"`. |
| `p_value` | number | Calculated p‑value (0–1). |
| `is_significant` | boolean | `true` if `p_value < 0.05`. |
| `seed` | integer | Random seed used for this iteration. |

### 4. ComparisonResult
Aggregated metrics for a given condition (one mechanism × rate × dataset) (validated by `comparison_result.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `config_hash` | string | SHA‑256 of the `SimulationConfig`. |
| `mechanism` | enum | `"MCAR"`, `"MAR"` or `"MNAR"` (or TD‑variants). |
| `missingness_rate` | float | Same as in `SimulationConfig`. |
| `method` | enum | `"CC"`, `"MI"` or `"IPW"`. |
| `empirical_type1_error` | float | Proportion of rejections across iterations. |
| `binomial_p_value` | float | Binomial test p‑value vs. nominal 0.05. |
| `fdr_corrected_q` | float | BH‑adjusted q‑value across all conditions. |
| `tipping_point_flag` | boolean | `true` if error > 1.10·0.05 **and** q < 0.05. |

### 5. SimulationOutput
Final report‑level object (validated by `simulation_output.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `condition_id` | string | Unique identifier (hash of dataset + mechanism + rate). |
| `dataset_id` | string | Source dataset identifier. |
| `mechanism` | enum | `"MCAR"`, `"MAR"` or `"MNAR"` (or TD‑variants). |
| `missing_rate` | float | Missingness proportion. |
| `n_iterations` | integer | Number of Monte‑Carlo runs. |
| `error_rate_CC` | float | Empirical Type I error for CC. |
| `error_rate_MI` | float | Empirical Type I error for MI. |
| `error_rate_IPW` | float | Empirical Type I error for IPW. |
| `binomial_p_CC` | float | Binomial test p‑value for CC. |
| `adjusted_p_CC` | float | BH‑adjusted q‑value for CC. |
| `tipping_point_flag` | boolean | `true` if CC exceeds the tipping‑point criteria. |
| `cc_mi_ratio` | float | `error_rate_CC / error_rate_MI`. |
| `validated_tipping_point` | boolean | `true` if `cc_mi_ratio > 2` and q < 0.05. |
| `validation_status` | enum | `"PASS"`, `"FLAGGED"` or `"SKIPPED"` (e.g., dataset too small). |

## Data Flow
1. **Load** → `SimulationConfig` (JSON).  
2. **Preparation** → synthesize treatment/outcome if needed.  
3. **Simulation** → generate `ErrorMetric` rows **and** `PValueDistribution` records → stored as Parquet.  
4. **Aggregation** → compute `ComparisonResult` (per‑condition) → stored as JSON.  
5. **Final Reporting** → `SimulationOutput` → JSON + CSV summary + figures.

## File Layout
```text
data/
├── raw/
│   ├── mcar_parquet_0.parquet
│   ├── mcar_parquet_1.parquet
│   ├── mar_csv_0.csv
│   └── …
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

