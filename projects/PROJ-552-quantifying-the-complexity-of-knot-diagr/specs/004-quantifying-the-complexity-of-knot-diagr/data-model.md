# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31

## Entity Overview

This project models knot data and analysis results as the following key entities:

1. **KnotRecord** - Represents a single prime knot with all associated invariants
2. **InvariantsDataset** - Aggregated collection of KnotRecord entities
3. **RegressionModel** - Represents fitted statistical model
4. **CompositeComplexityScore** - Represents the weighted complexity measure

## Entity Definitions

### KnotRecord

A single prime knot with all computed and tabulated invariants.

| Attribute | Type | Description | Required | Constraints |
|-----------|------|-------------|----------|-------------|
| `knot_id` | string | Unique identifier (e.g., "10_123" for 123rd knot with 10 crossings) | Yes | Format: `{crossing_number}_{index}` |
| `crossing_number` | integer | Tabulated crossing number (minimum crossings in any diagram) | Yes | ≥0, validated against KnotInfo |
| `braid_index` | integer | Minimum number of strands in any braid representation | Yes | ≥1, ≤crossing_number (for most knots) |
| `hyperbolic_volume` | float | Hyperbolic volume of knot complement | Yes (for volume analysis) | >0 (exclude torus/satellite with volume=0 or undefined) |
| `is_alternating` | boolean | Whether knot is alternating or non-alternating | Yes | True = alternating, False = non-alternating, null = unclassifiable |
| `arc_index` | integer | Minimum number of arcs in any grid diagram (computed) | No | ≥crossing_number (known constraint) |
| `seifert_circle_count` | integer | Number of Seifert circles from Seifert's algorithm (computed) | No | ≥1 |
| `bridge_number` | integer | Minimum number of bridges in any bridge decomposition (computed) | No | ≤crossing_number (known constraint) |
| `dt_code` | string | Dowker-Thistlethwaite code representation | No | Non-empty if available |
| `braid_word` | string | Braid word representation | No | Non-empty if available |
| `missing_invariant_flags` | array[string] | Flags for which invariants could not be computed | No | Values: "no_representation_available", "algorithm_not_implemented" |
| `data_source` | string | Source of the knot data | Yes | "knot_atlas" |
| `data_timestamp` | string | ISO 8601 timestamp of data download | Yes | Format: "YYYY-MM-DDTHH:MM:SSZ" |

**Invariant Dependency Note**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies must be acknowledged in all analysis and reporting. Validation is exploratory correlation, not independence testing (see spec.md).

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata.

| Attribute | Type | Description | Required | Constraints |
|-----------|------|-------------|----------|-------------|
| `dataset_id` | string | Unique identifier for the dataset version | Yes | Format: "knots_{date}_{version}" |
| `knot_records` | array[KnotRecord] | Collection of all knot records | Yes | ≥1 record |
| `total_knots` | integer | Total number of knots in dataset | Yes | Matches length of knot_records |
| `crossing_number_range` | object | Min and max crossing numbers | Yes | {min: integer, max: integer} |
| `alternating_count` | integer | Number of alternating knots | Yes | ≥0 |
| `non_alternating_count` | integer | Number of non-alternating knots | Yes | ≥0 |
| `unclassifiable_count` | integer | Number of knots with ambiguous classification | Yes | ≥0 |
| `volume_data_complete_count` | integer | Number of knots with valid hyperbolic volume | Yes | ≥0 |
| `invariant_computation_coverage` | object | Coverage for each computed invariant | Yes | {arc_index: float, seifert_circle_count: float, bridge_number: float} (0.0-1.0) |
| `checksum` | string | SHA-256 checksum of dataset file | Yes | 64-character hex string |
| `derivation_notes_path` | string | Path to derivation notes document | Yes | Relative path to `docs/reproducibility/` |
| `created_at` | string | ISO 8601 timestamp of dataset creation | Yes | Format: "YYYY-MM-DDTHH:MM:SSZ" |

### RegressionModel

Represents fitted statistical model for predicting hyperbolic volume.

| Attribute | Type | Description | Required | Constraints |
|-----------|------|-------------|----------|-------------|
| `model_id` | string | Unique identifier for the model | Yes | Format: "regression_{model_type}_{timestamp}" |
| `model_type` | string | Type of regression model | Yes | "linear", "polynomial", "logarithmic" |
| `predictors` | array[string] | List of predictor variables | Yes | Must include "crossing_number", "braid_index" |
| `coefficients` | object | Model coefficients | Yes | {predictor_name: coefficient_value} |
| `intercept` | float | Model intercept | Yes | |
| `r_squared` | float | Coefficient of determination | Yes | 0.0-1.0 |
| `adjusted_r_squared` | float | Adjusted R² for number of predictors | Yes | 0.0-1.0 |
| `aic` | float | Akaike Information Criterion | Yes | |
| `bic` | float | Bayesian Information Criterion | Yes | |
| `mae` | float | Mean Absolute Error | Yes | ≥0 |
| `rmse` | float | Root Mean Squared Error | Yes | ≥0 |
| `vif_scores` | object | Variance Inflation Factors for predictors | Yes | {predictor_name: vif_value} |
| `residual_outliers` | array[string] | Knot IDs that deviate significantly from predictions | Yes | List of knot_ids |
| `training_sample_size` | integer | Number of knots in training sample | Yes | ≥1 |
| `validation_sample_size` | integer | Number of knots in validation sample | Yes | ≥1 |
| `random_seed` | integer | Random seed used for sample split | Yes | |
| `created_at` | string | ISO 8601 timestamp of model creation | Yes | Format: "YYYY-MM-DDTHH:MM:SSZ" |

