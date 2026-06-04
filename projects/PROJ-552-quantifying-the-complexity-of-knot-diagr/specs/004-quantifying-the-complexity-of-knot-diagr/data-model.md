# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Overview

This document defines the data entities used throughout the knot complexity analysis pipeline. All entities are designed to support reproducibility per Constitution Principle III (Data Hygiene) and single source of truth per Constitution Principle IV.

## Key Entities

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, arc index, Seifert circle count, bridge number, alternating classification, and hyperbolic volume.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| knot_id | string | Yes | Unique identifier (e.g., "3_1", "4_1") |
| crossing_number | integer | Yes | Minimum number of crossings in any diagram |
| braid_index | integer | No | Minimum number of strands in braid representation |
| arc_index | integer | No | Computed via Birman-Menasco algorithm |
| seifert_circle_count | integer | No | Computed via Seifert's algorithm |
| bridge_number | integer | No | Computed via Schubert's bridge decomposition |
| alternating_classification | string | Yes | One of: "alternating", "non-alternating", "unclassifiable" |
| hyperbolic_volume | float | No | Geometric volume (zero/undefined for torus/satellite) |
| diagram_representation | string | No | DT code or braid word representation |
| missing_invariant_flags | array[string] | No | List of invariants that could not be computed |
| data_source | string | Yes | Source of data (e.g., "knot_atlas") |
| checksum | string | Yes | SHA-256 checksum of raw record |
| created_at | timestamp | Yes | Record creation timestamp |

**Invariant Dependency Note**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies must be acknowledged in all analysis and reporting.

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| dataset_id | string | Yes | Unique identifier for dataset version |
| knot_records | array[KnotRecord] | Yes | Collection of knot records (field name aligned with contracts/invariants_dataset.schema.yaml) |
| total_count | integer | Yes | Total number of records |
| crossing_number_range | object | Yes | Min and max crossing numbers in dataset |
| alternating_count | integer | Yes | Count of alternating knots |
| non_alternating_count | integer | Yes | Count of non-alternating knots |
| volume_valid_count | integer | Yes | Count with valid hyperbolic volume |
| computation_timestamp | timestamp | Yes | When invariants were computed |
| algorithm_versions | object | Yes | Version info for each algorithm used |
| validation_status | object | Yes | Pass/fail status per invariant per algorithm |
| checksum | string | Yes | SHA-256 checksum of entire dataset |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Unique identifier for model instance |
| model_type | string | Yes | One of: linear, polynomial, logarithmic |
| predictors | array[string] | Yes | List of predictor variables used |
| coefficients | object | Yes | Model coefficients with names |
| intercept | float | Yes | Model intercept |
| r_squared | float | Yes | Coefficient of determination |
| adjusted_r_squared | float | Yes | Adjusted R-squared |
| aic | float | Yes | Akaike Information Criterion |
| bic | float | Yes | Bayesian Information Criterion |
| mae | float | Yes | Mean Absolute Error |
| vif_values | object | Yes | Variance Inflation Factors per predictor |
| training_sample_size | integer | Yes | Number of records in training sample |
| validation_sample_size | integer | Yes | Number of records in validation sample |
| random_seed | integer | Yes | Seed used for sample split |
| fitted_at | timestamp | Yes | When model was fitted |

### CompositeComplexityScore

Represents the weighted complexity measure with attributes including weight parameters, per-knot scores, and validation correlation metrics.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| score_id | string | Yes | Unique identifier for score configuration |
| crossing_weight | float | Yes | Weight for crossing number |
| braid_weight | float | Yes | Weight for braid index |
| per_knot_scores | object | Yes | Map of knot_id to complexity score |
| correlation_pearson | float | Yes | Pearson correlation with hyperbolic volume |
| correlation_spearman | float | Yes | Spearman correlation with hyperbolic volume |
| effect_size_r | float | Yes | Effect size for correlation |
| validation_sample_size | integer | Yes | Number of records in validation sample |
| random_seed | integer | Yes | Seed used for sample split |
| created_at | timestamp | Yes | When score was computed |

