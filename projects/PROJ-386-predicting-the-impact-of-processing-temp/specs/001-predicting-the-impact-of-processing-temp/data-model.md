# Data Model: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in `data/` and processed into `data/processed/`. The model expects a specific schema for training and validation.

## Entity Definitions

### AlloySample (Core Entity)

Represents a single experimental entry for a rolled aluminum alloy.

| Field | Type | Description | Source/Origin |
| :--- | :--- | :--- | :--- |
| `sample_id` | `str` | Unique identifier for the sample. | Generated (UUID) or Source ID |
| `alloy_series` | `str` | Series classification (e.g., "1xxx", "6xxx"). | Derived from composition |
| `temperature` | `float` | Rolling temperature in °C. | Source Dataset |
| `grain_size` | `float` | Measured grain size in µm. | Source Dataset |
| `mg_wt` | `float` | Magnesium weight percentage. | Source Dataset (or 0 if missing) |
| `si_wt` | `float` | Silicon weight percentage. | Source Dataset (or 0 if missing) |
| `cu_wt` | `float` | Copper weight percentage. | Source Dataset (or 0 if missing) |
| `zn_wt` | `float` | Zinc weight percentage. | Source Dataset (or 0 if missing) |
| `other_wt` | `float` | Sum of other elements (Fe, Mn, etc.). | Calculated |
| `source` | `str` | Original dataset source (e.g., "NOMAD"). | Metadata |

### InteractionFeature

Derived features created during preprocessing.

| Field | Type | Description | Formula |
| :--- | :--- | :--- | :--- |
| `temp_mg_int` | `float` | Interaction of Temp and Mg. | `temperature * mg_wt` |
| `temp_si_int` | `float` | Interaction of Temp and Si. | `temperature * si_wt` |
| `temp_cu_int` | `float` | Interaction of Temp and Cu. | `temperature * cu_wt` |
| `temp_zn_int` | `float` | Interaction of Temp and Zn. | `temperature * zn_wt` |

### ModelArtifact

Serialized output of the training process.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | `str` | "LinearRegression" or "RandomForest" |
| `hyperparams` | `dict` | Grid search best params (e.g., `{'n_estimators': 100}`) |
| `metrics` | `dict` | `{'r2': float, 'mae': float, 'rmse': float}` |
| `feature_importance` | `dict` | Map of feature name to importance score (RF) or coefficient (Linear) |
| `collinearity_flags` | `list` | List of feature pairs with correlation > 0.8 |
| `timestamp` | `str` | ISO 8601 timestamp of training |
| `seed` | `int` | Random seed used |

## Data Flow

1.  **Raw Ingestion**: Download from verified URL -> `data/raw/nomad_structure_hf.csv`.
2.  **Schema Validation**: Check for `temperature`, `grain_size`, `mg`, `si`.
    *   *Fail*: Exit 1.
    *   *Pass*: Proceed.
3.  **Preprocessing**:
    *   Filter rows with missing critical values.
    *   Compute `alloy_series` from composition.
    *   Generate `InteractionFeature` columns.
    *   **Residualization**: Regress `grain_size` against `alloy_series` and `composition` to compute residuals (stored in a temporary column `residual_grain_size`).
    *   Normalize numeric features (StandardScaler).
    *   Output: `data/processed/engineered_data.csv` (contains original features + residuals + interactions).
4.  **Modeling**:
 * Split: [deferred] Train, [deferred] Test (**Stratified Group K-Fold** with groups=`alloy_series`).
    *   Train Linear (on residuals) -> Output `artifacts/baseline_model.pkl`.
    *   Train RF (on residuals) -> Output `artifacts/rf_model.pkl`.
5.  **Analysis**:
    *   Generate `artifacts/collinearity_report.json`.
    *   Generate `artifacts/sensitivity_analysis.csv`.
    *   Generate `artifacts/final_metrics.json`.

## Constraints

*   **Missing Data**: Rows with missing `temperature` or `grain_size` are dropped. Rows with missing composition elements (e.g., no Mg listed) are imputed as 0.0 (assuming trace amounts) or dropped if the element is critical for the interaction term being tested.
*   **Normalization**: All continuous predictors are standardized (mean=0, std=1) before modeling to ensure coefficient comparability.
*   **Stratification**: Train/Test split must preserve the distribution of `alloy_series` to prevent leakage of specific alloy behaviors.
*   **Versioning**: Every file in `data/raw/` and `data/processed/` is checksummed using `sha256sum`. The hashes are stored in `state/projects/PROJ-386...yaml` under `artifact_hashes` with keys like `data_raw_nomad_structure_hf.csv` and `data_processed_engineered_data.csv`.