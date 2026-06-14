# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entities

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, alternating classification, and hyperbolic volume.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `knot_id` | string | Unique identifier (e.g., "10_123") | Required, Unique |
| `crossing_number` | integer | Number of crossings in minimal diagram | ≥ 1, ≤ 13 |
| `braid_index` | integer | Minimum number of strands in braid representation | ≥ 1, ≤ crossing_number |
| `hyperbolic_volume` | float | Volume of hyperbolic complement | > 0 (for hyperbolic knots), null otherwise |
| `is_alternating` | boolean | Classification as alternating or non-alternating | null if ambiguous |
| `data_quality_flags` | list[string] | General data quality issues (null values, format failures) | Optional |
| `missing_invariant_flags` | list[string] | Invariants not computable from available representations | Optional |

### InvariantsDataset

Aggregated collection of `KnotRecord` entities with computed relationships and metadata.

| Field | Type | Description |
|-------|------|-------------|
| `records` | list[KnotRecord] | Collection of knot records |
| `metadata` | object | Data source, computation timestamp, checksums |
| `validation_scope` | string | Phase 1 benchmark (≤ 10 crossings) vs exploratory (11-13) |
| `crossing_number_at` | integer | Crossing number for this dataset subset (e.g., 13 for 9988 knots per OEIS A002863) |
| `cumulative_note` | string | Documentation that cumulative ≤13 is [deferred]+ knots |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | "linear", "polynomial", or "logarithmic" |
| `coefficients` | dict | Model parameters |
| `r_squared` | float | Goodness-of-fit metric (descriptive) |
| `aic` | float | Akaike Information Criterion |
| `bic` | float | Bayesian Information Criterion |
| `mae` | float | Mean Absolute Error |

## Data Flow

1.  **Download**: Raw JSON from Knot Atlas → `data/raw/knot_atlas_export.json`
2.  **Parse/Clean**: Raw JSON → `data/processed/invariants_dataset.csv` (with flags)
3.  **Analyze**: Dataset → `docs/reproducibility/regression_results.json`
4.  **Visualize**: Dataset → `data/plots/crossing_vs_braid.png`