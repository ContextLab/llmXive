# Data Model: Predicting the Impact of Composition on the Density of Metallic Glasses

## 1. Overview
This document defines the data structures, schemas, and transformations used in the metallic glass density prediction pipeline. The model adheres to the **Single Source of Truth** principle: all derived data is traceable to the raw input.

## 2. Entity Definitions

### 2.1 MetallicGlassRecord
Represents a single alloy entry in the dataset.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | String | Unique identifier (UUID or hash of composition) | Generated |
| `composition` | Dict[Str, Float] | Map of Element Symbol -> Mass Fraction | Keys are IUPAC symbols; Values sum to 1.0 (±0.001) |
| `bulk_density` | Float | Measured bulk density (g/cm³) | > 0.0 |
| `dominant_element` | Str | Element with highest mass fraction | Derived (Used for Group K-Fold) |
| `baseline_density` | Float | Linear mixing rule prediction (g/cm³) | Derived |
| `residual_density` | Float | Actual - Baseline (g/cm³) | Derived |
| `mean_atomic_mass` | Float | Weighted mean atomic mass (g/mol) | Derived |
| `mean_atomic_radius` | Float | Weighted mean atomic radius (pm) | Derived (Atomic Fractions) |
| `radius_mismatch` | Float | Std dev of atomic radii | Derived |
| `packing_efficiency` | Float | Non-linear packing proxy | Derived (Guard: $\ge 0.0$) |
| `electronegativity_var`| Float | Variance of electronegativity | Derived |

### 2.2 PredictionModel
Represents the trained regressor state.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `algorithm` | Str | "LightGBM" |
| `hyperparameters` | Dict | Model config (num_leaves, learning_rate, etc.) |
| `feature_importance` | Dict[Str, Float] | Map of feature name -> importance score |
| `training_metrics` | Dict | MAE, R², RMSE on test set |

### 2.3 AnalysisReport
The final output artifact.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `metrics` | Dict | Final MAE, R², Sensitivity Results |
| `visualizations` | List[Str] | Paths to generated plot files (PNG/HTML) |
| `interpretability` | Dict | SHAP summary data, Partial Dependence plots |
| `status` | Str | "SUCCESS" or "VALIDATION_MODE" |
| `baseline_comparison` | Dict | Metrics comparing Full Model vs Mass-Only Model |

## 3. Data Flow & Transformations

1.  **Ingestion**:
    -   Input: Raw CSV from Zenodo/Materials Cloud (or Synthetic Generator).
    -   Output: `data/raw_data.csv`
    -   Transformation: None (Raw preservation).

2.  **Preprocessing**:
    -   Input: `raw_data.csv`
    -   Output: `data/clean_data.csv`
    -   Transformation:
        -   Filter rows with missing density.
        -   Normalize element symbols (e.g., "Fe" vs "IRON").
        -   Validate mass fraction sum = 1.0.

3.  **Feature Engineering**:
    -   Input: `clean_data.csv`
    -   Output: `data/derived_data.csv` (internal to pipeline)
    -   Transformation:
        -   Calculate `baseline_density`.
        -   Calculate `residual_density`.
        -   Convert mass fractions to atomic fractions.
        -   Compute `mean_atomic_mass`, `mean_atomic_radius`, `radius_mismatch`, `packing_efficiency`, `electronegativity_var`.

4.  **Modeling**:
    -   Input: `derived_data.csv`
    -   Output: `models/model.pkl`, `reports/metrics.json`
    -   Transformation:
        -   **Group K-Fold Split** (Dominant Element as group).
        -   LightGBM Training on `residual_density`.
        -   Prediction and Error Calculation.
        -   **Mass-Only Baseline Training** (Linear Regression on `mean_atomic_mass`).
        -   Comparison of Full Model vs Mass-Only Model.

5.  **Reporting**:
    -   Input: `model.pkl`, `derived_data.csv` (test split), `reports/metrics.json`
    -   Output: `reports/analysis_report.html`
    -   Transformation:
        -   SHAP Analysis.
        -   Partial Dependence Plot Generation.
        -   Sensitivity Analysis (Noise injection).
        -   Plot Generation.

## 4. Constraints & Validation Rules

-   **Mass Fraction Sum**: $\sum w_i \in [0.999, 1.001]$.
-   **Density**: Must be positive.
-   **Element Symbols**: Must be valid IUPAC symbols (1 or 2 chars).
-   **Packing Efficiency**: If $\sigma_r = 0$, $PE = 1.0$.
-   **Data Integrity**: No PII; Checksums recorded for all raw files.
-   **SSoT Designation**: `models/model.pkl` is the source of truth for the model state. `reports/metrics.json` is the source of truth for the reported metrics in the paper.