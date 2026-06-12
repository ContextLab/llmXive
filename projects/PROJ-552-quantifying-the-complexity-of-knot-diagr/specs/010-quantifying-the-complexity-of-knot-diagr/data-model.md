# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, alternating classification, and hyperbolic volume.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| knot_id | string | Yes | Unique identifier from Knot Atlas (e.g., "8_19") | Format: "{crossing number}_{sequence number}" |
| crossing_number | integer | Yes | Minimum number of crossings in any diagram | Range: 1-13 |
| braid_index | integer | Yes | Minimum number of strands in any braid representation | Range: 1 ≤ braid_index ≤ crossing_number |
| hyperbolic_volume | float | Conditional | Volume of knot complement (hyperbolic knots only) | Must be > 0 for hyperbolic knots; null for torus/satellite |
| is_alternating | boolean | Conditional | Whether knot is alternating or non-alternating | May be null if classification ambiguous |
| dt_code | string | Optional | Dowker-Thistlethwaite code for diagram representation | May be null if representation unavailable |
| braid_word | string | Optional | Braid word representation | May be null if representation unavailable |
| data_quality_flags | array[string] | Yes | Flags for data quality issues | Values: "null_crossing", "null_braid", "null_volume", "format_invalid", "duplicate_id" |
| missing_invariant_flags | array[string] | Yes | Flags for uncomputable invariants | Values: "no_representation", "algorithm_not_implemented" |
| source_url | string | Yes | Source URL for data | Must be https://katlas.org |
| checksum | string | Yes | SHA-256 checksum of record | Format: 64-character hex string |
| timestamp | string | Yes | Data extraction timestamp | ISO 8601 format |

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Field | Type | Description |
|-------|------|-------------|
| dataset_id | string | Unique identifier for dataset version |
| total_records | integer | Total number of knots in dataset |
| hyperbolic_records | integer | Number of knots with volume > 0 |
| alternating_count | integer | Number of alternating knots |
| non_alternating_count | integer | Number of non-alternating knots |
| null_crossing_percentage | float | Percentage of records with null crossing number |
| null_braid_percentage | float | Percentage of records with null braid index |
| null_volume_percentage | float | Percentage of records with null hyperbolic volume |
| validation_status | string | Overall validation status | Values: "passed", "failed", "partial" |
| validation_notes | string | Notes on validation outcomes |
| created_at | string | Dataset creation timestamp | ISO 8601 format |
| checksum | string | SHA-256 checksum of dataset file | 64-character hex string |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| model_id | string | Unique identifier for model | Format: "{model_type}_{timestamp}" |
| model_type | string | Type of regression model | Values: "linear", "polynomial", "logarithmic" |
| predictors | array[string] | Predictor variables used | Values: "crossing_number", "braid_index" |
| coefficients | object | Model coefficients | Varies by model type |
| r_squared | float | Coefficient of determination | Range: 0-1 |
| aic | float | Akaike Information Criterion | Lower is better |
| bic | float | Bayesian Information Criterion | Lower is better |
| mae | float | Mean Absolute Error | Non-negative |
| vif_crossing | float | Variance Inflation Factor for crossing number | Expected to be high due to mathematical constraint |
| vif_braid | float | Variance Inflation Factor for braid index | Expected to be high due to mathematical constraint |
| residual_families | array[string] | Families with significant residual deviations | Values: "pretzel", "hyperbolic_non_alternating", etc. |
| dataset_checksum | string | Checksum of training dataset | Links to InvariantsDataset |
| created_at | string | Model creation timestamp | ISO 8601 format |

## Data Flow Diagram

```
Knot Atlas (https://katlas.org)
        ↓ [FR-001, FR-008: Download with retry]
raw/knot_atlas_export.csv [checksummed]
        ↓ [FR-002: Parse and clean]
processed/knots_cleaned.parquet [checksummed]
        ↓ [FR-012: Filter to hyperbolic]
processed/knots_hyperbolic.parquet [checksummed]
        ↓ [FR-004: Exploratory plots]
plots/crossing_vs_braid_*.png
        ↓ [FR-005: Regression models]
analysis/regression_models.parquet
        ↓ [FR-006: Statistical tests]
analysis/statistics_summary.parquet
        ↓ [FR-007: Reproducibility docs]
docs/reproducibility/*
```

## Validation Rules

1. **Crossing Number Range**: Must be integer in range [1, 13]
2. **Braid Index Constraint**: Must satisfy 1 ≤ braid_index ≤ crossing_number
3. **Hyperbolic Volume**: Must be > 0 for hyperbolic knots; null for torus/satellite
4. **No Duplicates**: knot_id must be unique within dataset
5. **Checksum Verification**: All data files must have valid SHA-256 checksums
6. **Flag Consistency**: data_quality_flags and missing_invariant_flags must be mutually exclusive categories (per FR-002 and FR-009 distinction)

## Tabulation vs Computation Boundary (SC-010, FR-003)

**Core invariants (crossing number, braid index) are TABULATED from Knot Atlas per SC-008 and FR-003, NOT computed.** Algorithm validation applies ONLY to Phase 2+ additional invariants (arc index, Seifert circle count, bridge number).

The `docs/reproducibility/algorithm_validation.md` document is reserved **exclusively** for Phase 2+ invariant computation validation. Phase 1 does not perform algorithm validation on core invariants because they are tabulated from Knot Atlas, not computed. This semantic boundary is enforced in the task definitions and validation workflow.

**Phase 1 Scope**: Core invariants validated via cross-reference consistency checks (Knot Atlas vs KnotInfo), not algorithm implementation validation.

**Phase 2+ Scope**: Additional invariants (arc index, Seifert circle count, bridge number) will be computed via implemented algorithms and documented in `algorithm_validation.md` per SC-010.