**Multicollinearity Note**: VIF scores must be documented alongside model metrics. If VIF > 5 for any predictor, this must be flagged in final reports as a potential multicollinearity issue affecting coefficient interpretation (FR-005).

### CompositeComplexityScore

Represents the weighted complexity measure.

| Attribute | Type | Description | Required | Constraints |
|-----------|------|-------------|----------|-------------|
| `score_id` | string | Unique identifier for the score configuration | Yes | Format: "complexity_{weights_hash}_{timestamp}" |
| `weight_crossing_number` | float | Weight for crossing number | Yes | ≥0, default 0.5 |
| `weight_braid_index` | float | Weight for braid index | Yes | ≥0, default 0.5 |
| `weights_config_path` | string | Path to weights configuration file | Yes | Relative path to `config/complexity_weights.yaml` |
| `per_knot_scores` | array[object] | Complexity score for each knot | Yes | [{knot_id: string, score: float}] |
| `correlation_pearson` | float | Pearson correlation with hyperbolic volume | Yes | -1.0 to 1.0 |
| `correlation_spearman` | float | Spearman correlation with hyperbolic volume | Yes | -1.0 to 1.0 |
| `correlation_effect_size` | float | Effect size (r or r²) for correlation | Yes | ≥0 |
| `validation_sample_size` | integer | Number of knots in validation sample | Yes | ≥1 |
| `validation_method` | string | Method used for validation | Yes | "exploratory_validation_sample" |
| `random_seed` | integer | Random seed used for sample split | Yes | |
| `created_at` | string | ISO 8601 timestamp of score creation | Yes | Format: "YYYY-MM-DDTHH:MM:SSZ" |

**Theoretical Limitation Acknowledgment**: No established mathematical basis exists in knot theory literature for linear combination of crossing number and braid index. The equal-weight default is exploratory and configurable. This limitation must be acknowledged in all final reports (FR-006).

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA PIPELINE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Knot Atlas (https://katlas.org)                                    │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ download_knot_atlas.py                                       │   │
│  │ - Retry logic with exponential backoff                       │   │
│  │ - Cache partial results after 3 failures                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│           │                                                         │
│           ▼                                                         │
│  data/raw/knot_atlas_{date}.json (SHA-256 checksummed)             │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ parse_and_clean.py                                           │   │
│  │ - Extract consistent representations                        │   │
│  │ - Flag missing invariant data                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│           │                                                         │
│           ▼                                                         │
│  data/derived/knots_cleaned.parquet                                │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ compute_invariants.py                                        │   │
│  │ - Arc index (Birman-Menasco)                                 │   │
│  │ - Seifert circle count (Seifert's algorithm)                 │   │
│  │ - Bridge number (Schubert's decomposition)                   │   │
│  │ - Validate against KnotInfo (≥10% coverage)                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│           │                                                         │
│           ▼                                                         │
│  data/derived/knots_with_invariants.parquet                        │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ exploratory_analysis.py                                      │   │
│  │ - Scatter plots (crossing number vs. braid index)           │   │
│  │ - Stratified by alternating/non-alternating                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│           │                                                         │
│           ▼                                                         │
│  data/derived/plots/crossing_vs_braid_*.png                        │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ regression_models.py                                         │   │
│  │ - Linear, polynomial, logarithmic models                     │   │
│  │ - VIF assessment for multicollinearity                       │   │
│  │ - Residual analysis for outlier knot families                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│           │                                                         │
│           ▼                                                         │
│  data/derived/regression_models.parquet                            │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ statistical_tests.py                                         │   │
│  │ - Pearson AND Spearman correlations                          │   │
│  │ - ANOVA (with assumption checks)                             │   │
│  │ - Effect size reporting (Cohen's d, r²)                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│           │                                                         │
│           ▼                                                         │
│  data/derived/statistical_results.parquet                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## File Formats

### Parquet Schema

All derived datasets stored in Parquet format with the following schema:

| Column | Type | Nullable |
|--------|------|----------|
| knot_id | string | No |
| crossing_number | int32 | No |
| braid_index | int32 | No |
| hyperbolic_volume | float64 | Yes |
| is_alternating | boolean | Yes |
| arc_index | int32 | Yes |
| seifert_circle_count | int32 | Yes |
| bridge_number | int32 | Yes |
| dt_code | string | Yes |
| braid_word | string | Yes |
| missing_invariant_flags | string (JSON array) | Yes |
| data_source | string | No |
| data_timestamp | string (ISO 8601) | No |

### Checksum Format

Checksums recorded in `data/checksums.txt`:

```
<sha256_hash>  <relative_path>
```

Example:
```
a1b2c3d4e5f6...  data/raw/knot_atlas_2026-05-31.json
b2c3d4e5f6a1...  data/derived/knots_cleaned.parquet
```

### Log Format

Execution logs in `docs/reproducibility/logs/`:

```json
{
  "timestamp": "2026-05-31T14:30:00Z",
  "operation": "download_knot_atlas",
  "input_file": null,
  "output_file": "data/raw/knot_atlas_2026-05-31.json",
  "parameters": {"retry_count": 3, "backoff_max_seconds": 60},
  "status": "success",
  "duration_ms": 45230,
  "error": null
}
```
