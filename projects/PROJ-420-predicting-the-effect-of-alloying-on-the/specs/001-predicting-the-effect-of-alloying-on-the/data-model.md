# Data Model: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Overview

This document defines the data structures used throughout the project, ensuring consistency between data extraction, processing, modeling, and output. All data is stored in Parquet format for efficient I/O and schema enforcement.

## Entity Definitions

### 1. AlloyRecord
Represents a single aluminum alloy entry after cleaning and filtering.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `alloy_id` | string | Unique identifier for the alloy | Primary Key |
| `poissons_ratio` | float | Poisson's ratio (dimensionless) | Non-null, 0 < value < 0.5 |
| `youngs_modulus_gpa` | float | Young's modulus in GPa | Non-null, > 0 |
| `composition_cu` | float | Atomic fraction of Copper | 0 ≤ value ≤ 1 |
| `composition_mg` | float | Atomic fraction of Magnesium | 0 ≤ value ≤ 1 |
| `composition_si` | float | Atomic fraction of Silicon | 0 ≤ value ≤ 1 |
| `composition_zn` | float | Atomic fraction of Zinc | 0 ≤ value ≤ 1 |
| `composition_mn` | float | Atomic fraction of Manganese | 0 ≤ value ≤ 1 |
| `composition_al` | float | Atomic fraction of Aluminum (calculated) | 1.0 - sum(other elements) |
| `sum_major_elements` | float | Sum of Cu, Mg, Si, Zn, Mn | ≥ 0.95 |
| `measurement_method` | string | Method used to measure Poisson's ratio | Must not be "Derived" |
| `is_independent_measurement` | boolean | True if Poisson's ratio is an independent measurement | False if derived |
| `source` | string | Original data source (MP or NIST) | Enum: ["Materials Project", "NIST MDR"] |
| `alloy_series` | string | Derived alloy series (e.g., "2xxx", "6xxx") | Inferred from composition |

### 2. ILR_AlloyRecord
Represents the AlloyRecord after Isometric Log-Ratio transformation.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `alloy_id` | string | Unique identifier | Primary Key |
| `poissons_ratio` | float | Target variable | Non-null |
| `ilr_1` | float | ILR-transformed feature 1 | Non-null |
| `ilr_2` | float | ILR-transformed feature 2 | Non-null |
| `ilr_3` | float | ILR-transformed feature 3 | Non-null |
| `ilr_4` | float | ILR-transformed feature 4 | Non-null |
| `alloy_series` | string | Derived alloy series | Categorical |

### 3. ModelMetrics
Stores the evaluation results of the Random Forest model.

| Field | Type | Description |
| :--- | :--- | :--- |
| `cv_mae` | float | Mean Absolute Error from 5-fold cross-validation |
| `test_mae` | float | Mean Absolute Error on the held-out test set |
| `feature_importance_cu` | float | Permutation importance score for Copper (ILR space) |
| `feature_importance_mg` | float | Permutation importance score for Magnesium (ILR space) |
| `feature_importance_si` | float | Permutation importance score for Silicon (ILR space) |
| `feature_importance_zn` | float | Permutation importance score for Zinc (ILR space) |
| `feature_importance_mn` | float | Permutation importance score for Manganese (ILR space) |
| `collinearity_flag` | boolean | True if any VIF > 5 (Diagnostic only) |

### 4. CollinearityDiagnostic
Stores the Variance Inflation Factor (VIF) for raw predictors.

| Field | Type | Description |
| :--- | :--- | :--- |
| `element` | string | Alloying element name |
| `vif_score` | float | Variance Inflation Factor |
| `flagged` | boolean | True if VIF > 5 (Diagnostic only) |

## Data Flow

1.  **Raw Data**: Downloaded from MP and NIST into `data/raw/`.
2.  **Cleaned Data**: Filtered and normalized into `data/processed/alloys_clean.parquet` (AlloyRecord schema).
3.  **Transformed Data**: ILR applied to create `data/processed/alloys_ilr.parquet` (ILR_AlloyRecord schema).
4.  **Model Output**: Metrics saved to `data/processed/model_metrics.json` (ModelMetrics schema).
5.  **Diagnostics**: VIF results saved to `data/processed/collinearity_diagnostic.json` (CollinearityDiagnostic schema).
