# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, arc index, Seifert circle count, bridge number, alternating classification, and hyperbolic volume.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knot_id | string | Yes | Unique identifier (e.g., "10_123") |
| crossing_number | integer | Yes | Minimal crossing number |
| braid_index | integer | Yes | Minimal braid index |
| arc_index | integer | No | Arc index (computed via Birman-Menasco) |
| seifert_circle_count | integer | No | Seifert circle count (via Seifert's algorithm) |
| bridge_number | integer | No | Bridge number (via Schubert's decomposition) |
| is_alternating | boolean | No | Alternating classification (True/False/Null) |
| hyperbolic_volume | float | No | Hyperbolic volume (Null for torus/satellite knots) |
| missing_invariant_flags | array | No | List of flags for uncomputable invariants |
| diagram_representation | string | No | Preferred representation type (braid_word/dt_code) |
| checksum | string | Yes | SHA-256 hash for reproducibility |

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dataset_id | string | Yes | Unique identifier for dataset version |
| source | string | Yes | Data source (e.g., "Knot Atlas") |
| download_timestamp | datetime | Yes | When data was downloaded |
| computation_timestamp | datetime | Yes | When invariants were computed |
| total_records | integer | Yes | Total number of KnotRecords |
| valid_volume_records | integer | Yes | Records with non-null hyperbolic_volume |
| missing_invariant_count | integer | Yes | Records with missing_invariant_flags |
| unclassifiable_count | integer | Yes | Records with null is_alternating |
| schema_version | string | Yes | Data model schema version |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model_id | string | Yes | Unique identifier for model |
| model_type | string | Yes | Linear, polynomial, etc. |
| predictors | array | Yes | List of predictor variables |
| coefficients | object | Yes | Model coefficients |
| r_squared | float | Yes | R² goodness-of-fit metric |
| aic | float | Yes | Akaike Information Criterion |
| bic | float | Yes | Bayesian Information Criterion |
| mae | float | Yes | Mean Absolute Error |
| vif_values | object | Yes | Variance inflation factors per predictor |
| training_split | float | Yes | Training sample proportion (e.g., 0.8) |
| validation_split | float | Yes | Validation sample proportion (e.g., 0.2) |
| random_seed | integer | Yes | Random seed for reproducibility |

### CompositeComplexityScore

Represents the weighted complexity measure with attributes including weight parameters, per-knot scores, and validation correlation metrics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| score_id | string | Yes | Unique identifier for score configuration |
| crossing_weight | float | Yes | Weight for crossing number |
| braid_weight | float | Yes | Weight for braid index |
| formula | string | Yes | Mathematical formula used |
| knot_scores | object | Yes | Per-knot complexity scores |
| correlation_pearson | float | No | Pearson correlation with hyperbolic volume |
| correlation_spearman | float | No | Spearman correlation with hyperbolic volume |
| validation_sample_size | integer | Yes | Number of knots in validation sample |
| random_seed | integer | Yes | Random seed for stratified split |

## Invariant Dependency Note

Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies must be acknowledged in all analysis and reporting. Validation is exploratory correlation analysis, not independence testing.
