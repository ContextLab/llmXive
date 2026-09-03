# Data Model: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Overview

This document defines the data structures used throughout the project. It ensures consistency between data extraction, cleaning, modeling, and reporting.

## Core Entities

### 1. AlloyRecord
Represents a single aluminum alloy entry after cleaning and validation.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `alloy_id` | str | Unique identifier for the alloy record. | Required, unique. |
| `source` | str | Source of the data (e.g., "Materials Project", "NIST"). | Required. |
| `composition` | dict | Atomic fractions of alloying elements. | Keys: `Cu`, `Mg`, `Si`, `Zn`, `Mn`, `Al`. Values: float [0, 1]. Sum = 1.0. |
| `poisson_ratio` | float | Poisson's ratio (dimensionless). | Required, > 0. |
| `youngs_modulus_gpa` | float | Young's modulus in GPa. | Required, > 0. |
| `measurement_method` | str | Description of how Poisson's ratio was measured. | Optional (may be null if not in source). |
| `is_independent_measurement` | bool | True if Poisson's ratio is an independent measurement. | Required. |
| `row_index` | int | Original row index in the raw dataset. | Required for traceability. |

### 2. ILRFeatures
Represents the transformed feature vector for modeling.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `alloy_id` | str | Reference to the original AlloyRecord. | Required. |
| `ilr_1` | float | First ILR coordinate. | Derived from composition (SBP basis). |
| `ilr_2` | float | Second ILR coordinate. | Derived from composition (SBP basis). |
| `ilr_3` | float | Third ILR coordinate. | Derived from composition (SBP basis). |
| `ilr_4` | float | Fourth ILR coordinate. | Derived from composition (SBP basis). |
| `ilr_5` | float | Fifth ILR coordinate. | Derived from composition (SBP basis). |

*Note: For 5 alloying elements + Al (6 components), the ILR transformation yields 5 coordinates.*

### 3. ModelMetrics
Stores the results of the modeling process.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `cv_mae_mean` | float | Mean Absolute Error from 5-fold CV. | Required. |
| `cv_mae_ci_lower` | float | 95% Confidence Interval Lower Bound. | Required. |
| `cv_mae_ci_upper` | float | 95% Confidence Interval Upper Bound. | Required. |
| `test_mae` | float | Mean Absolute Error on the held-out test set. | Required. |
| `best_params` | dict | Best hyperparameters found during CV. | Required. |
| `feature_importance` | dict | Importance scores for each alloying element (Grouped ILR). | Keys: `Cu`, `Mg`, `Si`, `Zn`, `Mn`. Values: float. |
| `vif_scores` | dict | Variance Inflation Factors for ILR features. | Keys: `ilr_1`...`ilr_5`. Values: float. |
| `vif_flag` | bool | True if any VIF > 5. | Required. |
| `associational_framing` | bool | True if results are framed as associational. | Required (const: true). |

## Data Flow

1.  **Raw Data**: Downloaded from source (JSON/CSV/Parquet).
2.  **Cleaned Data**: Filtered and normalized `AlloyRecord` objects. Saved as `data/processed/alloys_clean.parquet`.
3.  **Transformed Data**: `ILRFeatures` derived from `AlloyRecord`. Used for training.
4.  **Model Output**: `ModelMetrics` saved as JSON files in `results/`.

## Data Integrity Rules

- **Unit Consistency**: All elastic constants must be in GPa.
- **Compositional Sum**: `Cu + Mg + Si + Zn + Mn + Al` must equal 1.0 (within floating point tolerance).
- **Missing Data**: Any record with missing `poisson_ratio`, `youngs_modulus`, or any of the 5 alloying elements is excluded.
- **Independence**: Records where `is_independent_measurement` is False or Unknown are excluded.
- **Traceability**: Every processed record must retain its `row_index` from the raw source.