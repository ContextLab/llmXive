# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with invariant data.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| knot_id | string | Unique identifier (e.g., "10_123") | Knot Atlas |
| crossing_number | integer | Minimum number of crossings | Knot Atlas |
| braid_index | integer | Minimum number of strands in braid representation | Knot Atlas |
| hyperbolic_volume | float | Hyperbolic volume (0 or undefined for torus/satellite) | Knot Atlas |
| is_alternating | boolean | Alternating classification | Knot Atlas |
| dt_code | string | Dowker-Thistlethwaite code | Knot Atlas |
| braid_word | string | Braid word representation | Knot Atlas |
| data_quality_flags | list | General data quality issues (null values, format failures, duplicates) | Derived |
| missing_invariant_flags | list | Invariants not computable from available representations | Derived |
| phase_1_validated | boolean | True if crossing number ≤10 (validated completeness) | Derived |
| is_hyperbolic | boolean | True if hyperbolic volume >0 | Derived |

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata.

| Field | Type | Description |
|-------|------|-------------|
| dataset_id | string | Unique dataset identifier |
| data_source | string | Source database (e.g., Knot Atlas) |
| created_at | datetime | Dataset creation timestamp (ISO 8601) |
| checksum | string | SHA-256 of raw data file |
| crossing_number_range | string | Range of crossing numbers included |
| validated_range | string | Range with validated completeness |
| total_records | integer | Total number of knot records |
| hyperbolic_records | integer | Number of hyperbolic knots (volume > 0) |
| null_percentage_crossing | number | Null percentage in crossing number field |
| null_percentage_braid | number | Null percentage in braid index field |
| null_percentage_volume | number | Null percentage in hyperbolic volume field |

### RegressionModel

Represents fitted regression model with metadata.

| Field | Type | Description |
|-------|------|-------------|
| model_id | string | Unique identifier for the model |
| model_type | string | "linear", "polynomial", or "logarithmic" |
| coefficients | dict | Model coefficients |
| r_squared | float | Coefficient of determination |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| predictors | list | Predictor variables used |
| residuals | list | Residual values for each record |
| target | string | Target variable name |
| fitted_timestamp | datetime | ISO 8601 timestamp when model was fitted |
| random_seed | integer | Random seed used for model fitting |
| census_data_flag | boolean | Always true for census data |
| p_value_disclaimer | string | Explicit disclaimer text for p-values in census data |
| multicollinearity_limitation | string | Documentation of braid index ≤ crossing number constraint |

## Data Flow

```
Knot Atlas (download)
    ↓
Raw Data (data/raw/knot_atlas_raw.json)
    ↓
Cleaned Data (data/processed/cleaned_knots.csv)
    ↓
Derived Invariants (data/processed/derived_invariants.csv)
    ↓
Regression Analysis (code/analysis/regression_models.py)
    ↓
Model Outputs (data/processed/regression_results.json)
```

## Data Quality Rules

1. **Null Values**: Required invariant fields (crossing_number, braid_index, hyperbolic_volume) must have a negligible null percentage.
2. **Format Validation**: DT code format must be valid; braid word format must be valid where present
3. **Duplicate Detection**: No duplicate knot IDs in output dataset
4. **Filtering**: Hyperbolic volume >0 for volume prediction analysis (exclude torus/satellite knots)

## Derived Fields

| Field | Derivation | Formula |
|-------|------------|---------|
| phase_1_validated | Classification | crossing_number ≤10 |
| is_hyperbolic | Classification | hyperbolic_volume >0 |
| residual | Computation | observed_volume - predicted_volume |
| standardized_residual | Computation | residual / std(residuals) |

## File Paths

| File | Path | Purpose |
|------|------|---------|
| Raw data | data/raw/knot_atlas_raw.json | Unmodified download |
| Cleaned data | data/processed/cleaned_knots.csv | Primary analysis dataset |
| Regression results | data/processed/regression_results.json | Model outputs |
| Checksums | data/checksums.json | SHA-256 for all data files |
| Logs | docs/reproducibility/*.md | Transformation logs |

## Statistical Reporting Policy (Census Data)

**p-values are NOT reported for census data**. This dataset represents complete enumeration of prime knots up to a defined crossing threshold (corresponding total per OEIS A002863). All statistical analysis is descriptive rather than inferential. Effect sizes are primary metrics. This policy is documented in plan.md, research.md, and enforced via regression_model.schema.yaml (census_data_flag: true, p_value_disclaimer field).