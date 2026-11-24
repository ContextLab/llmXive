# Data Model: Quantifying the Impact of Data Cleaning

## Overview
All pipeline artefacts are JSON files stored under `data/processed/`. Each artefact is validated against a JSON‑Schema located in `contracts/`. Numeric fields are rounded to at least three‑decimal places as required by SC‑002.

## Core Artefacts

| File | Description | Key Fields |
|------|-------------|------------|
| `dataset_metadata.json` | Per‑dataset meta‑information (outcome column, sample size, missingness proportion, checksum). | `dataset_id`, `outcome_column`, `n_samples`, `missingness_proportion`, `checksum` |
| `baseline_metrics.json` | Baseline statistical results on raw data. | `dataset_id`, `test_type`, `p_value`, `ci_lower`, `ci_upper`, `effect_size`, `assumptions_met` |
| `cleaned_metrics.json` | Results for each cleaning variant, including delta metrics and cleaning metadata. | `dataset_id`, `variant_id`, `p_value`, `adjusted_p_value`, `ci_lower`, `ci_upper`, `effect_size`, `effect_size_change`, `direction`, `ci_overlap`, `p_value_delta`, `assumptions_met`, `robust_test_used`, `metadata` (rows_removed, missing_before, missing_after, variance_reduction), `cohens_d` (optional), `r_squared` (optional), `effect_size_cv` (optional) |
| `bootstrap_metrics.json` | Bootstrap confidence intervals for each cleaned variant. | `dataset_id`, `cleaning_variant`, `bootstrap_ci_lower`, `bootstrap_ci_upper`, `iterations` |
| `null_fpr_metrics.json` | Permutation‑based false‑positive‑rate estimates. | `dataset_id`, `variant_id`, `missingness_mechanism`, `fpr`, `fpr_ci_lower`, `fpr_ci_upper` |
| `sensitivity_metrics.json` | Two‑way ANOVA (size × missingness) results, with assumption checks. | `size_bin`, `missingness_level`, `effect_size_change_mean`, `anova_f`, `anova_p`, `assumptions_met` |
| `hypothesis_test_results.json` | Wilcoxon signed‑rank test on `effect_size_change` per cleaning factor, plus H2 stability correlations; raw p‑values only. | `test_factor`, `test_statistic`, `p_value_raw`, `p_value_holm` (always equal to raw, kept for schema compatibility), `reject_null`, `correlation_ci_overlap`, `correlation_effect_size_cv` |
| `comparison_report.json` | Aggregated delta metrics for the manuscript. | `overall_effect_size_change_mean`, `overall_ci_overlap_mean`, `overall_fpr_mean`, `variant_summary` (list of per‑variant aggregates) |
| `power_analysis.txt` | Plain‑text report of a priori power calculations (t‑test & Wilcoxon). | — (free‑form) |

## Schema Files (located in `contracts/`)

| Schema | Purpose |
|--------|---------|
| `dataset.schema.yaml` | Validates raw dataset description and checksum. |
| `baseline_metrics.schema.yaml` | Ensures baseline artefact completeness and numeric precision. |
| `cleaned_metrics.schema.yaml` | Validates each cleaning‑variant entry, including required metadata and optional effect‑size fields. |
| `bootstrap_metrics.schema.yaml` | Checks bootstrap CI fields and iteration count. |
| `null_fpr_metrics.schema.yaml` | Validates permutation‑based FPR artefact. |
| `sensitivity_metrics.schema.yaml` | Guarantees ANOVA result structure (size × missingness). |
| `hypothesis_test_results.schema.yaml` | Validates Wilcoxon test output and H2 correlation fields. |
| `comparison_report.schema.yaml` | Guarantees final aggregated report structure. |
| `delta_metrics.schema.yaml` | Provides a minimal schema for the delta fields used in SC‑001. |

All schemas follow JSON‑Schema Draft‑07 syntax, expressed in YAML for readability.

---

