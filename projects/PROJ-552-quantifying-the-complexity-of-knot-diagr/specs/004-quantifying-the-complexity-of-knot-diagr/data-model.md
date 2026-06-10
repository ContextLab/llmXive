# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31

## Entity Relationship Diagram

```
┌─────────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
│   KnotRecord        │──────▶│  InvariantsDataset  │◀──────│  RegressionModel    │
│                     │       │                     │       │                     │
│ - knot_id           │       │ - knots[]           │       │ - model_id          │
│ - crossing_number   │       │ - metadata          │       │ - model_type        │
│ - braid_index       │       │ - source            │       │ - coefficients      │
│ - hyperbolic_volume │       │ - created_at        │       │ - metrics           │
│ - alternating       │       │ - checksum          │       │ - validation_data   │
│ - diagram_type      │       └─────────────────────┘       └─────────────────────┘
│ - dt_code           │
│ - braid_word        │
│ - missing_flags     │
│ - checksum          │
└─────────────────────┘
```

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, arc index, Seifert circle count, bridge number, alternating classification, and hyperbolic volume.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| knot_id | string | Yes | Unique identifier for the knot | Format: "c{crossing}_{name}" (e.g., "c10_123") |
| crossing_number | integer | Yes | Minimum number of crossings in any diagram | Range: [1, 13] for Phase 1 |
| braid_index | integer | Yes | Minimum number of strands in braid representation | Range: [2, crossing_number] |
| hyperbolic_volume | float | Conditional | Volume of hyperbolic complement | Required for volume prediction analysis; exclude if zero/undefined (torus/satellite knots) |
| alternating | boolean | Conditional | Whether knot is alternating | Must be true/false; "unclassifiable" if ambiguous/missing |
| arc_index | integer | Conditional | Minimum number of arcs in grid diagram | Computed via Birman-Menasco method |
| seifert_circle_count | integer | Conditional | Number of Seifert circles in minimal diagram | Computed via Seifert's algorithm |
| bridge_number | integer | Conditional | Minimum number of bridges | Computed via Schubert's decomposition |
| diagram_type | string | No | Type of diagram representation available | One of: "braid_word", "dt_code", "both", "none" |
| dt_code | string | No | Dowker-Thistlethwaite code | May be null if not available |
| braid_word | string | No | Braid word representation | May be null if not available |
| missing_invariant_flags | array[string] | No | Flags for missing computable invariants | Values: "arc_index", "seifert_circle_count", "bridge_number" |
| checksum | string | Yes | SHA-256 hash of record | Used for reproducibility tracking |

### InvariantsDataset

Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| dataset_id | string | Yes | Unique identifier for dataset version | Format: "invariants_{timestamp}" |
| knots | array[KnotRecord] | Yes | Collection of knot records | Must include all prime knots with crossing number ≤13 |
| metadata | object | Yes | Dataset metadata | Includes source, version, creation timestamp |
| source | string | Yes | Data source name | "knot_atlas" |
| created_at | string | Yes | ISO 8601 timestamp | Format: "YYYY-MM-DDTHH:MM:SSZ" |
| checksum | string | Yes | SHA-256 hash of entire dataset | Stored in `data/checksums.txt` |
| validation_scope | string | Yes | Scope of validation | "crossing_number_≤10" for Phase 1 |
| completeness_rate | float | Yes | Percentage of records with complete invariant fields | Target: ≥95% |

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| model_id | string | Yes | Unique identifier for model | Format: "model_{type}_{timestamp}" |
| model_type | string | Yes | Type of regression model | One of: "linear", "polynomial", "logarithmic" |
| coefficients | object | Yes | Model coefficients | Keys: predictor names; Values: coefficient values |
| metrics | object | Yes | Goodness-of-fit metrics | Includes R², AIC, BIC, MAE |
| vif_values | object | Yes | Variance Inflation Factors | Keys: predictor names; Values: VIF scores |
| validation_data | object | Yes | Validation sample information | Includes split ratio, random seed, correlation results |
| residuals | array[object] | No | Residual analysis results | Includes knot families with significant deviations |
| created_at | string | Yes | ISO 8601 timestamp | Format: "YYYY-MM-DDTHH:MM:SSZ" |

### CompositeComplexityScore

Represents the weighted complexity measure with attributes including weight parameters, per-knot scores, and validation correlation metrics.

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| score_id | string | Yes | Unique identifier for score configuration | Format: "complexity_{timestamp}" |
| weight_crossing | float | Yes | Weight for crossing number | Default: 1.0 |
| weight_braid | float | Yes | Weight for braid index | Default: 1.0 |
| per_knot_scores | array[object] | Yes | Score for each knot | Includes knot_id and computed score |
| correlation_metrics | object | Yes | Validation correlation results | Includes Pearson r, Spearman rho, effect sizes |
| config_file | string | Yes | Path to configuration file | "config/complexity_weights.yaml" |
| theoretical_basis | string | Yes | Theoretical justification | "exploratory" (no established basis in literature) |

## Data Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Knot Atlas API  │────▶│  Raw Data File   │────▶│  Cleaned Dataset │
│  (knots ≤13)     │     │  data/raw/       │     │  data/processed/ │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                         │
                                                         ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Regression      │◀────│  Invariant       │◀────│  Computed        │
│  Model Output    │     │  Computation     │     │  Invariants      │
│  data/results/   │     │  code/compute/   │     │  data/processed/ │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

## Validation Rules

### Crossing Number Validation

- Must be integer in range [1, 13] for Phase 1 data collection
- Must be integer in range [1, 10] for Phase 1 validated data
- Cross-reference with Hoste-Thistlethwaite-Weeks enumeration for completeness check

### Braid Index Validation

- Must satisfy inequality: 2 ≤ braid_index ≤ crossing_number (for most knots)
- Must be validated against KnotInfo reference values where available
- Pass/fail threshold: ≥95% match with reference values where reference data exists

### Hyperbolic Volume Validation

- Must be positive float for hyperbolic knots
- Zero or undefined values indicate torus/satellite knots; must be excluded from volume prediction analysis
- Excluded records documented in `docs/reproducibility/excluded_knots.md`

### Missing Data Handling

- Records with missing invariant data flagged with `missing_invariant_flags`
- Records NOT silently excluded from dataset
- Summary report generated at `docs/reproducibility/uncomputable_invariants.md`

### Classification Handling

- Ambiguous alternating/non-alternating classification: mark as "unclassifiable"
- Unclassifiable records excluded from stratified analysis (with count logged)
- No silent exclusions occur

## File Organization

```
data/
├── raw/
│   ├── knots_raw.csv              # Unmodified download from Knot Atlas
│   └── knots_raw_checksum.txt     # SHA-256 checksum of raw file
├── processed/
│   ├── knots_cleaned.csv          # Parsed and cleaned dataset
│   ├── knots_with_invariants.csv  # Dataset with computed invariants
│   └── plots/                     # Exploratory analysis plots (PNG, 1200x900px min)
│       ├── crossing_vs_braid_alternating.png
│       └── crossing_vs_braid_non_alternating.png
├── results/
│   ├── regression_models.json     # Fitted model coefficients and metrics
│   ├── composite_scores.json      # Composite complexity scores
│   └── statistical_tests.json     # ANOVA, correlation results
└── checksums.txt                  # All data file checksums
```
