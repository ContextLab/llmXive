# Data Model: Quantifying the Influence of Topological Defects on 2D Material Properties

## Overview

This document defines the data structures used throughout the pipeline, ensuring consistency between the acquisition, processing, and modeling stages. The model is designed to be extensible and strictly typed to support automated validation.

## Entity Definitions

### 1. DefectEntry
Represents a single record of a defective 2D material structure.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | str | Unique identifier (UUID or hash). | Required, Unique |
| `material` | str | Material type (e.g., "graphene", "MoS2"). | Required |
| `defect_type` | str | Type of defect (e.g., "dislocation", "grain_boundary", "vacancy"). | Required |
| `defect_density` | float | Fraction of atoms affected. | ≥ 0, ≤ 0.1 |
| `conductivity` | float | Electronic conductivity (S/m). | > 0 |
| `youngs_modulus` | float | Young's modulus (GPa). | > 0 |
| `fracture_energy` | float | Fracture energy (J/m²). | > 0 |
| `synthesis_method` | str | Method used to create the defect (optional). | Optional |
| `grain_size` | float | Grain size (nm) (optional). | Optional |
| `source` | str | Source of the data (e.g., "MP_API", "Synthetic", "2022_CSV"). | Required |
| `exclusion_flag` | str | Flag for missing data. | `[MISSING: requires exclusion]` or null |

### 2. MaterialProperty
Represents the normalized property values relative to pristine references.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `entry_id` | str | Reference to `DefectEntry.id`. | Required |
| `delta_conductivity` | float | Relative change (Δσ/σ₀). | Real number |
| `delta_youngs` | float | Relative change (ΔE/E₀). | Real number |
| `delta_fracture` | float | Relative change (Δσ_f/σ_f₀). | Real number |
| `pristine_conductivity` | float | Reference value σ₀. | > 0 |
| `pristine_youngs` | float | Reference value E₀. | > 0 |
| `pristine_fracture` | float | Reference value σ_f₀. | > 0 |

### 3. ModelOutput
Represents the results of the Random Forest regression and statistical tests.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `model_id` | str | Identifier for the model run. | Required |
| `target_property` | str | The property modeled (e.g., "delta_conductivity"). | Required |
| `r_squared` | float | R² score on test set. | [-1, 1] |
| `mape` | float | Mean Absolute Percentage Error. | ≥ 0 |
| `cv_std` | float | Standard deviation of R² across 5 folds. | ≥ 0 |
| `feature_importance` | dict | Map of feature name to importance score. | Required |
| `p_values` | dict | Map of feature name to p-value (from permutation). | [0, 1] |
| `fdr_adjusted` | dict | Map of feature name to BH-adjusted p-value. | [0, 1] |
| `collinearity_flags` | list | List of features with VIF > 5. | Optional |

## Data Flow

1.  **Acquisition**: `DefectEntry` raw data is ingested from API/CSV/Synthetic.
2.  **Validation**: Missing values flagged with `[MISSING: requires exclusion]`; entries with `defect_density` ≤ 0 or NaN excluded.
3.  **Normalization**: `MaterialProperty` created by dividing raw properties by pristine references (from MP API).
4.  **Modeling**: `ModelOutput` generated from `MaterialProperty` features.
5.  **Reporting**: Final results aggregated in `Validation_Report.json`.