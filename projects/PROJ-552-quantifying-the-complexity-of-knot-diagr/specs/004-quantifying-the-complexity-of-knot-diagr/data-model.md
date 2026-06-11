# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Entity Overview

This document describes the data entities used throughout the project, their attributes, relationships, and validation constraints.

## Core Entities

### KnotRecord

Represents a single prime knot with all computed and tabulated invariants.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `knot_id` | string | Unique identifier (e.g., "10_123" for 123rd knot with 10 crossings) | Required, unique |
| `crossing_number` | integer | Tabulated crossing number | Required, ≥ 3, ≤ 13 |
| `braid_index` | integer | Algorithmically determined braid index | Required, ≥ 2 |
| `hyperbolic_volume` | float | Hyperbolic volume (geometric invariant) | Required for volume analysis, > 0 |
| `is_alternating` | boolean | Alternating classification | Required, true/false |
| `arc_index` | integer | Computed arc index | Optional, ≥ 2 |
| `seifert_circle_count` | integer | Computed Seifert circle count | Optional, ≥ 1 |
| `bridge_number` | integer | Computed bridge number | Optional, ≥ 2 |
| `dt_code` | string | Dowker-Thistlethwaite code | Optional |
| `braid_word` | string | Braid word representation | Optional |
| `missing_invariant_flags` | list[string] | Flags for missing computable invariants | Optional, empty list if all present |
| `data_source` | string | Source of data (e.g., "knot_atlas", "computed") | Required |
| `computation_timestamp` | datetime | When invariants were computed | Required |
| `checksum` | string | SHA-256 checksum of record | Required |

**Invariant Dependency Note**: Bridge number ≤ crossing number for most knots (known inequality). This dependency must be acknowledged in all analysis and reporting.

### InvariantsDataset

Aggregated collection of KnotRecord entities with metadata.

| Attribute | Type | Description |
|-----------|------|-------------|
| `dataset_id` | string | Unique dataset identifier |
| `knot_records` | list[KnotRecord] | All knot records |
| `total_count` | integer | Total number of knots |
| `alternating_count` | integer | Number of alternating knots |
| `non_alternating_count` | integer | Number of non-alternating knots |
| `volume_complete_count` | integer | Knots with complete hyperbolic volume |
| `computation_timestamp` | datetime | When dataset was created |
| `data_source_version` | string | Version of Knot Atlas data (tracked from API response) |
| `checksum` | string | SHA-256 checksum of dataset |

### RegressionModel

Represents fitted regression model with metrics.

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_id` | string | Unique model identifier |
| `model_type` | string | "linear", "polynomial", "logarithmic", or "spline" |
| `coefficients` | dict | Model coefficients |
| `r_squared` | float | R² goodness-of-fit |
| `aic` | float | Akaike Information Criterion |
| `bic` | float | Bayesian Information Criterion |
| `mae` | float | Mean Absolute Error |
| `vif_scores` | dict | Variance Inflation Factors per predictor |
| `training_sample_size` | integer | Number of knots in training sample |
| `validation_sample_size` | integer | Number of knots in validation sample |
| `residual_families` | list[string] | Knot families with significant deviations |
| `fit_timestamp` | datetime | When model was fitted |

**Schema Governance**: Regression output MUST conform to `contracts/regression_output.schema.yaml` (CANONICAL).

### CompositeComplexityScore

Weighted complexity measure.

| Attribute | Type | Description |
|-----------|------|-------------|
| `score_id` | string | Unique score identifier |
| `crossing_weight` | float | Weight for crossing number (default: 1.0) |
| `braid_weight` | float | Weight for braid index (default: 1.0) |
| `per_knot_scores` | dict[knot_id, float] | Score per knot |
| `correlation_pearson` | float | Pearson correlation with hyperbolic volume |
| `correlation_spearman` | float | Spearman correlation with hyperbolic volume |
| `effect_size_r` | float | Effect size (r) |
| `validation_sample_size` | integer | Number of knots in validation |
| `creation_timestamp` | datetime | When score was created |

**Storage Location**: CompositeComplexityScore records are stored in `data/processed/validation_results.parquet` (not separate file).

## Data Flow

```
Knot Atlas API
    ↓ (download_knots.py)
Raw Dataset (data/raw/knot_atlas_*.parquet)
    ↓ (parse_knots.py)
Cleaned Dataset (data/processed/cleaned_*.parquet)
    ↓ (compute_invariants.py)
Invariants Dataset (data/processed/invariants_*.parquet)
    ↓ (exploratory.py)
Plots (data/plots/*.png) + Exploratory Results
    ↓ (regression.py)
Regression Results (data/processed/regression_results_*.parquet) [conforms to regression_output.schema.yaml]
    ↓ (validation.py)
Validation Results (data/processed/validation_results.parquet) [includes CompositeComplexityScore]
```

## Validation Constraints

1. **Crossing Number**: Must be integer ≥ 3 and ≤ 13 (Phase 1 scope)
2. **Braid Index**: Must be integer ≥ 2 (per knot theory constraints)
3. **Hyperbolic Volume**: Must be float > 0 for volume prediction analysis (torus/satellite knots excluded)
4. **Missing Invariant Flags**: Records with computable invariants missing must be flagged, not silently excluded
5. **Checksums**: All data files under `data/` must have SHA-256 checksums recorded
6. **Random Seeds**: All stochastic operations must use pinned random seeds documented in `docs/reproducibility/`
7. **Inequality Verification**: Known mathematical inequalities (bridge ≤ crossing, etc.) must be verified empirically before analysis per Constitution Principle VI
8. **Spec Defect Tracking**: SC-006 (provisional) and SC-012 (provisional) thresholds documented; validation checks use provisional values pending spec amendment

## File Locations

| Data Type | Location | Format |
|-----------|----------|--------|
| Raw Knot Atlas Data | `data/raw/knot_atlas_*.parquet` | Parquet |
| Cleaned Dataset | `data/processed/cleaned_*.parquet` | Parquet |
| Invariants Dataset | `data/processed/invariants_*.parquet` | Parquet |
| Regression Results | `data/processed/regression_results_*.parquet` | Parquet (conforms to regression_output.schema.yaml) |
| Validation Results | `data/processed/validation_results.parquet` | Parquet (includes CompositeComplexityScore) |
| Exploratory Plots | `data/plots/*.png` | PNG (minimum 1200x900 pixels) |
| Reproducibility Docs | `docs/reproducibility/` | Markdown |
| Power Analysis | `docs/reproducibility/power_analysis.md` | Markdown |
| License Compliance | `docs/reproducibility/license_compliance.md` | Markdown |
| Spec Defects | `docs/reproducibility/spec_defects.md` | Markdown |

## License Compliance

Knot Atlas data license terms will be checked and documented in `docs/reproducibility/license_compliance.md`. Redistribution and reproducibility requirements documented per Constitution Principle III.