# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, alternating classification, and hyperbolic volume.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| knot_id | string | Yes | Unique identifier (e.g., "K11n34") | Non-empty, unique |
| crossing_number | integer | Yes | Number of crossings in minimal diagram | ≥1 |
| braid_index | integer | No | Minimum number of strands in braid representation | ≥1, ≤crossing_number |
| hyperbolic_volume | float | No | Volume of hyperbolic complement | >0 for hyperbolic knots |
| is_alternating | boolean | No | Whether knot is alternating | null if ambiguous |
| dt_code | string | No | Dowker-Thistlethwaite code | Valid DT format |
| braid_word | string | No | Braid word representation | Valid braid word format |
| data_quality_flags | string | No | Flags for data quality issues | Comma-separated |
| missing_invariant_flags | string | No | Flags for missing computable invariants | Comma-separated |
| data_source | string | Yes | Data source (e.g., "Knot Atlas") | Non-empty |
| download_timestamp | datetime | Yes | When data was downloaded | ISO 8601 format |

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Field | Type | Description |
|-------|------|-------------|
| dataset_id | string | Unique dataset identifier |
| version | string | Semantic version (e.g., "1.0.0") |
| total_knots | integer | Total number of KnotRecord entities |
| hyperbolic_knots | integer | Count of knots with hyperbolic_volume > 0 |
| alternating_knots | integer | Count of knots with is_alternating = true |
| non_alternating_knots | integer | Count of knots with is_alternating = false |
| unclassifiable_knots | integer | Count of knots with is_alternating = null |
| null_percentage_crossing | float | Percentage of null values in crossing_number |
| null_percentage_braid | float | Percentage of null values in braid_index |
| null_percentage_volume | float | Percentage of null values in hyperbolic_volume |
| checksum_sha256 | string | SHA-256 checksum of dataset file |
| created_at | datetime | Dataset creation timestamp |
| source_checksum | string | SHA-256 checksum of raw source data |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Field | Type | Description |
|-------|------|-------------|
| model_id | string | Unique model identifier |
| model_type | string | "linear", "polynomial", or "logarithmic" |
| predictor_variables | list | List of predictor variables (e.g., ["crossing_number", "braid_index"]) |
| coefficients | dict | Model coefficients |
| r_squared | float | Coefficient of determination |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| vif_crossing | float | Variance Inflation Factor for crossing_number |
| vif_braid | float | Variance Inflation Factor for braid_index |
| residual_std | float | Standard deviation of residuals |
| outlier_families | list | Knot families with residuals ≥2 standard deviations |
| fitted_at | datetime | Model fitting timestamp |
| random_seed | integer | Random seed used for fitting |

## Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Knot Atlas    │────▶│  Raw Data File  │────▶│  Cleaned Data   │
│   (download)    │     │  (data/raw/)    │     │  (data/processed/)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │  Analysis Output│
                                              │  (data/plots/)  │
                                              └─────────────────┘
```

## File Organization

```
data/
├── raw/
│   ├── knot_atlas_raw.csv          # Unmodified downloaded data
│   └── knot_atlas_raw.csv.sha256   # Checksum for raw data
├── processed/
│   ├── knots_cleaned.csv           # Cleaned dataset (no in-place modification)
│   ├── knots_cleaned.csv.sha256    # Checksum for cleaned data
│   └── knots_hyperbolic.csv        # Filtered to volume > 0
├── plots/
│   ├── crossing_vs_braid.png       # Scatter plot (1200x900 min resolution)
│   └── alternating_stratified.png  # Stratified by alternating classification
└── models/
    ├── regression_linear.pkl       # Fitted linear model
    ├── regression_polynomial.pkl   # Fitted polynomial model
    └── regression_logarithmic.pkl  # Fitted logarithmic model
```

## Validation Rules

### Data Quality (FR-002)

1. **Null Percentage**: Required invariant fields must have null percentage <5% in validated dataset subset
2. **Format Validation**: Valid DT code format, valid braid word format where present
3. **Duplicate Detection**: Zero duplicates in output dataset

### Filtering (FR-012)

- Filter to knots with hyperbolic_volume > 0 for volume prediction analysis
- Exclude torus/satellite knots (volume = 0 or undefined)
- Excluded records documented in `docs/reproducibility/excluded_knots.md`

### Flag Distinction

- **data_quality_flags**: General data quality issues (null values, format failures, duplicates)
- **missing_invariant_flags**: Specifically when invariants cannot be computed from available diagram representations