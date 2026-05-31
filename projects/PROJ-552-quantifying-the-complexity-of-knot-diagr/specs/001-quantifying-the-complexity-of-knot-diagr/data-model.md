# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Definitions

### KnotRecord

Represents a single prime knot with all computed invariants and metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| knot_id | string | Yes | Unique identifier (e.g., "8_19" for knot 8.19) |
| crossing_number | integer | Yes | Minimum crossing number of the knot |
| braid_index | integer | Yes | Minimum braid index of the knot |
| is_alternating | boolean | Yes | Whether the knot is alternating (True), non-alternating (False), or unclassifiable (None) |
| arc_index | integer | No | Arc index (computed via Birman-Menasco method) |
| seifert_circle_count | integer | No | Seifert circle count (computed via Seifert's algorithm) |
| bridge_number | integer | No | Bridge number (computed via Schubert's bridge decomposition) |
| braid_word | string | No | Braid word representation if available |
| dt_code | string | No | Dowker-Thistlethwaite code if available |
| missing_invariant_flags | array[string] | No | List of reasons why invariants could not be computed |
| source_checksum | string | Yes | SHA-256 checksum of source record |

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dataset_id | string | Yes | Unique identifier for this dataset version |
| created_at | timestamp | Yes | ISO 8601 timestamp of dataset creation |
| random_seed | integer | Yes | Random seed used for any stochastic operations |
| total_knots | integer | Yes | Total number of knots in dataset |
| alternating_count | integer | Yes | Number of alternating knots |
| non_alternating_count | integer | Yes | Number of non-alternating knots |
| unclassifiable_count | integer | Yes | Number of knots with ambiguous classification |
| missing_invariant_counts | object | Yes | Count of records missing each invariant type |
| source_urls | array[string] | Yes | Original data source URLs (may be empty if no verified sources) |
| checksums | object | Yes | SHA-256 checksums for all data files |

### RegressionModel

Represents a fitted regression model.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model_id | string | Yes | Unique identifier for this model |
| model_type | string | Yes | "linear" or "polynomial" (degree specified) |
| coefficients | object | Yes | Model coefficients as key-value pairs |
| r_squared | float | Yes | Coefficient of determination |
| aic | float | Yes | Akaike Information Criterion |
| bic | float | Yes | Bayesian Information Criterion |
| training_size | integer | Yes | Number of records used for training |
| validation_size | integer | Yes | Number of records used for validation |
| random_seed | integer | Yes | Random seed used for train/validation split |

### CompositeComplexityScore

Represents the weighted complexity measure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| score_id | string | Yes | Unique identifier for this score configuration |
| crossing_weight | float | Yes | Weight applied to crossing number (default 0.5) |
| braid_weight | float | Yes | Weight applied to braid index (default 0.5) |
| per_knot_scores | object | Yes | Map of knot_id to computed score |
| validation_correlation_pearson | object | Yes | Pearson correlation with arc index and Seifert circle count |
| validation_correlation_spearman | object | Yes | Spearman correlation with arc index and Seifert circle count |
| effect_sizes | object | Yes | Cohen's d and r values for all correlations |

## Data Flow

```
knot_atlas_download → knot_atlas_raw.json
                    ↓
            knot_atlas_cleaned.csv
                    ↓
       invariants_computed.csv
                    ↓
        exploratory_plots.png
                    ↓
         regression_models.pkl
                    ↓
        composite_scores.csv
                    ↓
    validation_results.json
```

## File Formats

- **Raw Data**: JSON (from Knot Atlas API)
- **Processed Data**: CSV with UTF-8 encoding
- **Plots**: PNG with minimum 1200x900 pixels
- **Models**: Pickle (with version pinning)
- **Validation Results**: JSON with structured output
