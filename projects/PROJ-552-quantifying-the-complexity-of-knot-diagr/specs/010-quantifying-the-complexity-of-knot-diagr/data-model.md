# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This document defines the core data entities and their relationships for the knot complexity analysis pipeline. All data flows from Knot Atlas download through cleaning, analysis, and reproducibility documentation.

## Core Entities

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, alternating classification, and hyperbolic volume.

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| knot_id | string | Yes | Unique identifier for the knot (e.g., "10_123") | Knot Atlas |
| crossing_number | integer | Yes | Number of crossings in minimal diagram | Knot Atlas |
| braid_index | integer | Yes | Minimum number of strands in braid representation | Knot Atlas |
| hyperbolic_volume | float | Conditional | Hyperbolic volume (null for torus/satellite knots) | Knot Atlas |
| is_alternating | boolean | Conditional | Alternating vs. non-alternating classification | Knot Atlas |
| dt_code | string | Optional | Dowker-Thistlethwaite code representation | Knot Atlas |
| braid_word | string | Optional | Braid word representation | Knot Atlas |
| data_quality_flags | array | No | General data quality issues (null values, format failures, duplicates) | Computed |
| missing_invariant_flags | array | No | Invariants not computable from available diagram representations | Computed |
| validation_status | string | No | Status of validation against reference values | Computed |

**Field Constraints**:
- crossing_number > 0
- braid_index > 0
- braid_index ≤ crossing_number (mathematical constraint)
- hyperbolic_volume > 0 for hyperbolic knots; null or 0 for torus/satellite knots

**Flag Distinction** (per FR-002 and FR-009):
- data_quality_flags: Used for general data quality issues (null values, format failures, duplicates)
- missing_invariant_flags: Used specifically when invariants cannot be computed from available diagram representations
- Records may have both flag types if multiple conditions apply

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dataset_id | string | Yes | Unique identifier for dataset version |
| source | string | Yes | Data source (e.g., "Knot Atlas") |
| license | string | Yes | Dataset license/provenance (e.g., "CC-BY-4.0", "Unknown", or "Research-Use-Only") |
| download_timestamp | datetime | Yes | When data was downloaded |
| crossing_number_max | integer | Yes | Maximum crossing number in dataset (Phase 1: ≤13 available, ≤10 validated) |
| phase_1_scope_boundary | string | Yes | Scope annotation: "≤10 validated completeness, ≤13 data available" |
| total_records | integer | Yes | Total number of knot records |
| hyperbolic_records | integer | Yes | Number of hyperbolic knots (volume > 0) |
| null_percentage_crossing | float | Yes | Null percentage for crossing_number |
| null_percentage_braid | float | Yes | Null percentage for braid_index |
| null_percentage_volume | float | Yes | Null percentage for hyperbolic_volume |
| checksum_sha256 | string | Yes | SHA-256 checksum of dataset file |
| reproducibility_artifacts | array | Yes | List of documentation file paths |

**Data Quality Thresholds** (per FR-002):
- null_percentage < a minimal acceptable threshold for all required invariant fields
- Format validation pass rate is expected to meet a high reliability threshold.
- Zero duplicates in output dataset

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model_id | string | Yes | Unique identifier for model |
| model_type | string | Yes | Type (linear, polynomial, logarithmic) |
| predictor_variables | array | Yes | List of predictor variables used |
| coefficients | object | Yes | Model coefficients |
| r_squared | float | Yes | Coefficient of determination |
| aic | float | Yes | Akaike Information Criterion |
| bic | float | Yes | Bayesian Information Criterion |
| mae | float | Yes | Mean Absolute Error |
| vif_crossing | float | Yes | Variance Inflation Factor for crossing_number |
| vif_braid | float | Yes | Variance Inflation Factor for braid_index |
| residual_std | float | Yes | Standard deviation of residuals |
| outlier_families | array | No | Knot families with residuals ≥2 standard deviations |
| fitted_timestamp | datetime | Yes | When model was fitted |

**Model Selection Criteria** (per SC-002):
- Select model based on goodness-of-fit metrics (R², AIC/BIC, MAE), not on statistical power
- Descriptive interpretation for finite census dataset

## Relationships

```
InvariantsDataset
    ├── contains: KnotRecord (0..n)
    └── referenced_by: RegressionModel (1)

RegressionModel
    ├── uses: InvariantsDataset (1)
    └── analyzed_by: ResidualAnalysis (1)
```

## Data Flow

```
Knot Atlas Download
    ↓ (FR-001)
data/raw/knot_atlas_raw.json
    ↓ (FR-002)
data/processed/knots_cleaned.csv
    ↓ (FR-012)
data/processed/knots_hyperbolic.csv
    ↓ (FR-004, FR-005)
analysis/exploratory_plots/ + analysis/regression_models/
    ↓ (FR-007)
docs/reproducibility/
```

## Constraints

### Mathematical Constraints

1. **Braid Index Bound**: braid_index ≤ crossing_number (known mathematical constraint, not empirical finding)
2. **Hyperbolic Volume**: hyperbolic_volume > 0 for hyperbolic knots; null or 0 for torus/satellite knots
3. **Crossing Number**: crossing_number ≥ 1 for all prime knots

### Data Quality Constraints

1. **Null Percentage**: < 5% in required invariant fields (crossing_number, braid_index, hyperbolic_volume)
2. **Format Validation**: Valid DT code format, valid braid word format where present
3. **Duplicate Detection**: Zero duplicates in output dataset

### Validation Constraints

1. **Hyperbolic Volume Validation** (per FR-013): high match threshold with KnotInfo reference values where available
2. **Algorithm Validation** (per FR-003): a high match threshold for additional invariants (Phase 2+) where KnotInfo reference coverage is sufficient

## Versioning

All data files carry content hash in project state YAML. Derived data files include source file reference in metadata to maintain Constitution Principle IV (Single Source of Truth) traceability.