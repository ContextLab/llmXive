# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with all required and optional attributes.

**Attributes**:
- `knot_id`: string, unique identifier (e.g., "10_123", "11n42")
- `crossing_number`: integer, number of crossings in minimal diagram
- `braid_index`: integer, minimum number of strands in braid representation
- `hyperbolic_volume`: float ≥ 0, hyperbolic volume of knot complement (0 for torus/satellite)
- `alternating`: boolean, true if knot is alternating, false otherwise
- `source`: object containing:
  - `database`: string, e.g., "Knot Atlas"
  - `version`: string, source version
  - `url`: string, canonical URL for record
  - `accessed_at`: ISO-8601 timestamp, when data was fetched
  - `source_timestamp`: ISO-8601 timestamp, when source record was created/updated
  - `checksum_sha256`: string, SHA-256 hash of raw source record
- `data_quality_flags`: array of strings, general data quality issues (e.g., "null_crossing_number", "format_failure", "duplicate_id")
- `missing_invariant_flags`: array of strings, invariants not computable from available representations (e.g., "no_braid_word", "no_dt_code")
- `unclassifiable`: boolean, true if alternating classification is ambiguous/missing

**Constraints**:
- `knot_id` must be unique across dataset
- `crossing_number` ≥ 1
- `braid_index` ≥ 1
- `hyperbolic_volume` ≥ 0
- `data_quality_flags` and `missing_invariant_flags` are mutually exclusive categories (FR-002 vs. FR-009)

### InvariantsDataset

Aggregated collection of `KnotRecord` entities with metadata.

**Attributes**:
- `records`: array of `KnotRecord` objects
- `metadata`: object containing:
  - `source_database`: string
  - `source_version`: string
  - `download_timestamp`: ISO-8601 timestamp
  - `total_records`: integer
  - `hyperbolic_records`: integer (volume > 0)
  - `alternating_records`: integer
  - `non_alternating_records`: integer
  - `unclassifiable_records`: integer
  - `null_counts`: object with field names as keys and null counts as values
  - `checksum_sha256`: string, SHA-256 of entire dataset

### RegressionModel

Represents a fitted regression model.

**Attributes**:
- `model_type`: string, e.g., "linear", "polynomial", "logarithmic"
- `coefficients`: array of floats, model coefficients
- `intercept`: float, model intercept
- `r_squared`: float, goodness-of-fit metric
- `aic`: float, Akaike Information Criterion
- `bic`: float, Bayesian Information Criterion
- `mae`: float, Mean Absolute Error
- `vif_crossing`: float, VIF for crossing number predictor
- `vif_braid`: float, VIF for braid index predictor
- `residuals`: array of floats, residual values for each knot
- `outlier_families`: array of strings, knot families with residuals ≥ 2σ

## Data Flow

1. **Raw Data**: `data/raw/knot_atlas_raw.json` (unmodified download)
2. **Parsed Data**: `data/processed/knots_parsed.csv` (extracted fields)
3. **Cleaned Data**: `data/processed/knots_cleaned.csv` (validated, deduplicated)
4. **Validated Data**: `data/processed/knots_validated.csv` (with flags, excluded knots marked)
5. **Filtered Data**: `data/processed/hyperbolic_knots.csv` (volume > 0 only)
6. **Analysis Outputs**: `data/processed/plots/` (PNG files), `data/processed/model_results.json`

## Transformation Rules

### Cleaning Rules (FR-002)

1. Remove duplicate `knot_id` records (keep first occurrence)
2. Flag records with null values in required fields (`crossing_number`, `braid_index`, `hyperbolic_volume`)
3. Validate format against `knot_record.schema.yaml`
4. Apply tie-breaking rules for multiple diagram representations (FR-011)

### Filtering Rules (FR-012)

1. Exclude knots with `hyperbolic_volume` = 0 or undefined (torus/satellite knots)
2. Document excluded knots in `docs/reproducibility/excluded_knots.md`
3. Filtered dataset used for volume prediction analysis only

### Flagging Rules (FR-009, FR-010)

1. `missing_invariant_flags`: Used when invariants cannot be computed from available diagram representations (Phase 2+ scope)
2. `data_quality_flags`: Used for general data quality issues (null values, format failures, duplicates)
3. `unclassifiable`: Set to true if alternating classification is ambiguous/missing; exclude from stratified analysis

## Derived Metrics

### Correlation Coefficients (FR-006)

- **Spearman**: Primary for discrete integer-valued invariants
- **Pearson**: Supplementary for reporting completeness
- **Effect Sizes**: r, r² for all correlations

### Group Comparison Metrics (FR-006, SC-009)

- **Mean Difference**: Alternating vs. non-alternating groups
- **Variance Ratio**: Variance ratio between groups
- **Cohen's d**: Effect size for group comparisons

### Regression Metrics (FR-005, SC-002)

- **R²**: Goodness-of-fit (descriptive for census data)
- **AIC/BIC**: Model selection criteria
- **MAE**: Mean Absolute Error
- **VIF**: Variance Inflation Factor (expected high due to mathematical constraint)
