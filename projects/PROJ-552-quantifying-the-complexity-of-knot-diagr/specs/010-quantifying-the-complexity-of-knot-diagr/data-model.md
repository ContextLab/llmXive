# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knot_id | string | YES | Unique identifier for the knot (e.g., `KNOT_3_1`). |
| name | string | YES | Human‑readable name or Rolfsen notation. |
| crossing_number | integer | YES | Number of crossings in minimal diagram (≥ 3, ≤ 13). |
| braid_index | integer | YES | Minimum number of strands in a braid representation (≥ 2, ≤ crossing_number). |
| hyperbolic_volume | float (≥ 0) | YES | Hyperbolic volume of the knot complement (0 for torus/satellite knots). |
| alternating | boolean | YES | Whether the knot is alternating. |
| data_quality_flags | array of strings | NO | General data quality issues (null values, format failures, duplicates). |
| missing_invariant_flags | array of strings | NO | Invariants not computable from available diagram representations. |
| source | object | YES | Source metadata. |
| source_timestamp | string (ISO‑8601) | YES | Timestamp of the source record. |
| checksum_sha256 | string | YES | SHA‑256 checksum of the raw source record. |
| source.database | string | YES | Database name (e.g., `"KnotAtlas"`). |
| source.version | string | YES | Database version or access date. |
| source.url | string | YES | Canonical URL for the record. |
| source.accessed_at | string (ISO‑8601) | YES | Timestamp when data was accessed. |
| source.source_timestamp | string (ISO‑8601) | YES | Timestamp of the source record (duplicate of `source_timestamp` for compatibility). |
| source.checksum_sha256 | string | YES | SHA‑256 of the raw source record. |

### InvariantsDataset

Aggregated collection of KnotRecord entities:

| Field | Type | Description |
|-------|------|-------------|
| records | array of KnotRecord | All knot records |
| metadata | object | Dataset metadata |
| metadata.source | string | Data source |
| metadata.version | string | Dataset version |
| metadata.created_at | string (ISO‑8601) | Creation timestamp |
| metadata.crossing_number_range | object | Min/max crossing numbers |
| metadata.total_records | integer | Total number of records |
| metadata.hyperbolic_count | integer | Count of knots with volume > 0 |
| metadata.null_percentages | object | Null percentage per required field |

## Derived Fields

### data_quality_flags

Values:  
- `null_crossing_number`  
- `null_braid_index`  
- `null_hyperbolic_volume`  
- `null_alternating`  
- `format_failure`  
- `duplicate_knot_id`

### missing_invariant_flags

Values:  
- `no_representation_available` – Invariant cannot be computed from available diagram data (e.g., additional invariants in Phase 2+).  
- `algorithm_not_implemented` – Placeholder for future algorithmic support.

**Flag Distinction**: `data_quality_flags` handle generic quality issues; `missing_invariant_flags` flag invariants that are intrinsically unavailable.

## Data Transformations

### Raw → Cleaned

1. Parse Knot Atlas JSON/CSV to extract knot records.  
2. Apply tie‑breaking rules for multiple diagram representations (FR‑011).  
3. Validate format against `knot_record.schema.yaml`.  
4. Flag records with null values, format failures, duplicates.  
5. Output: `data/processed/knots_cleaned.csv`.

### Cleaned → Validated

1. Compute null percentages per required field.  
2. Verify null percentage ≤ 5 % per field (FR‑002, SC‑001).  
3. Verify format validation pass rate ≥ 99 % (FR‑002).  
4. Verify duplicate count = 0 (FR‑002).  
5. Flag records failing conditions.  
6. Output: `data/processed/knots_validated.csv`.

### Validated → Hyperbolic

1. Filter to knots with `hyperbolic_volume` > 0 (FR‑012).  
2. Document excluded knots in `docs/reproducibility/excluded_knots.md`.  
3. Output: `data/processed/knots_hyperbolic.csv`.

## Schema Validation

All records MUST validate against `knot_record.schema.yaml` (see contracts/). Format validation pass rate ≥ 99 % required (FR‑002).

## Handling of Missing Invariants

Records flagged with `missing_invariant_flags` are **excluded** from any quantitative modelling (regression, correlation, group comparison). They remain in the cleaned dataset for completeness reporting but are omitted from statistical computations. Documentation of excluded records is provided in `missing_invariants.md`.

## Completeness Verification (SC‑001)

The validator (`code/data/validator.py`) computes null percentages, format‑pass rate, and duplicate count. These metrics are recorded in `data_quality_report.md`. The pipeline aborts if any required field exceeds a 5 % null threshold, if format‑pass rate falls below [deferred], or if any duplicates are detected, thereby enforcing SC‑001.
