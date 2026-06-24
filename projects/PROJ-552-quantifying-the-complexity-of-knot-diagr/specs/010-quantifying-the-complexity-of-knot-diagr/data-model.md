# Data Model: Quantifying the Complexity of Knot Diagrams

## Core Entities

### KnotRecord
| Field | Type | Description |
|-------|------|-------------|
| `knot_id` | string | Unique identifier (e.g., “4_1”). |
| `name` | string | Common name or Rolfsen notation. |
| `crossing_number` | integer | Minimal crossing number (c). |
| `braid_index` | integer | Braid index (b). Must satisfy **b ≤ c** (Mathematical Invariant Consistency, Principle VI). |
| `hyperbolic_volume` | float | Hyperbolic volume (V); `0.0` for non‑hyperbolic knots (source: https://en.wikipedia.org/wiki/Hyperbolic_volume). |
| `alternating` | boolean | `true` if alternating, `false` if non‑alternating, `null` if ambiguous. |
| `arc_index` | integer | Optional; computed in Phase 9 (FR‑003). |
| `seifert_circle_count` | integer | Optional; computed in Phase 9 (FR‑003). |
| `bridge_number` | integer | Optional; computed in Phase 9 (FR‑003). |
| `source` | object | Metadata about the provenance (see below). |
| `source_timestamp` | string (ISO‑8601) | Timestamp when the source record was fetched. |
| `checksum_sha256` | string | SHA‑256 checksum of the raw source record. |
| `data_quality_flags` | list[string] | Flags from FR‑002 (e.g., `null_crossing_number`). |
| `missing_invariant_flags` | list[string] | Flags from FR‑009 (e.g., `missing_braid_index`). |
| `classification_flag` | string | `"unclassifiable"` when alternating status is ambiguous (FR‑010). |

#### `source` object
| Sub‑field | Type | Description |
|-----------|------|-------------|
| `database` | string | Name of the source database (e.g., `"KnotAtlas"`). |
| `version` | string | Version string or commit hash of the source dump. |
| `url` | string | Canonical URL of the source (e.g., `https://katlas.org`). |
| `accessed_at` | string (ISO‑8601) | When the download occurred. |

### InvariantsDataset
A collection of `KnotRecord`s together with derived metadata:
- `record_count`: total number of records.  
- `hyperbolic_count`: number of records with `hyperbolic_volume > 0`.  
- `validated_crossing_number_coverage`: % of records where crossing number matches a reference (KnotInfo).  
- `validated_braid_index_coverage`: % of records where braid index matches a reference **or satisfies the inequality b ≤ c**.  
- `data_quality_summary`: includes null % ≤ 5, format pass ≥ 99, duplicate = 0 (SC‑013).  

### RegressionModel
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"linear"`, `"polynomial"` or `"logarithmic"`. |
| `coefficients` | object | Mapping from predictor name to numeric coefficient. |
| `intercept` | float | Intercept term. |
| `r_squared` | float | Coefficient of determination (R²). |
| `aic` | float | Akaike Information Criterion. |
| `bic` | float | Bayesian Information Criterion. |
| `mae` | float | Mean Absolute Error. |
| `vif` | object | VIF values for each predictor. |
| `fit_timestamp` | string (ISO‑8601) | When the model was trained. |
| `alternating_control` | boolean | Whether alternating classification was used as a covariate. |
| `braid_index_uncertainty` | boolean | Whether braid index uncertainty is propagated (Phase 0/1 exploratory). |

## Relationships
- Each `RegressionModel` references a single `InvariantsDataset` (the hyperbolic subset).  
- `KnotRecord` objects are stored in CSV files; the schema is enforced by `contracts/knot_record.schema.yaml`.  


