# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Key Entities

### KnotRecord

Represents a single prime knot with attributes including computed invariants and classification.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `knot_id` | string | Unique identifier (e.g., "3_1", "4_1", "10_123") | Yes |
| `crossing_number` | integer | Minimal crossing number of the knot | Yes |
| `braid_index` | integer | Minimal braid index (algorithmically determined) | Yes |
| `hyperbolic_volume` | float | Hyperbolic volume (filtered for valid values) | Yes |
| `is_alternating` | string | Alternating classification ("true"/"false"/"unclassifiable") | Yes |
| `arc_index` | integer | Arc index (computed via Birman-Menasco) | No |
| `seifert_circle_count` | integer | Seifert circle count (computed via Seifert's algorithm) | No |
| `bridge_number` | integer | Bridge number (computed via Schubert's decomposition) | No |
| `dt_code` | string | Dowker-Thistlethwaite code representation | No |
| `braid_word` | string | Braid word representation | No |
| `missing_invariant_flags` | array[string] | Flags for missing computable invariants | No |
| `data_source` | string | Source of original data (e.g., "knot_atlas") | Yes |
| `download_timestamp` | datetime | When data was downloaded | Yes |
| `checksum_sha256` | string | SHA-256 checksum of source record | Yes |

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | Unique dataset identifier |
| `knot_records` | array[KnotRecord] | Array of knot records |
| `total_knots` | integer | Total number of knots in dataset |
| `crossing_number_range` | object | Min and max crossing numbers |
| `alternating_count` | integer | Count of alternating knots |
| `non_alternating_count` | integer | Count of non-alternating knots |
| `unclassifiable_count` | integer | Count of unclassifiable knots |
| `data_source` | string | Primary data source |
| `created_timestamp` | datetime | When dataset was created |
| `checksum_sha256` | string | SHA-256 checksum of dataset file |

### RegressionModel

Represents fitted model with attributes including coefficients and metrics.

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string | Unique model identifier |
| `model_type` | string | "linear", "polynomial", or "logarithmic" |
| `predictors` | array[string] | List of predictor variables |
| `outcome` | string | Outcome variable name |
| `coefficients` | object | Model coefficients |
| `r_squared` | float | R² goodness-of-fit |
| `aic` | float | Akaike Information Criterion |
| `bic` | float | Bayesian Information Criterion |
| `mae` | float | Mean Absolute Error |
| `vif_values` | object | Variance inflation factors per predictor |
| `training_sample_size` | integer | Number of samples in training set |
| `validation_sample_size` | integer | Number of samples in validation set |
| `created_timestamp` | datetime | When model was fitted |

### CompositeComplexityScore

Represents the weighted complexity measure.

| Field | Type | Description |
|-------|------|-------------|
| `score_id` | string | Unique score identifier |
| `crossing_weight` | float | Weight for crossing number |
| `braid_weight` | float | Weight for braid index |
| `per_knot_scores` | object | Map of knot_id to complexity score |
| `correlation_pearson` | float | Pearson correlation with hyperbolic volume |
| `correlation_spearman` | float | Spearman correlation with hyperbolic volume |
| `validation_sample_size` | integer | Size of exploratory validation sample |
| `created_timestamp` | datetime | When score was computed |

## Data Flow

```
Knot Atlas (https://katlas.org)
    ↓ [FR-001: Download]
raw/knot_atlas_export.csv
    ↓ [FR-002: Parse & Clean]
processed/invariants_dataset.parquet
    ↓ [FR-003: Compute Invariants]
processed/invariants_dataset_with_computed.parquet
    ↓ [FR-004: Exploratory Analysis]
data/plots/*.png
    ↓ [FR-005: Regression Fitting]
models/regression_models.json
    ↓ [FR-006: Composite Score]
models/composite_complexity_score.json
```

## Data Hygiene Requirements

1. **Checksumming**: All files under `data/` must be checksummed with SHA-256; checksums recorded in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml`
2. **No In-Place Modification**: Raw data preserved unchanged; derivations produce new files with new names
3. **Derivation Notes**: All transformations documented in `docs/reproducibility/` with formula citations, step-by-step logic, intermediate values, and parameter justifications
4. **Random Seeds**: All stochastic operations pinned with documented seed values in `docs/reproducibility/`