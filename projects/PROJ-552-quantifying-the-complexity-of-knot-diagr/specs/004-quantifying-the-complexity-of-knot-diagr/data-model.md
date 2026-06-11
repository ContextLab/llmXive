# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Key Entities

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, arc index, Seifert circle count, bridge number, alternating classification, and hyperbolic volume.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knot_id | string | Yes | Unique identifier for the knot |
| crossing_number | integer | Yes | Minimum number of crossings in any diagram |
| braid_index | integer | Yes | Minimum number of strands in any braid representation |
| arc_index | integer | No | Arc index computed via Birman-Menasco method |
| seifert_circle_count | integer | No | Seifert circle count from Seifert's algorithm |
| bridge_number | integer | No | Bridge number from Schubert's decomposition |
| is_alternating | boolean | Yes | True if alternating, false if non-alternating |
| hyperbolic_volume | float | No | Hyperbolic volume (null for torus/satellite knots) |
| dt_code | string | No | Dowker-Thistlethwaite code |
| braid_word | string | No | Braid word representation |
| missing_invariant_flags | array[string] | Yes | Flags for invariants that could not be computed |
| data_source | string | Yes | Source of the record (e.g., "knot_info") |

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Field | Type | Description |
|-------|------|-------------|
| records | array[KnotRecord] | All knot records |
| total_count | integer | Total number of records |
| alternating_count | integer | Count of alternating knots |
| non_alternating_count | integer | Count of non-alternating knots |
| hyperbolic_volume_available_count | integer | Count with valid hyperbolic volume |
| computation_timestamp | timestamp | When invariants were computed |
| checksum | string | SHA-256 checksum of the dataset |

### RegressionOutput

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Field | Type | Description |
|-------|------|-------------|
| model_id | string | Unique identifier for the model |
| model_type | string | Linear, polynomial (degree=2), or logarithmic (base e) |
| predictors | array[string] | List of predictor variables |
| coefficients | object | Model coefficients |
| r_squared | float | Coefficient of determination |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| vif_scores | object | Variance inflation factors per predictor |
| training_sample_size | integer | Number of samples in training set |
| validation_sample_size | integer | Number of samples in validation set |
| random_seed | integer | Random seed used for split |

### CompositeComplexityScore

Represents the weighted complexity measure with attributes including weight parameters, per-knot scores, and validation correlation metrics.

**Weighting Disclaimer**: Composite score weighting is exploratory/arbitrary. Equal-weight default is a heuristic without theoretical justification. Results should be interpreted as exploratory constructs, not established complexity measures.

| Field | Type | Description |
|-------|------|-------------|
| score_id | string | Unique identifier for the score |
| crossing_weight | float | Weight for crossing number (default: 1.0) |
| braid_weight | float | Weight for braid index (default: 1.0) |
| per_knot_scores | object | Composite score for each knot |
| correlation_pearson | float | Pearson correlation with hyperbolic volume |
| correlation_spearman | float | Spearman correlation with hyperbolic volume |
| p_value | float | Statistical significance of correlation |
| effect_size | float | Cohen's d or r effect size |
| validation_sample_size | integer | Number of samples in validation |
| random_seed | integer | Random seed used for split |

## Data Flow

```
KnotInfo/HTW (raw) → parse_knot_data.py → InvariantsDataset (processed)
                                      ↓
                              compute_invariants.py
                                      ↓
                              exploratory_analysis.py → plots
                                      ↓
                              regression_models.py → RegressionOutput
                                      ↓
                              composite_score.py → CompositeComplexityScore
```

## Data Hygiene Rules

1. **No in-place modification**: All transformations produce new files with documented derivation
2. **Checksumming**: All files under data/ are checksummed (SHA-256)
3. **Raw data preservation**: Raw data from KnotInfo/HTW is kept unchanged in data/raw/
4. **Derivation documentation**: All transformations documented in docs/reproducibility/derivation_notes.md
5. **Reproducibility**: All stochastic operations use pinned random seeds

## Invariant Dependency Note

Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies create fundamental multicollinearity when using both crossing number and braid index as independent predictors. VIF can flag but not resolve this mathematical constraint. Analysis acknowledges predictors are mathematically linked, not independent.