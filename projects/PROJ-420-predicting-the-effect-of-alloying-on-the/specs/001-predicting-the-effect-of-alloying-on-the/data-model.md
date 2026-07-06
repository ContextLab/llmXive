# Data Model: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Overview

This document defines the data structures and transformations used in the project. It ensures consistency between the raw data extraction, the modeling pipeline, and the final output.

## Entities

### 1. AlloyRecord (Raw & Processed)

Represents a single aluminum alloy entry.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `alloy_id` | string | Unique identifier from source. | Non-null, unique. |
| `source` | string | "Materials Project" or "NIST". | Non-null. |
| `poissons_ratio` | float | Poisson's ratio. | Non-null, > 0, < 1. |
| `youngs_modulus_gpa` | float | Young's modulus in GPa. | Non-null, > 0. |
| `fraction_cu` | float | Atomic fraction of Copper. | ≥ 0, ≤ 1. |
| `fraction_mg` | float | Atomic fraction of Magnesium. | ≥ 0, ≤ 1. |
| `fraction_si` | float | Atomic fraction of Silicon. | ≥ 0, ≤ 1. |
| `fraction_zn` | float | Atomic fraction of Zinc. | ≥ 0, ≤ 1. |
| `fraction_mn` | float | Atomic fraction of Manganese. | ≥ 0, ≤ 1. |
| `fraction_al` | float | Calculated atomic fraction of Aluminum. | `1.0 - sum(other fractions)`. |
| `sum_major_elements` | float | Sum of Cu, Mg, Si, Zn, Mn fractions. | Must be ≥ 0.95 (else excluded). |
| `measurement_method` | string | Method used to measure Poisson's ratio. | Must be "ultrasonic" or "experimental" (else excluded). |
| `is_independent_measurement` | boolean | Flag for Poisson's ratio independence. | Must be True (else excluded/flagged). |

### 2. ILRFeatureVector

The transformed feature set used for modeling.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `alloy_id` | string | Reference to source. | Non-null. |
| `ilr_1` ... `ilr_4` | float | Isometric Log-Ratio transformed coordinates. | Real numbers. |
| *Note*: ILR transforms D components into D-1 coordinates. Here D=5 (Cu, Mg, Si, Zn, Mn), so 4 coordinates. |

### 3. ModelMetrics

Output metrics from the modeling phase.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `cv_mae` | float | Mean Absolute Error from 5-fold CV. | ≥ 0. |
| `test_mae` | float | Mean Absolute Error on held-out test set. | ≥ 0. |
| `model_type` | string | "Random Forest". | Constant. |
| `random_seed` | integer | Seed used for reproducibility. | Pinned. |

### 4. CollinearityDiagnostic

Diagnostic output for raw composition collinearity.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `element` | string | Element name (Cu, Mg, Si, Zn, Mn). | Non-null. |
| `vif_score` | float | Variance Inflation Factor. | ≥ 1.0. |
| `is_flagged` | boolean | True if VIF > 5. | **Clarification**: Indicates "High collinearity in raw space (expected)", not a model failure. |

## Transformations

1.  **Normalization**: Convert all elastic constants to GPa.
2.  **Filtering**: Remove rows where `sum_major_elements` < 0.95 or missing required fields.
3.  **Independence Filter**: Remove rows where `measurement_method` is not "ultrasonic" or "experimental".
4.  **ILR Transformation**:
    - Input: Vector $x = [x_1, x_2, x_3, x_4, x_5]$ (atomic fractions).
    - Method: Apply sequential binary partition or standard basis to compute ILR coordinates.
    - Output: Vector $z = [z_1, z_2, z_3, z_4]$.
5.  **Back-transformation for Importance**: Map feature importance from $z$ space to $x$ space using a perturbation-based sensitivity analysis (shuffling original components and measuring impact on ILR-transformed predictions).

## Data Flow

1.  `data/raw` (JSON/CSV) -> `data_extraction.py` -> `data/processed/alloy_records.parquet`
2.  `alloy_records.parquet` -> `data_cleaning.py` -> `data/processed/cleaned_records.parquet`
3.  `cleaned_records.parquet` -> `modeling.py` -> `data/processed/ilr_features.parquet` + `models/random_forest.joblib`
4.  `models/random_forest.joblib` + `cleaned_records.parquet` -> `analysis.py` -> `data/processed/metrics.json`, `data/processed/diagnostics.json`