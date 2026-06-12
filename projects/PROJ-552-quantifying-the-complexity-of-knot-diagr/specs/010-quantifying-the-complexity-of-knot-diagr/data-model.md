# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, alternating classification, and hyperbolic volume.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knot_id | string | Yes | Unique identifier (e.g., "10_123" for crossing number 10, knot 123) |
| crossing_number | integer | Yes | Minimal number of crossings in any diagram representation |
| braid_index | integer | No | Minimal number of strands in any braid representation |
| hyperbolic_volume | float | No | Hyperbolic volume (0 or undefined for torus/satellite knots) |
| is_alternating | boolean | No | True if knot is alternating; null if ambiguous/missing |
| dt_code | string | No | Dowker-Thistlethwaite code for minimal crossing diagram |
| braid_word | string | No | Braid word representation if available |
| data_quality_flags | array | Yes | Flags for general data quality issues (null values, format failures, duplicates) |
| missing_invariant_flags | array | Yes | Flags for invariants not computable from available diagram representations |
| source | string | Yes | Data source (e.g., "knot_atlas") |
| download_timestamp | datetime | Yes | When record was downloaded |

**Invariant Dependency Note**: Additional invariants (arc index, Seifert circle count, bridge number) have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies must be acknowledged in all analysis and reporting. **Additional Invariants Cannot Claim Independent Predictive Value**: Due to known mathematical dependencies, additional invariants cannot claim independent predictive value beyond crossing number and braid index.

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Field | Type | Description |
|-------|------|-------------|
| dataset_id | string | Unique identifier for dataset version |
| records | array of KnotRecord | All knot records in dataset |
| total_count | integer | Total number of records |
| hyperbolic_count | integer | Count of records with hyperbolic_volume > 0 |
| alternating_count | integer | Count of alternating knots |
| non_alternating_count | integer | Count of non-alternating knots |
| null_percentage_crossing | float | Percentage of records with null crossing_number |
| null_percentage_braid | float | Percentage of records with null braid_index |
| null_percentage_volume | float | Percentage of records with null hyperbolic_volume |
| checksum | string | SHA-256 hash of dataset file |
| created_at | datetime | Dataset creation timestamp |
| source_version | string | Version/hash of source data |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Field | Type | Description |
|-------|------|-------------|
| model_id | string | Unique identifier for model instance |
| model_type | string | Type of model (linear, polynomial, logarithmic) |
| predictors | array | List of predictor variables used |
| coefficients | object | Mapping of predictor names to coefficient values |
| r_squared | float | Coefficient of determination |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| residuals | array | Array of residual values |
| residual_families | array | Names of knot families with ≥2σ deviation |
| fitted_at | datetime | When model was fitted |

## Data Flow

```
Knot Atlas Download → Raw CSV → Cleaned Dataset → Invariants Dataset → Regression Models → Results Report
```

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| raw_knots.csv | data/raw/knot_atlas_export.csv | Unprocessed download from Knot Atlas |
| cleaned_knots.csv | data/processed/cleaned_knots.csv | Cleaned dataset with quality flags |
| invariants_computed.csv | data/processed/invariants_computed.csv | Dataset with additional computed invariants (Phase 2+) |
| regression_results.json | data/processed/regression_results.json | Fitted model parameters and metrics |
| plots/crossing_vs_braid.png | data/plots/crossing_vs_braid.png | Exploratory analysis visualization |
