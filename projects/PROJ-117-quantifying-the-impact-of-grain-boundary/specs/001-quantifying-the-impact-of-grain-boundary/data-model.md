# Data Model: Quantifying the Association of Grain Boundary Character with Diffusivity

## Entity Definitions

### 1. GrainBoundaryRecord
Represents a single atomistic simulation record used for training.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `record_id` | string | Unique identifier (UUID) | Required, Unique |
| `material_composition` | string | Chemical formula (e.g., "Fe", "Cu") | Required |
| `temperature` | float | Temperature in Kelvin | Required, > 0 |
| `misorientation_angle` | float | Angle in degrees | Required, [0, 180] |
| `boundary_plane_normal` | array | Miller indices [h, k, l] (integers) | Required, length 3 |
| `sigma_value` | integer | Σ value (CSL) | Required, > 0 |
| `diffusivity` | float | Diffusivity (m² s⁻¹) | Required, > 0 |
| `source` | string | Origin (e.g., "MaterialsProject", "OpenKIM") | Required |
| `checksum` | string | SHA-256 of raw source line | Required |
| `boundary_width` | float | Geometric descriptor (nm) | Required (parsed) |
| `excess_volume` | float | Geometric descriptor (Å³/atom) | Required (parsed) |
| `simulation_method` | string | Method used (DFT, MD, KMC) | Required (to control bias) |
| `potential_id` | string | Identifier for the interatomic potential | Required (if available) |

### 2. ModelArtifact
Represents the trained XGBoost model and its metadata.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `model_id` | string | Unique identifier | Required |
| `hyperparameters` | object | JSON dict of XGBoost params | Required |
| `feature_importance` | array | List of (feature, score) tuples | Required |
| `performance_metrics` | object | R², RMSE, MAPE on test set | Required |
| `training_timestamp` | string | ISO 8601 timestamp | Required |
| `random_seed` | integer | Seed used for reproducibility | Required |
| `final_feature_set` | array | List of features used after collinearity filtering | Required |

### 3. ValidationReport
Represents the statistical validation output.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `report_id` | string | Unique identifier | Required |
| `k_fold_metrics` | array | List of metrics per fold (R², RMSE) | Required |
| `bias_test_results` | object | Intercept, Slope, P-values | Required |
| `fwer_adjusted_alpha` | float | Adjusted significance threshold | Required |
| `is_bias_detected` | boolean | True if bias test fails | Required |
| `mi_scores` | object | Mutual Information scores for collinearity | Required |
| `threshold_sweep_results` | object | Results for R² {0.65, 0.70, 0.75} | Required |

## Data Flow

1.  **Ingestion**: Raw data downloaded from APIs → `data/raw/` (JSON/CSV/Parquet).
2.  **Geometry Parsing**: Parse POSCAR/CIF files → `boundary_width`, `excess_volume`.
3.  **Validation**: Check for required fields. Exclude incomplete records.
    *   *If n < 500*: **HALT**.
4.  **Feature Engineering**:
    *   Convert `boundary_plane_normal` to Miller indices (if not already).
    *   Compute Rodrigues vectors for misorientation (internal representation).
    *   Tag `simulation_method` and `potential_id`.
5.  **Collinearity Diagnostics**: Calculate MI between misorientation and Σ value.
6.  **Feature Selection**: If MI > 0.8, apply L1 regularization or RFE to reduce redundancy.
7.  **Splitting**: 70/15/15 split (Train/Val/Test) with stratification if applicable (though regression stratification is less common, random split with fixed seed is used).
8.  **Training**: XGBoost with `RandomizedSearchCV` (k=5 CV).
9.  **Validation**: Bias test, SHAP analysis, Threshold Sweep.
10. **Output**: `ModelArtifact` and `ValidationReport` stored in `artifacts/`.