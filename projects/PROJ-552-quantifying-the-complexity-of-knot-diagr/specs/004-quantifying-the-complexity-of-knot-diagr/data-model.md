# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Key Entities

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, arc index, Seifert circle count, bridge number, alternating classification, and hyperbolic volume.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| knot_id | string | Yes | Unique identifier (e.g., "3_1", "4_1", "13_9988") |
| crossing_number | integer | Yes | Tabulated crossing number (minimal crossing count) |
| braid_index | integer | Yes | Braid index from algorithmic determination or tabulated value |
| arc_index | integer | No | Computed via Birman-Menasco method; null if not computable |
| seifert_circle_count | integer | No | Computed via Seifert's algorithm; null if not computable |
| bridge_number | integer | No | Computed via Schubert's decomposition; null if not computable |
| is_alternating | boolean | No | Alternating classification; null if ambiguous/missing |
| knot_family | string | No | Knot family classification (torus, satellite, pretzel, hyperbolic, unknown); null if unknown |
| hyperbolic_volume | float | No | Hyperbolic volume; null for torus/satellite knots (volume zero or undefined) |
| dt_code | string | No | Dowker-Thistlethwaite code representation |
| braid_word | string | No | Braid word representation |
| missing_invariant_flags | array[string] | No | List of invariants that could not be computed |
| data_source | string | Yes | Source of data (e.g., "knot_atlas") |
| checksum | string | Yes | SHA-256 checksum of record data |
| volume_filter_flag | boolean | No | True if excluded from volume analysis per FR-014 |

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Attribute | Type | Description |
|-----------|------|-------------|
| dataset_id | string | Unique identifier for dataset version |
| source | string | Data source (e.g., "knot_atlas") |
| download_timestamp | datetime | When data was downloaded |
| total_knots | integer | Total number of knot records |
| alternating_count | integer | Count of alternating knots |
| non_alternating_count | integer | Count of non-alternating knots |
| unclassifiable_count | integer | Count of knots with ambiguous classification |
| missing_volume_count | integer | Count of knots with missing hyperbolic volume |
| excluded_volume_count | integer | Count of knots excluded per FR-014 (torus/satellite) |
| volume_completeness_pct | float | Percentage of knots with valid hyperbolic volume (SC-014) |
| checksum | string | SHA-256 checksum of dataset file |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Attribute | Type | Description |
|-----------|------|-------------|
| model_id | string | Unique identifier for model |
| model_type | string | Type: "linear", "polynomial", "logarithmic" |
| predictors | array[string] | List of predictor variables (e.g., ["crossing_number", "braid_index"]) |
| coefficients | object | Model coefficients (JSON object) |
| r_squared | float | R² goodness-of-fit metric |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| vif_scores | object | Variance Inflation Factors for each predictor |
| training_sample_size | integer | Number of knots in training sample |
| validation_sample_size | integer | Number of knots in validation sample |
| random_seed | integer | Random seed used for sample split |

### RegressionResult

Extended regression output including multicollinearity flag and target variable specification.

| Attribute | Type | Description |
|-----------|------|-------------|
| model_id | string | Unique identifier for model |
| model_type | string | Type: "linear", "polynomial", "logarithmic" |
| predictors | array[string] | List of predictor variables |
| target | string | Target variable (hyperbolic_volume) |
| coefficients | object | Model coefficients |
| r_squared | float | R² goodness-of-fit metric |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| vif_scores | object | Variance Inflation Factors for each predictor |
| multicollinearity_flag | boolean | True if any VIF > 5 |
| training_sample_size | integer | Number of knots in training sample |
| validation_sample_size | integer | Number of knots in validation sample |
| random_seed | integer | Random seed used for sample split |

### CompositeComplexityScore

Represents the weighted complexity measure with attributes including weight parameters, per-knot scores, and validation correlation metrics.

| Attribute | Type | Description |
|-----------|------|-------------|
| score_id | string | Unique identifier for score version |
| crossing_weight | float | Weight for crossing number (default: 1.0) |
| braid_weight | float | Weight for braid index (default: 1.0) |
| per_knot_scores | object | Map of knot_id to complexity score |
| pearson_correlation | float | Pearson correlation with hyperbolic volume |
| spearman_correlation | float | Spearman correlation with hyperbolic volume |
| effect_size | float | Effect size measure (r or r²) |
| validation_sample_size | integer | Number of knots in validation sample |
| random_seed | integer | Random seed used for sample split |

## Data Flow

```
knot_atlas_raw.json (data/raw/)
 ↓ [download_knot_atlas.py]
knots_cleaned.csv (data/processed/)
 ↓ [compute_invariants.py]
 ↓ [validate_discrepancies.py → docs/reproducibility/discrepancy_notes.md] # Constitution Principle VI
knots_with_invariants.csv (data/processed/)
 ↓ [volume_completeness.py → docs/reproducibility/excluded_knots.md] # FR-014/SC-014
knots_filtered_volume.csv (data/processed/)
 ↓ [exploratory_analysis.py]
crossing_vs_braid_alternating.png, crossing_vs_braid_nonalternating.png (data/plots/)
 ↓ [regression_models.py]
regression_results.json (data/processed/)
 ↓ [statistical_tests.py]
validation_results.json (data/processed/)
```

## Data Transformations

All transformations produce new files with documented derivation notes in `docs/reproducibility/derivation_notes.md`:

1. **Raw to Cleaned**: Parse Knot Atlas JSON, extract required fields, handle missing values
2. **Cleaned to Invariants**: Compute arc index, Seifert circle count, bridge number from available diagram representations
3. **Invariants to Discrepancy Notes**: Compare computed invariants against canonical values; document discrepancies per Constitution Principle VI
4. **Invariants to Volume-Filtered**: Filter torus/satellite knots with zero/undefined hyperbolic volume per FR-014; document excluded knots per SC-014
5. **Filtered to Plots**: Generate scatter plots with stratification by alternating classification
6. **Filtered to Regression**: Fit multiple model types, compute goodness-of-fit metrics
7. **Regression to Validation**: Construct composite complexity score, validate against exploratory validation sample

## Data Quality Rules

| Rule | Action on Violation |
|------|---------------------|
| crossing_number > 0 | Flag record, log to uncomputable_invariants.md |
| hyperbolic_volume ≤ 0 OR null | Exclude from volume prediction analysis per FR-014, log to excluded_knots.md per SC-014 |
| is_alternating is null | Mark as "unclassifiable", exclude from stratified analysis |
| missing_invariant_flags contains all invariants | Record retained with flags, excluded from invariant analysis |
| Any required field missing for crossing_number ≤10 | Flag for Phase 1 completeness validation |
| knot_family is unknown | Retain record, mark as "unknown" for covariate modeling |
| Volume completeness < 95% | SC-014 violation; document in validation_status.md |
