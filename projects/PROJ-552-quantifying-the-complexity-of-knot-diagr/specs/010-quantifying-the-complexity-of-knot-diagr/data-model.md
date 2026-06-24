# Data Model: Knot Complexity Analysis

## Core Entity: KnotRecord
| Field | Type | Description |
|-------|------|-------------|
| `knot_id` | string | Unique identifier (e.g., `"3_1"` for the trefoil). |
| `crossing_number` | integer | Minimum crossing number (c). |
| `braid_index` | integer | Minimal braid index (b). |
| `hyperbolic_volume` | float | Hyperbolic volume (V); not applicable for non‑hyperbolic knots. |
| `alternating` | boolean | `true` if the knot is alternating, `false` otherwise. |
| `data_quality_flags` | list[string] | Flags from FR‑002 (e.g., `"null_crossing_number"`). |
| `missing_invariant_flags` | list[string] | Flags from FR‑009 (e.g., `"missing_braid_index"`). |
| `source_timestamp` | string (ISO‑8601) | Time of download from Knot Atlas. |
| `checksum_sha256` | string | SHA‑256 of the raw JSON entry for this knot. |

## Derived Datasets
1. **knots_cleaned.csv** – Contains all `KnotRecord` fields after parsing and tie‑breaking; no flags applied.
2. **knots_validated.csv** – Same schema plus `data_quality_flags` and `missing_invariant_flags`; filtered to `hyperbolic_volume > 0` for modeling.
3. **regression_summary.csv** – One row per fitted model type with columns: `model_type`, `R2`, `AIC`, `BIC`, `MAE`, `VIF_crossing`, `VIF_braid`.

All datasets are stored under `data/processed/` and accompanied by a checksum manifest `data/checksums.sha256`.
