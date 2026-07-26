# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes derived from KnotInfo.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `knot_id` | string | Unique identifier (e.g., "10_123") | Unique, non-null |
| `crossing_number` | integer | Number of crossings in minimal diagram | ≥ 1, ≤ 13 |
| `braid_index` | integer | Minimal braid index | ≥ 2, ≤ crossing_number |
| `hyperbolic_volume` | float | Hyperbolic volume (0 if not hyperbolic) | ≥ 0 |
| `alternating` | boolean | Is the knot alternating? | True/False/None |
| `source` | object | Metadata about the data source | Non-null |
| `source.database` | string | Name of source database | "KnotInfo" |
| `source.version` | string | Version of the database | Non-null |
| `source.url` | string | Canonical URL for the record | Valid URL |
| `source.accessed_at` | string | ISO-8601 timestamp of access | Non-null |
| `source.source_timestamp` | string | ISO-8601 timestamp of source record | Non-null |
| `source.checksum_sha256` | string | SHA-256 of raw source record | Non-null |
| `data_quality_flags` | array | General data quality issues (null, format, duplicate) | Optional |
| `missing_invariant_flags` | array | Specific invariant computation failures | Optional |

### InvariantsDataset

Aggregated collection of `KnotRecord` entities with derived fields and metadata.

| Field | Type | Description |
| :--- | :--- | :--- |
| `records` | array[KnotRecord] | List of all knot records |
| `metadata` | object | Dataset-level metadata |
| `metadata.source` | string | Data source name |
| `metadata.created_at` | string | ISO-8601 timestamp |
| `metadata.record_count` | integer | Total number of records |
| `metadata.hyperbolic_count` | integer | Count of hyperbolic knots (volume > 0) |
| `metadata.alternating_count` | integer | Count of alternating knots |

### RegressionModel

Represents a fitted regression model.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "linear", "polynomial", "logarithmic" |
| `coefficients` | object | Model coefficients |
| `r_squared` | float | R² goodness-of-fit |
| `aic` | float | Akaike Information Criterion |
| `bic` | float | Bayesian Information Criterion |
| `mae` | float | Mean Absolute Error |
| `vif_crossing` | float | VIF for crossing number predictor |
| `vif_braid` | float | VIF for braid index predictor |

## Data Flow

1.  **Raw Data**: `data/raw/knot_atlas_raw.json` (from `database-knotinfo`).
2.  **Parsed Data**: `data/processed/knots_cleaned.csv` (validated `KnotRecord` objects).
3.  **Filtered Data**: `data/processed/knots_hyperbolic.csv` (volume > 0).
4.  **Analysis Output**: `data/analysis/regression_results.json`, `data/analysis/residuals.csv`.
5.  **Reproducibility Artifacts**: `docs/reproducibility/` (checksums, logs, reports).

## Data Quality Rules

- **Null Percentage**: ≤ 5% for required fields (crossing number, braid index, hyperbolic volume) in validated subset.
- **Format Validation**: ≥ 99% pass rate for all records against `knot_record.schema.yaml`.
- **Duplicates**: 0 duplicate `knot_id`s allowed.
- **Flagging**: Records failing validation are flagged, not excluded (unless critical).

## File Paths

- `data/raw/knot_atlas_raw.json`
- `data/processed/knots_cleaned.csv`
- `data/processed/knots_hyperbolic.csv`
- `data/analysis/regression_results.json`
- `data/analysis/residuals.csv`
- `docs/reproducibility/data_quality_report.md`
- `docs/reproducibility/excluded_knots.md`
- `docs/reproducibility/random_seeds.md`
