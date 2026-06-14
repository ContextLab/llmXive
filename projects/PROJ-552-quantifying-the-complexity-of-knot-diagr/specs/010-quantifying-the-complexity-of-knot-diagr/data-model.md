# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12

## Core Entities

### KnotRecord

Represents a single prime knot with attributes from Knot Atlas and computed relationships.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knot_id | string | Yes | Unique identifier (e.g., "10_5" for crossing number 10, knot 5) |
| crossing_number | integer | Yes | Minimum number of crossings in any diagram (tabulated) |
| braid_index | integer | Yes | Minimum number of strands in any braid representation (tabulated) |
| hyperbolic_volume | float | Conditional | Volume of knot complement (required for volume prediction analysis; zero/undefined for torus/satellite) |
| is_alternating | boolean | Conditional | Alternating vs. non-alternating classification (may be ambiguous/missing) |
| dt_code | string | Optional | Dowker-Thistlethwaite code representation |
| braid_word | string | Optional | Braid word representation |
| data_quality_flags | string | No | General data quality issues (null values, format failures, duplicates) |
| missing_invariant_flags | string | No | Specifically when invariants cannot be computed from available representations |
| source | string | Yes | Data source (e.g., "knot_atlas") |
| checksum | string | Yes | SHA-256 hash of record (for reproducibility) |

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata.

| Field | Type | Description |
|-------|------|-------------|
| dataset_id | string | Unique dataset identifier |
| data_source | string | Source database (e.g., Knot Atlas) |
| created_at | string | Dataset creation timestamp (ISO 8601) |
| checksum | string | SHA-256 checksum of dataset file |
| crossing_number_range | string | Range of crossing numbers included |
| validated_range | string | Range with validated completeness |
| total_records | integer | Total number of knot records |
| hyperbolic_records | integer | Number of hyperbolic knots (volume > 0) |
| null_percentage_crossing | number | Null percentage in crossing number field |
| null_percentage_braid | number | Null percentage in braid index field |
| null_percentage_volume | number | Null percentage in hyperbolic volume field |

### RegressionModel

Represents fitted model with attributes.

| Field | Type | Description |
|-------|------|-------------|
| model_id | string | Unique identifier |
| model_type | string | "linear", "polynomial", or "logarithmic" |
| predictors | array | Predictor variables (e.g., ["crossing_number", "braid_index"]) |
| target | string | Target variable (e.g., "hyperbolic_volume") |
| coefficients | object | Model coefficients |
| r_squared | float | Coefficient of determination (descriptive) |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| vif_scores | object | Variance Inflation Factor for each predictor |
| residual_outliers | array | Knot IDs with residuals ≥ 2 standard deviations |

## File Structure

```text
data/
├── raw/
│   ├── knot_atlas_raw.json          # Original download (FR-001)
│   └── knot_atlas_checksum.txt      # SHA-256 checksum
├── processed/
│   ├── knots_cleaned.csv            # Cleaned dataset (FR-002)
│   ├── knots_hyperbolic.csv         # Filtered to volume > 0 (FR-012)
│   └── knots_checksum.txt           # SHA-256 checksum
└── plots/
    ├── crossing_vs_braid_all.png    # FR-004: All knots
    ├── crossing_vs_braid_alternating.png  # FR-004: Alternating subset
    ├── crossing_vs_braid_non_alternating.png  # FR-004: Non-alternating subset
    └── residual_analysis.png        # SC-011: Residual patterns
```

## Data Transformations

| Step | Input | Output | Description | Derivation Notes |
|------|-------|--------|-------------|------------------|
| Download | Knot Atlas API | `raw/knot_atlas_raw.json` | Fetch all prime knots ≤ 13 crossings | FR-001; retry logic FR-008 |
| Parse | `raw/knot_atlas_raw.json` | `processed/knots_cleaned.csv` | Extract invariants, validate format | FR-002; format validation ≥ 99% |
| Filter | `processed/knots_cleaned.csv` | `processed/knots_hyperbolic.csv` | Keep volume > 0 only | FR-012; excluded documented |
| Plot | `processed/knots_hyperbolic.csv` | `plots/*.png` | Scatter plots (1200x900 min) | FR-004 |
| Model | `processed/knots_hyperbolic.csv` | `models/*.pkl` | Fit regression models | FR-005 |

## Validation Rules

| Rule | Condition | Action |
|------|-----------|--------|
| Unique IDs | knot_id must be unique | Reject duplicate; flag in data_quality_flags |
| Crossing number | Integer ≥ 1 | Reject invalid; flag in data_quality_flags |
| Braid index | Integer ≥ 1, ≤ crossing_number | Reject invalid; flag in data_quality_flags |
| Hyperbolic volume | Float ≥ 0 | Filter to > 0 for volume analysis (FR-012) |
| Alternating classification | Boolean or null | Exclude from stratified if null (FR-010) |
| DT code format | Valid DT code string | Flag format failures in data_quality_flags |
| Braid word format | Valid braid word string | Flag format failures in data_quality_flags |

## Reproducibility Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Checksums | `data/` | SHA-256 for all data files |
| Derivation notes | `docs/reproducibility/` | Step-by-step transformation logic |
| Logs | `docs/reproducibility/logs/` | Timestamped execution logs |
| Random seeds | `docs/reproducibility/random_seeds.md` | Seed values for stochastic operations |
| Validation reports | `docs/reproducibility/` | Data quality, tie-breaking, etc. |