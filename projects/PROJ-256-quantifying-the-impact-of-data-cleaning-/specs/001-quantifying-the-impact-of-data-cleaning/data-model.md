# Data Model: Quantifying the Impact of Data Cleaning

## Overview
All pipeline artefacts are JSON (or JSONL) files stored under `data/processed/`. Each file conforms to a strict JSON schema located in `contracts/`. The schemas guarantee type safety, required fields, and numeric precision (≥ 3 decimal places).

## Core Artefacts

| File | Description | Key Fields |
|------|-------------|------------|
| `dataset_metadata.json` | Per‑dataset metadata (outcome column, size, missingness proportion). | `dataset_id`, `outcome_column`, `n_samples`, `missingness_proportion`, `checksum` |
| `baseline_metrics.json` | Baseline statistical results on raw data. | `dataset_id`, `test_type`, `p_value`, `ci_lower`, `ci_upper`, `effect_size`, `assumptions_met` |
| `cleaned_metrics.json` | Metrics for each cleaning variant (outlier threshold, imputation, encoding). | `dataset_id`, `variant_id`, `p_value`, `adjusted_p_value`, `ci_lower`, `ci_upper`, `effect_size`, `effect_size_change`, `direction`, `ci_overlap`, `p_value_delta`, `assumptions_met`, `robust_test_used`, `metadata` (rows_removed, missing_before, missing_after, variance_reduction) |
| `null_fpr_metrics.json` | Permutation‑based false‑positive‑rate estimates. | `dataset_id`, `variant_id`, `missingness_mechanism`, `fpr`, `fpr_ci_lower`, `fpr_ci_upper` |
| `bootstrap_metrics.json` | Bootstrap confidence intervals for each cleaned variant. | `dataset_id`, `cleaning_variant`, `bootstrap_ci_lower`, `bootstrap_ci_upper`, `iterations` |
| `sensitivity_metrics.json` | Results of the two‑way ANOVA / mixed‑effects model across size and missingness bins. | `size_bin`, `missingness_level`, `effect_size_change_mean`, `anova_f`, `anova_p` |
| `hypothesis_test_results.json` | Wilcoxon signed‑rank test on `effect_size_change` (per cleaning factor) plus Holm‑corrected p‑values. | `test_factor`, `test_statistic`, `p_value_raw`, `p_value_holm`, `reject_null` |
| `comparison_report.json` | Aggregated delta metrics for the final paper. | `overall_effect_size_change_mean`, `overall_ci_overlap_mean`, `overall_fpr_mean`, `variant_summary` (list) |
| `power_analysis.txt` | Plain‑text report of a priori power calculations (t‑test and Wilcoxon). | — (free‑form text) |

## Schema Files (located in `contracts/`)

| Schema | Purpose |
|--------|---------|
| `dataset.schema.yaml` | Validates raw dataset shape (required columns, outcome type, checksum). |
| `baseline_metrics.schema.yaml` | Ensures baseline metrics contain required numeric fields with ≥ 3‑decimal precision. |
| `cleaned_metrics.schema.yaml` | Validates each cleaning‑variant entry, including metadata dict and the `robust_test_used` field. |
| `null_fpr_metrics.schema.yaml` | Checks permutation FPR structure and confidence interval fields. |
| `comparison_report.schema.yaml` | Guarantees the final aggregated report matches expected keys and types. |
| `bootstrap_metrics.schema.yaml` | Validates bootstrap variance artefacts (added validation step). |
| `hypothesis_test_results.schema.yaml` | (Required by spec) validates the structure of `hypothesis_test_results.json`. |

All schemas follow the JSON‑Schema draft‑07 syntax, expressed in YAML for readability.

---


