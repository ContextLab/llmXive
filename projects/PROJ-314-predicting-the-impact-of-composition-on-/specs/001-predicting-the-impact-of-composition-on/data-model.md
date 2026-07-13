# Data Model: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in CSV/Parquet formats with strict schema enforcement.

## Entity Definitions

### 1. CeramicEntry (Raw & Processed)

Represents a single material sample.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier (hash of composition + params) | Unique |
| `composition` | string | Chemical formula (e.g., "Al2O3") | Not null |
| `weibull_modulus` | float | Target variable (m) | Not null |
| `sample_count` | int | Number of samples in Weibull test ($N$) | $\ge 30$ (filtered) |
| `sintering_temp` | float | Processing parameter (°C) | Nullable (imputed) |
| `is_imputed` | boolean | True if sintering_temp was imputed | Default: False |
| `is_range_flag` | boolean | True if original value was a range | Default: False |
| `range_original` | string | Original string if range (e.g., "10-15") | Nullable |
| `range_uncertainty` | float | Width of the range (max - min) | Nullable |
| `primary_anion_cation_group` | string | Derived group (e.g., "Oxide-Aluminum") | Not null |
| `source` | string | Original dataset/paper source | Not null |
| `is_high_bias_class` | boolean | True if class has >40% imputed data | Default: False |

### 2. DescriptorSet (Engineered Features)

Computed features appended to `CeramicEntry`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `mean_atomic_radius` | float | Weighted mean of atomic radii |
| `electronegativity_std` | float | Standard deviation of electronegativity |
| `valence_electron_concentration` | float | Total valence electrons / total atoms |
| `cation_size_variance` | float | Variance of cation ionic radii |
| `vif_flags` | list | List of features with VIF > 5 (for correlation clustering) |

### 3. ModelResult

Output of the training pipeline.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "RandomForest" or "GradientBoosting" |
| `mae` | float | Mean Absolute Error |
| `r_squared` | float | Coefficient of determination |
| `mae_95_ci` | list | [lower, upper] of 95% CI via bootstrapping |
| `feature_importance_ranking` | list | Top 10 features by importance (or cluster names) |
| `cv_stability_scores` | dict | CV of feature importance across folds |
| `vif_flags` | list | Features with VIF > 5 |
| `leakage_warning` | boolean | *Deprecated*: Replaced by `descriptor_sufficiency` |
| `descriptor_sufficiency` | boolean | True if descriptors capture class physics (no drop when group removed) |
| `baseline_mae` | float | MAE of the global mean baseline |
| `improvement_percentage` | float | Percentage improvement over baseline |
| `permutation_p_value` | float | p-value from permutation test for SC-001 |
| `is_significant` | boolean | True if p < 0.05 and improvement >= 10% |

## Data Flow

1.  **Raw Ingestion**: `data/raw/` (Checksummed)
2.  **Cleaning**: `data/processed/cleaned.csv` (Filter $N < 30$, impute missing, add flags)
3.  **Feature Engineering**: `data/processed/features.csv` (Add descriptors, VIF flags)
4.  **Model Output**: `data/outputs/model_results.json`

## Constraints & Rules

-   **Immutability**: Raw files are never modified.
-   **Imputation**: Missing `sintering_temp` is imputed with group median, then global median. `is_imputed` flag is set to True.
-   **Range Handling**: Midpoint used for calculation; original string preserved; `range_uncertainty` added.
-   **Filtering**: Any entry with `sample_count` < 30 is permanently excluded from training.
-   **High-Bias Class**: Classes with >40% imputed data are flagged and excluded from training.