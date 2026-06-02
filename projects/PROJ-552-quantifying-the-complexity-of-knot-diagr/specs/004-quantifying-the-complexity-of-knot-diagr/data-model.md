# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This document defines the data entities and relationships for the knot complexity analysis project. All data transformations must produce new files with documented derivation per Constitution Principle III.

## Key Entities

### KnotRecord

Represents a single prime knot with attributes including computed and tabulated invariants.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `knot_id` | string | Yes | Unique identifier (e.g., "3_1", "8_19") |
| `crossing_number` | integer | Yes | Tabulated crossing number (minimal) |
| `braid_index` | integer | Yes | Computed braid index |
| `hyperbolic_volume` | float | Conditional | Hyperbolic volume (required for volume prediction analysis; null for torus/satellite) |
| `alternating_classification` | string | Yes | "alternating", "non-alternating", or "unclassifiable" |
| `arc_index` | integer | Conditional | Computed via Birman-Menasco method |
| `seifert_circle_count` | integer | Conditional | Computed via Seifert's algorithm |
| `bridge_number` | integer | Conditional | Computed via Schubert's decomposition |
| `missing_invariant_flags` | array[string] | No | Flags for missing computable invariants |
| `diagram_representation_type` | string | No | "braid_word", "dt_code", or "both" |
| `source_checksum` | string | Yes | SHA-256 of source data file |
| `computation_timestamp` | string | Yes | ISO 8601 timestamp of invariant computation |

**Invariant Dependency Note**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots [UNRESOLVED-CLAIM: c_b320c94e — status=not_enough_info]). These dependencies must be acknowledged in all analysis and reporting.

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata about data source and computation timestamps.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | Unique identifier for this dataset version |
| `knot_records` | array[KnotRecord] | Collection of individual knot records |
| `data_source` | string | "knot_atlas" or other source |
| `download_timestamp` | string | ISO 8601 timestamp of data download |
| `crossing_number_range` | object | {`min`: integer, `max`: integer} |
| `total_knots` | integer | Count of all records |
| `alternating_count` | integer | Count of alternating knots |
| `non_alternating_count` | integer | Count of non-alternating knots |
| `volume_available_count` | integer | Count with valid hyperbolic volume |
| `schema_version` | string | Data model schema version |
| `validation_scope` | string | Scope of validation for Phase 1 (crossing number ≤10 validated, ≤13 collected) |
| `prime_knot_counts` | object | Prime knot counts per crossing number from OEIS A002863 |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, and goodness-of-fit metrics.

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string | Unique identifier for this model |
| `model_type` | string | "linear", "polynomial", or "logarithmic" |
| `predictors` | array[string] | List of predictor variables used |
| `target` | string | Target variable (e.g., "hyperbolic_volume") |
| `coefficients` | object | Model coefficients with names as keys |
| `r_squared` | float | Coefficient of determination |
| `adjusted_r_squared` | float | Adjusted R² |
| `aic` | float | Akaike Information Criterion |
| `bic` | float | Bayesian Information Criterion |
| `mae` | float | Mean Absolute Error |
| `vif_scores` | object | Variance Inflation Factors per predictor |
| `training_sample_size` | integer | Number of records used for fitting |
| `validation_sample_size` | integer | Number of records in exploratory validation sample |
| `random_seed` | integer | Seed used for validation sample split |
| `multicollinearity_flag` | boolean | True if any VIF > 5 |

### CompositeComplexityScore

Represents the weighted complexity measure with attributes including weight parameters and validation metrics.

| Field | Type | Description |
|-------|------|-------------|
| `score_id` | string | Unique identifier for this score configuration |
| `crossing_number_weight` | float | Weight for crossing number (default 0.5) |
| `braid_index_weight` | float | Weight for braid index (default 0.5) |
| `knot_scores` | array[object] | Per-knot scores with `knot_id` and `score` value |
| `pearson_correlation` | float | Pearson correlation with hyperbolic volume |
| `spearman_correlation` | float | Spearman correlation with hyperbolic volume |
| `effect_size_r` | float | Effect size for correlation |
| `p_value` | float | Statistical significance of correlation |
| `validation_sample_size` | integer | Size of exploratory correlation subset |
| `random_seed` | integer | Seed used for correlation subset split |

**Theoretical Limitation Acknowledgment**: No established mathematical basis exists in knot theory literature for a linear combination of crossing number and braid index. The equal-weight default is exploratory and configurable.

## Data Flow

```
┌─────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Knot Atlas │────▶│ Raw Data │────▶│ Processed Data │
│ (Download) │ │ (checksummed) │ │ (computed invariants)
└─────────────────┘ └──────────────────┘ └──────────────────┘
 │
 ▼
 ┌──────────────────┐
 │ Analysis Outputs│
 │ (plots, models) │
 └──────────────────┘
```

## Data Hygiene Requirements

1. **Checksums**: All files under `data/` must have SHA-256 checksums recorded in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` `artifact_hashes` map.
2. **No In-Place Modification**: Every transformation produces a new file with documented derivation.
3. **PII Scan**: No commits are accepted that fail the Repository-Hygiene Agent's PII scan (Constitution Principle III).
4. **Single Source of Truth**: All figures/statistics trace to exactly one row in `data/` and one code block (Constitution Principle IV).

## Validation Rules

| Rule | Description |
|------|-------------|
| `crossing_number >= 1` | Crossing number must be positive integer |
| `braid_index <= crossing_number` | Braid index typically ≤ crossing number (known inequality) |
| `hyperbolic_volume >= 0` OR `hyperbolic_volume` is null | Volume cannot be negative; null for torus/satellite |
| `alternating_classification IN ["alternating", "non-alternating", "unclassifiable"]` | Classification mustbe one of three values |
| `arc_index >= 3` | Arc index has lower bound for non-trivial knots |
| `seifert_circle_count >= 1` | At least one Seifert circle for any knot diagram |
| `bridge_number >= 2 (Theorem DB: 0909.1162, https://arxiv.org/abs/0909.1162)` | Bridge number has lower bound for non-trivial knots |