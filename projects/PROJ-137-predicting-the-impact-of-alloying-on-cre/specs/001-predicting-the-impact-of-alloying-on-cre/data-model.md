# Data Model: Predicting the Impact of Alloying on Creep Resistance

## 1. Overview

This document defines the data structures, schemas, and transformation rules for the project. It ensures consistency between the data pipeline, model training, and evaluation phases.

## 2. Core Entities

### 2.1 AlloySample
Represents a single experimental data point.
*   **Attributes**:
    *   `alloy_id`: Unique identifier (string).
    *   `composition_str`: Raw composition string (e.g., "Ni-10Cr-5Al").
    *   `temperature`: Temperature in Kelvin (float).
    *   `stress`: Stress in MPa (float).
    *   `rupture_time`: Time to rupture in hours (float).
    *   `elemental_fractions`: Dictionary of element -> atomic fraction.
    *   `thermodynamic_features`: Dictionary of derived properties (mixing_enthalpy, radius_mismatch, etc.).
    *   `synthetic_interaction_signal`: (Optional, for synthetic data only) The injected interaction term used to validate signal detection.

### 2.2 ThermodynamicDescriptor
Represents calculated physical properties.
*   **Attributes**:
    *   `mixing_enthalpy`: Enthalpy of mixing (kJ/mol).
    *   `radius_mismatch`: Standard deviation of atomic radii.
    *   `valence_electron_concentration`: (Optional) VEC.

### 2.3 ModelPerformance
Represents evaluation metrics.
*   **Attributes**:
    *   `model_type`: "thermodynamic" or "composition_only".
    *   `r2_mean`: Mean R² from outer CV.
    *   `rmse_mean`: Mean RMSE from outer CV.
    *   `ci_lower`: Lower bound of 95% CI.
    *   `ci_upper`: Upper bound of 95% CI.
    *   `p_value`: (If applicable) P-value from Permutation Test.
    *   `power_status`: "sufficient" or "insufficient" based on MDES calculation.

## 3. Data Flow

1.  **Raw Input**: NIMS CSV or Synthetic Generator Output.
2.  **Preprocessing**:
    *   Parse composition.
    *   Compute thermodynamic descriptors (if available).
    *   Filter missing data.
    *   Handle duplicates (average rupture time).
3.  **Merged Dataset**: Intersection of valid composition and thermodynamic data.
4.  **Model Input**:
    *   **Thermodynamic Model**: `elemental_fractions` + `thermodynamic_features`.
    *   **Composition Model**: `elemental_fractions` only.
5.  **Output**: Metrics, SHAP plots, reports.

## 4. Schema Definitions

See `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for formal YAML schema definitions used for validation.

## 5. Constraints & Rules

*   **Missing Data**: Any row missing `temperature`, `stress`, `rupture_time`, or thermodynamic data (for the thermodynamic model) is excluded.
*   **Duplicates**: If multiple rows exist for the same alloy/conditions, `rupture_time` is averaged.
*   **Normalization**: Composition strings must be normalized (sorted, rounded) before lookup.
*   **Fair Comparison**: Both models must use the exact same row indices.
*   **Synthetic Signal**: For synthetic data, the `synthetic_interaction_signal` must be non-zero to ensure the "Thermodynamic" model has a learnable advantage.
