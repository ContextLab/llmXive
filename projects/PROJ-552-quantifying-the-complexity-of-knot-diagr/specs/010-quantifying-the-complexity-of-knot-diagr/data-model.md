# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Core Entities

### KnotRecord

Represents a single prime knot with attributes extracted from Knot Atlas.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| knot_id | string | YES | Unique identifier from Knot Atlas |
| crossing_number | integer | YES | Minimal crossing number (tabulated) |
| braid_index | integer | NO | Minimal braid index (tabulated); may be null if unavailable |
| hyperbolic_volume | float | NO | Hyperbolic volume in units of volume; null for torus/satellite knots |
| is_alternating | boolean | NO | Alternating classification; null if ambiguous |
| dt_code | string | NO | Dowker-Thistlethwaite code representation |
| braid_word | string | NO | Braid word representation |
| data_quality_flags | list[string] | YES | General data quality flags (null values, format failures, duplicates) |
| missing_invariant_flags | list[string] | YES | Specific invariant computation flags (per FR-009) |

**Invariant Dependency Note**: Additional invariants (arc index, Seifert circle count, bridge number) have known mathematical constraints with crossing number and braid index. These dependencies must be acknowledged in all analysis and reporting.

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata.

| Attribute | Type | Description |
|-----------|------|-------------|
| records | list[KnotRecord] | All knot records |
| total_count | integer | Total number of records |
| hyperbolic_count | integer | Number of records with volume > 0 |
| alternating_count | integer | Number of alternating knots |
| non_alternating_count | integer | Number of non-alternating knots |
| validation_scope | string | "≤10" for Phase 1 validated; "≤13" for full data availability |
| checksum | string | SHA-256 checksum of dataset file |
| created_at | timestamp | Dataset creation timestamp |
| source | string | Data source identifier (e.g., "Knot Atlas") |

### RegressionModel

Represents a fitted regression model with metadata.

| Attribute | Type | Description |
|-----------|------|-------------|
| model_type | string | "linear", "polynomial", or "logarithmic" |
| coefficients | dict | Model coefficients |
| r_squared | float | Goodness-of-fit R² |
| aic | float | Akaike Information Criterion |
| bic | float | Bayesian Information Criterion |
| mae | float | Mean Absolute Error |
| predictors | list[string] | Predictor variables used |
| target | string | Target variable |
| residual_families | list[string] | Families with significant deviations (≥2 SD) |
| vif_scores | dict | Variance Inflation Factor per predictor |

## Data Flow

```
download_knot_data.py
    ↓ (raw data)
raw/knot_atlas_export.json
    ↓ (checksum + validation)
data/processed/cleaned_knots.parquet
    ↓ (exploratory analysis)
data/plots/crossing_vs_braid_scatter.png
    ↓ (regression fitting)
data/processed/regression_results.parquet
    ↓ (reproducibility artifacts)
docs/reproducibility/
```

## Data Quality Requirements

Per FR-002:
- Null percentage in required invariant fields < negligible threshold
- Format validation passes for all records (valid DT code, valid braid word)
- Zero duplicates in output dataset

Per FR-009:
- Records with uncomputable invariants flagged with missing_invariant_flags
- Distinct from data_quality_flags (which handles null values, format failures, duplicates)