## Data Flow Diagram

```
┌─────────────────────┐
│ Knot Atlas API │
│ (katlas.org) │
└──────────┬──────────┘
 │
 ▼
┌─────────────────────┐
│ raw_download.parquet│
│ (FR-001 download) │
└──────────┬──────────┘
 │
 ▼
┌─────────────────────┐
│ parsed_knots.parquet│
│ (FR-002 parse/clean)│
└──────────┬──────────┘
 │
 ▼
┌─────────────────────┐
│ knots_with_invariants│
│.parquet │
│ (FR-003 compute) │
└──────────┬──────────┘
 │
 ┌─────┴─────┐
 │ │
 ▼ ▼
┌──────────┐ ┌──────────┐
│ Exploratory│ │ Regression│
│ Analysis │ │ Models │
│ (FR-004) │ │ (FR-005) │
└──────────┘ └──────────┘
 │ │
 └─────┬─────┘
 ▼
┌─────────────────────┐
│ Composite Score │
│ Validation │
│ (FR-006, FR-007) │
└─────────────────────┘
```

## Data Transformations

### Raw to Parsed (FR-002)

| Transformation | Input Field | Output Field | Logic |
|----------------|-------------|--------------|-------|
| Extract crossing number | crossing_number | crossing_number | Integer conversion, validate ≥3 |
| Extract braid index | braid_index | braid_index | Integer conversion, validate ≥1 |
| Extract hyperbolic volume | hyperbolic_volume | hyperbolic_volume | Float conversion, flag zero/undefined |
| Extract alternating classification | is_alternating | alternating_classification | Convert boolean to enum string |
| Standardize knot_id | name | knot_id | Format: "c_n" (e.g., "3_1") |

### Parsed to Invariants (FR-003)

| Transformation | Input | Output | Algorithm |
|----------------|-------|--------|-----------|
| Compute arc index | diagram_representation | arc_index | Birman-Menasco |
| Compute Seifert circles | diagram_representation | seifert_circle_count | Seifert's algorithm |
| Compute bridge number | diagram_representation | bridge_number | Schubert's decomposition |
| Flag missing invariants | null values | missing_invariant_flags | Set of uncomputable invariant names |

### Validation Sample Split (FR-007)

| Transformation | Input | Output | Logic |
|----------------|-------|--------|-------|
| Stratified split | knots_with_invariants | exploratory_validation_sample | 20% random stratified by crossing number |
| Seed pinning | random_state | random_seed | Documented in docs/reproducibility/ |

## File Storage Convention

| Directory | Purpose | Checksum Location | Contract Schema |
|-----------|---------|-------------------|-----------------|
| data/raw/ | Unmodified downloads | data/raw/.checksums | N/A |
| data/processed/ | Derived datasets | data/processed/.checksums | contracts/invariants_dataset.schema.yaml |
| data/plots/ | Generated visualizations | data/plots/.checksums | N/A |
| code/models/ | Regression model outputs | code/models/.checksums | contracts/regression_output.schema.yaml |
| docs/reproducibility/ | Derivation notes, logs | N/A (documentation only) | N/A |
| config/ | Configuration files | config/.checksums | N/A |

**Contract-to-File Mapping**:
- `data/processed/knots_with_invariants.parquet` → validated against `contracts/invariants_dataset.schema.yaml`
- `code/models/*.json` → validated against `contracts/regression_output.schema.yaml`

## Schema Validation

All data files MUST conform to schema definitions in contracts/ directory. Contract validation runs automatically as part of the data pipeline (see contracts/knot_record.schema.yaml and contracts/regression_output.schema.yaml).

**Unified Field Naming**: All contracts use `alternating_classification` (string enum) consistently. The previous `is_alternating` (boolean) field has been deprecated to ensure schema consistency across the codebase.