# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This document defines the data models for the knot complexity analysis pipeline. All data flows through these models with strict type checking validated against YAML schemas in `contracts/`.

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, alternating classification, and hyperbolic volume.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knot_id | string | Yes | Unique identifier (e.g., "8_19", "10_124") |
| crossing_number | integer | Yes | Minimum number of crossings in any diagram representation |
| braid_index | integer | Yes | Minimum number of strands in any braid representation |
| hyperbolic_volume | float | Yes | Hyperbolic volume (0 for torus/satellite knots, > 0 for hyperbolic knots) |
| is_alternating | boolean | Yes | True if alternating knot; False if non-alternating |
| dt_code | string | No | Dowker-Thistlethwaite code (may be null) |
| braid_word | string | No | Braid word representation (may be null) |
| data_quality_flags | array<string> | Yes | Data quality issues (null values, format failures, duplicates) |
| missing_invariant_flags | array<string> | Yes | Invariants not computable from available diagram representations |
| is_hyperbolic | boolean | Yes | True if hyperbolic_volume > 0 (used for filtering per FR-012) |

### InvariantsDataset

Aggregated collection of knot records with metadata and summary statistics.

| Field | Type | Description |
|-------|------|-------------|
| dataset_id | string | Unique dataset identifier |
| data_source | string | Source database (e.g., Knot Atlas, KnotInfo, Hoste-Thistlethwaite-Weeks) |
| created_at | string | Dataset creation timestamp (ISO 8601) |
| checksum | string | SHA-256 checksum of dataset file |
| crossing_number_range | string | Range of crossing numbers included (e.g., "1-13") |
| validated_range | string | Range with validated completeness (e.g., "1-10") |
| total_records | integer | Total number of knot records |
| hyperbolic_records | integer | Number of hyperbolic knots (volume > 0) |
| null_percentage_crossing | number | Null percentage in crossing number field (0-100) |
| null_percentage_braid | number | Null percentage in braid index field (0-100) |
| null_percentage_volume | number | Null percentage in hyperbolic volume field (0-100) |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics.

| Field | Type | Description |
|-------|------|-------------|
| model_id | string | Unique identifier |
| model_type | string | "linear", "polynomial", or "logarithmic" |
| predictors | array<string> | Predictor variables (e.g., ["crossing_number", "braid_index"]) |
| target | string | Target variable (e.g., "hyperbolic_volume") |
| coefficients | object | Model coefficients |
| r_squared | float | R² goodness-of-fit metric |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| vif_scores | object | Variance Inflation Factor for each predictor |
| residual_outliers | array<string> | Knot IDs with residuals ≥ 2 standard deviations |

## Data Flow

```
Knot Atlas Download
    ↓
Raw JSON/CSV (data/raw/knot_atlas_raw.json)
    ↓
Parser (code/download/knot_atlas_downloader.py)
    ↓
Validated Records (data/processed/knots_validated.parquet)
    ↓
Hyperbolic Filter (code/data/filter_hyperbolic.py)
    ↓
Hyperbolic Dataset (data/processed/knots_hyperbolic.parquet)
    ↓
Exploratory Analysis (code/analysis/exploratory.py)
    ↓
Regression Models (code/analysis/regression.py)
    ↓
Residual Analysis (code/analysis/residual_analysis.py)
    ↓
Final Reports (docs/)
```

## Validation Rules

### Crossing Number Range

- **Valid Range**: 1 to 13 (per FR-001)
- **Phase 1 Validation**: ≤ 10 crossings validated; 11-13 crossings exploratory only
- **Validation**: Must match OEIS A002863 counts per crossing number for validated subset

### Hyperbolic Volume

- **Valid Values**: > 0 for hyperbolic knots, = 0 for torus/satellite knots
- **Filtering**: Volume > 0 required for volume prediction analysis (FR-012)
- **Validation**: ≥ 90% match against KnotInfo reference values where available (FR-013)

### Data Quality Flags

| Flag | Trigger Condition |
|------|-------------------|
| "null_crossing_number" | crossing_number is null |
| "null_braid_index" | braid_index is null |
| "null_hyperbolic_volume" | hyperbolic_volume is null |
| "invalid_dt_code" | dt_code format validation failed |
| "invalid_braid_word" | braid_word format validation failed |
| "duplicate_knot_id" | Duplicate knot_id detected |
| "no_representation" | No diagram representation available for invariant computation |
| "algorithm_not_implemented" | Invariant computation algorithm not implemented (Phase 2+) |

## Derived Fields

### is_hyperbolic

Computed from hyperbolic_volume:
```python
is_hyperbolic = hyperbolic_volume > 0
```

### data_quality_score

Computed from data_quality_flags:
```python
data_quality_score = 1.0 - (len(data_quality_flags) / total_possible_flags)
```

## Schema Validation

All data must pass validation against YAML schemas in `contracts/`:
- `contracts/knot_record.schema.yaml`: Validates individual KnotRecord entities
- `contracts/regression_model.schema.yaml`: Validates RegressionModel entities
- `contracts/dataset.schema.yaml`: Validates InvariantsDataset aggregation metadata

Validation performed by pytest contract tests in `tests/contract/`.