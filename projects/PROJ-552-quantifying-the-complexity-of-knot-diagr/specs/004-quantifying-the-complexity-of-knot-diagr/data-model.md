# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, arc index, Seifert circle count, bridge number, alternating classification, and hyperbolic volume.

**Attributes**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knot_id | string | ✅ Yes | Unique identifier (e.g., "10_123", "13_4567") |
| crossing_number | integer | ✅ Yes | Minimal crossing count |
| braid_index | integer | ✅ Yes | Minimal braid representation index |
| hyperbolic_volume | float | ⚠️ Conditional | Geometric volume (null for torus/satellite knots) |
| is_alternating | boolean | ⚠️ Conditional | Alternating classification (null if ambiguous) |
| arc_index | integer | ❌ No | Computed arc index (null if not computable) |
| seifert_circle_count | integer | ❌ No | Computed Seifert circle count (null if not computable) |
| bridge_number | integer | ❌ No | Computed bridge number (null if not computable) |
| dt_code | string | ❌ No | Dowker-Thistlethwaite code |
| braid_word | string | ❌ No | Braid word representation |
| missing_invariant_flags | array[string] | ❌ No | Flags for missing invariants (e.g., "no_representation_available") |
| data_source | string | ✅ Yes | Source of data (e.g., "Knot Atlas") |
| checksum | string | ✅ Yes | SHA-256 checksum of raw record |

**Invariant Dependency Note**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies must be acknowledged in all analysis and reporting.

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

**Attributes**:
| Field | Type | Description |
|-------|------|-------------|
| dataset_id | string | Unique dataset identifier |
| version | string | Dataset version (content hash) |
| created_at | timestamp | Dataset creation timestamp |
| source | string | Primary data source |
| total_records | integer | Total number of knot records |
| complete_records | integer | Records with all required fields populated |
| crossing_number_range | object | Min/max crossing number in dataset |
| validation_status | string | Validation status (e.g., "validated_≤10", "partial_≤13") |
| checksum | string | SHA-256 checksum of dataset file |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

**Attributes**:
| Field | Type | Description |
|-------|------|-------------|
| model_id | string | Unique model identifier |
| model_type | string | Type (e.g., "linear", "polynomial", "logarithmic") |
| predictors | array[string] | Predictor variables (e.g., ["crossing_number", "braid_index"]) |
| target | string | Target variable (e.g., "hyperbolic_volume") |
| coefficients | object | Model coefficients |
| r_squared | float | Coefficient of determination |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| vif_scores | object | Variance Inflation Factors for each predictor |
| training_sample_size | integer | Number of records in training set |
| validation_sample_size | integer | Number of records in validation set |
| random_seed | integer | Random seed used for split |
| created_at | timestamp | Model creation timestamp |

### CompositeComplexityScore

Represents the weighted complexity measure with attributes including weight parameters, per-knot scores, and validation correlation metrics.

**Attributes**:
| Field | Type | Description |
|-------|------|-------------|
| score_id | string | Unique score identifier |
| weight_crossing_number | float | Weight for crossing number (default: 0.5) |
| weight_braid_index | float | Weight for braid index (default: 0.5) |
| formula | string | Formula description (e.g., "0.5*crossing_number + 0.5*braid_index") |
| theoretical_basis | string | Theoretical justification (or "exploratory - no established basis") |
| validation_correlation_pearson | float | Pearson correlation with hyperbolic volume |
| validation_correlation_spearman | float | Spearman correlation with hyperbolic volume |
| validation_effect_size | float | Effect size (r or r²) |
| validation_sample_size | integer | Number of records in validation sample |
| random_seed | integer | Random seed used for split |
| created_at | timestamp | Score creation timestamp |

## Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Knot Atlas     │────▶│  Raw Data        │────▶│  Processed        │
│  (download)     │     │  (unchanged)     │     │  Dataset          │
└─────────────────┘     └──────────────────┘     └───────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Reproducibility│◀────│  Analysis        │◀────│  Invariant        │
│  Documentation  │     │  Outputs         │     │  Computation      │
└─────────────────┘     └──────────────────┘     └───────────────────┘
```

## Data Transformation Pipeline

### Stage 1: Download (FR-001)
- **Input**: Knot Atlas API
- **Output**: `data/raw/knot_atlas_export.json`
- **Transformation**: None (raw download)
- **Checksum**: SHA-256 recorded

### Stage 2: Parse and Clean (FR-002)
- **Input**: `data/raw/knot_atlas_export.json`
- **Output**: `data/processed/knot_records_cleaned.csv`
- **Transformation**: Extract consistent representations of crossing number, braid index, hyperbolic volume
- **Checksum**: SHA-256 recorded

### Stage 3: Invariant Computation (FR-003)
- **Input**: `data/processed/knot_records_cleaned.csv`
- **Output**: `data/processed/knot_records_with_invariants.csv`
- **Transformation**: Compute arc index, Seifert circle count, bridge number
- **Checksum**: SHA-256 recorded

### Stage 4: Exploratory Analysis (FR-004)
- **Input**: `data/processed/knot_records_with_invariants.csv`
- **Output**: `data/plots/crossing_vs_braid_alternating.png`, `data/plots/crossing_vs_braid_nonalternating.png`
- **Transformation**: Generate scatter plots with stratification
- **Resolution**: Minimum 1200x900 pixels

### Stage 5: Regression Modeling (FR-005)
- **Input**: `data/processed/knot_records_with_invariants.csv`
- **Output**: `data/processed/regression_results.json`
- **Transformation**: Fit 3 model types, compute metrics
- **Checksum**: SHA-256 recorded

### Stage 6: Composite Score (FR-006, FR-007)
- **Input**: `data/processed/knot_records_with_invariants.csv`
- **Output**: `data/processed/composite_complexity_scores.csv`
- **Transformation**: Apply weighted combination, validate correlation
- **Checksum**: SHA-256 recorded

## Validation Rules

### Completeness Validation (SC-001)
- **Threshold**: ≥95% completeness on required invariant fields for crossing number ≤10
- **Reference**: KnotInfo and Hoste-Thistlethwaite-Weeks enumeration
- **Documentation**: `docs/reproducibility/validation_scope.md`

### Algorithm Validation (SC-012)
- **Threshold**: ≥95% match with KnotInfo reference values where coverage ≥10%
- **Documentation**: `docs/reproducibility/algorithm_validation.md`
- **Skip Condition**: If KnotInfo coverage <10%, skip and document limitation

### Invariant Computation Coverage (SC-006)
- **Threshold**: ≥99% of knots with computable invariants have all invariants populated
- **Computable Definition**: (1) diagram representation available (non-null DT code OR braid word), AND (2) algorithm implemented
- **Documentation**: `docs/reproducibility/uncomputable_invariants.md`

### Classification Handling (SC-007)
- **Requirement**: All knots with ambiguous/missing alternating classification either excluded (with count logged) or marked "unclassifiable"
- **No silent exclusions**

### Hyperbolic Volume Filtering (FR-014, SC-014)
- **Requirement**: Filter dataset to include only prime knots with complete hyperbolic volume data
- **Excluded**: Torus/satellite knots where volume is zero or undefined
- **Documentation**: `docs/reproducibility/excluded_knots.md`
- **Completeness**: ≥95% hyperbolic volume data completeness for prime knots with crossing number ≤13
