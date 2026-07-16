# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity-Relationship Overview

The data model is designed to support a linear data pipeline: Raw Download -> Cleaned -> Validated -> Analyzed.

### Core Entities

1.  **KnotRecord**
    - Represents a single prime knot.
    - Contains raw and processed invariant values.
    - Includes metadata for reproducibility (source, checksum, flags).
    - **SSoT**: Defined by `contracts/knot_record.schema.yaml`.

2.  **InvariantsDataset**
    - Aggregation of `KnotRecord` entities.
    - Derived fields: `is_hyperbolic`, `invariant_completeness_score`.

3.  **RegressionModel**
    - Represents a fitted statistical model.
    - Stores coefficients, metrics, and residual analysis results.

## Attribute Definitions

### KnotRecord

| Attribute | Type | Description | Source | Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `knot_id` | string | Unique identifier (e.g., "8_18") | Knot Atlas | Primary Key, Unique, Pattern: `^[0-9]+_[0-9]+$` (SSoT) |
| `crossing_number` | integer | Number of crossings in minimal diagram | Knot Atlas | ≥ 1 |
| `braid_index` | integer | Minimum number of strands in braid representation | Knot Atlas | ≥ 1, ≤ `crossing_number` |
| `hyperbolic_volume` | float | Volume of hyperbolic complement | Knot Atlas | ≥ 0 (0 for non-hyperbolic) |
| `alternating` | boolean | Is the knot alternating? | Knot Atlas | True/False/Null (if ambiguous) |
| `source` | object | Metadata about the source record | Knot Atlas | See schema |
| `data_quality_flags` | list | General data quality issues | Derived | e.g., "duplicate_id", "format_error" |
| `missing_invariant_flags` | list | Specific missing invariants (Phase 2+) | Derived | e.g., "no_braid_word" |
| `checksum_sha256` | string | SHA-256 of raw source record | Derived | 64-char hex string |

### Source Object (Nested in KnotRecord)

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `database` | string | "Knot Atlas" |
| `version` | string | Version of the database accessed |
| `url` | string | Canonical URL for the record |
| `accessed_at` | string | ISO-8601 timestamp of download |
| `source_timestamp` | string | ISO-8601 timestamp of source record |
| `checksum_sha256` | string | SHA-256 of raw source record |

### RegressionModel

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `model_id` | string | Unique identifier for the model run |
| `model_type` | string | "linear", "polynomial", "logarithmic", "ridge" |
| `coefficients` | dict | Map of feature name to coefficient value |
| `metrics` | dict | R², AIC, BIC, MAE |
| `vif_scores` | dict | Variance Inflation Factor for each predictor |
| `residual_outliers` | list | List of `knot_id`s with residuals ≥ 2 SD |

## Data Flow

1.  **Raw**: `data/raw/knot_atlas_raw.json` (Immutable, checksummed).
2.  **Cleaned**: `data/processed/knots_cleaned.csv` (Parsed, deduplicated, basic cleaning).
    - *Normalization*: `knot_id` is normalized to the SSoT format `^[0-9]+_[0-9]+$` (e.g., "8_18") during this step.
3.  **Validated**: `data/processed/knots_validated.csv` (Filtered for hyperbolic, flags applied, validated against KnotInfo).
4.  **Analysis**: `docs/reproducibility/` (Reports, plots, model outputs).

## Data Quality Rules

- **Uniqueness**: `knot_id` must be unique.
- **Completeness**: Required fields (`crossing_number`, `braid_index`, `hyperbolic_volume`) must have null percentage ≤ 5% in the validated subset.
- **Consistency**: `braid_index` ≤ `crossing_number` must hold for all records.
- **Validation**: Hyperbolic volume must match KnotInfo within 1e-6 tolerance where reference exists.
- **SSoT**: `contracts/knot_record.schema.yaml` is the Single Source of Truth. Deprecated files (`knot-record.schema.yaml`, `knot_dataset.schema.yaml`) are not used.