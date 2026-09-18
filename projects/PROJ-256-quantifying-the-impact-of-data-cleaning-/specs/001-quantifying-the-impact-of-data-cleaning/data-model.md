# Data Model: Quantifying the Impact of Data Cleaning

## Raw Data Layout
| Path | Description |
|------|-------------|
| `data/raw/<dataset_name>/` | Original files as downloaded from OpenML (CSV/ARFF). Each dataset has a `README.txt` containing the OpenML ID and a SHA‑2 family checksum. |
| `data/raw/<dataset_name>/checksum.sha256` | SHA‑256 hash of the raw file for data‑hygiene verification. |

## Processed Data Files
| File | JSON Schema | Content |
|------|--------------|---------|
| `data/processed/dataset_metadata.json` | `contracts/dataset.schema.yaml` | For each dataset: `name`, `outcome_column`, `outcome_type` (`binary`/`continuous`), `n_rows`, `missingness_proportion`. |
| `data/processed/baseline_metrics.json` | `contracts/baseline_metrics.schema.yaml` | Array of objects, one per dataset, containing raw test statistics (`p_value`, `ci_lower`, `ci_upper`, `effect_size`, `test_type`). |
| `data/processed/cleaned_metrics.json` | `contracts/cleaned_metrics.schema.yaml` | One entry per cleaning variant (`dataset`, `variant_id`, `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`, `ci_overlap`, `effect_size_change`, `p_value_delta`, `direction`, `assumptions_met`). |
| `data/processed/delta_metrics.json` | `contracts/delta_metrics.schema.yaml` | Subset of fields from `cleaned_metrics.json` that are “delta‑only”: `p_value_delta`, `direction`, `ci_overlap`, `effect_size_change`. |
| `data/processed/bootstrap_metrics.json` | `contracts/bootstrap_metrics.schema.yaml` | For each cleaned variant: bootstrap confidence intervals for `p_value`, `effect_size`, and derived `ci_overlap`. |
| `data/processed/sensitivity_metrics.json` | `contracts/sensitivity_metrics.schema.yaml` | Stratified results keyed by `size_bin` and `missingness_level`. |
| `data/processed/comparison_report.json` | `contracts/comparison_report.schema.yaml` | Aggregated delta metrics across all datasets and variants, ready for figure generation. |

## Schema Overview (see `contracts/` directory)
- **Dataset schema** validates presence of required metadata fields and correct data types.  
- **Baseline metrics schema** ensures each metric includes numeric fields with at least three decimal places.  
- **Cleaned metrics schema** extends baseline schema with cleaning‑metadata fields.  
- **Delta metrics schema** contains only the delta fields and enforces the `"increase"` / `"decrease"` enumeration for `direction`.  
- **Bootstrap schema** records the number of iterations used and the resulting percentile intervals.  
- **Sensitivity schema** captures bin identifiers and the count of datasets per bin.  
- **Comparison report schema** aggregates the delta fields and includes a top‑level `generated_at` timestamp.

All schemas are version‑controlled and referenced by the validation scripts in `tests/contract/`.

---
