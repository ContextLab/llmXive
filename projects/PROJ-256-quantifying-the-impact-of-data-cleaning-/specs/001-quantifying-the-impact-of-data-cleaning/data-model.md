# Data Model: Quantifying the Impact of Data Cleaning

## Overview
The data model defines the JSON artefacts produced by the pipeline and the schemas used for validation. All files live under `data/processed/` (except raw downloads under `data/raw/`).

## Core Entities

| File | Description | Key Fields |
|------|-------------|------------|
| `dataset_metadata.json` | Metadata for each raw dataset. | `dataset_id`, `outcome_column`, `n_rows`, `missingness_rate`, `source_url`, `checksum` |
| `baseline_metrics.json` | Baseline statistical results on raw data. | `dataset_id`, `test_type`, `p_value`, `p_value_delta` (baseline condition yields a neutral value), `ci_lower`, `ci_upper`, `effect_size`, `assumptions_met` |
| `analysis_results.json` | Flat list of per‑test objects (t‑test or regression) for baseline and each cleaning variant. | `dataset_id`, `strategy_id`, `test_type`, `p_value`, `ci_lower`, `ci_upper`, `effect_size`, `sample_size_final`, `is_valid` |
| `cleaned_metrics.json` | Results for each cleaning variant. | `dataset_id`, `variant_id`, `p_value`, `p_value_delta`, `direction`, `ci_lower`, `ci_upper`, `ci_overlap`, `effect_size_change`, `assumptions_met`, `fpr`, `adjusted_p_value`, `metadata` |
| `null_fpr_metrics.json` | False‑positive‑rate estimates from permutation runs (outcome permuted after cleaning). | `dataset_id`, `outlier_k`, `fpr`, `num_permutations`, `seed` |
| `bootstrap_metrics.json` | Bootstrap confidence intervals for each cleaned variant. | `dataset_id`, `cleaning_variant`, `bootstrap_ci_lower`, `bootstrap_ci_upper`, `iterations` |
| `sensitivity_metrics.json` | Stratified results by size and missingness bins, including interaction terms between cleaning method and missingness. | `size_bin`, `missingness_level`, `datasets` (list of `dataset_id`s), aggregated metrics (mean `p_value_delta`, mean `ci_overlap`, interaction effect sizes, etc.) |
| `comparison_report.json` | Final report aggregating all delta metrics, CI overlap, effect‑size changes, and FPR values across datasets. | `overall_delta_summary`, `per_dataset` (list of objects mirroring `cleaned_metrics`), `fpr_summary`, `power_analysis_summary` |
| `hypothesis_test_results.json` | Results of paired Wilcoxon tests on Δ‑metrics. | `test_name`, `statistic`, `p_value`, `effect` |
| `power_analysis.txt` | Plain‑text summary of the a priori power calculation (Wilcoxon). | N/A (text) |

## Relationships
- Each `dataset_id` links rows across all metric files.  
- `variant_id` uniquely identifies a cleaning configuration (outlier threshold, imputation method, encoding method).  
- `strategy_id` in `analysis_results.json` mirrors `variant_id` for the corresponding statistical test.  
- `size_bin` and `missingness_level` are derived from `dataset_metadata.json` and the synthetic missingness injection step.

## Storage & Access Pattern
1. **Download** raw files → `data/raw/`.  
2. **Validate** raw files against `dataset.schema.yaml`.  
3. **Generate** `dataset_metadata.json`.  
4. **Baseline** → `baseline_metrics.json` **and** `analysis_results.json`.  
5. **Cleaning loops** → `cleaned_metrics.json`, `null_fpr_metrics.json`, `bootstrap_metrics.json`, additional entries in `analysis_results.json`.  
6. **Aggregate** → `sensitivity_metrics.json`, `comparison_report.json`.  

All reads/writes are performed with `pandas.read_json` / `DataFrame.to_json(orient="records")` to keep memory usage low.

---

