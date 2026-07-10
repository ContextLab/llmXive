# Data Model: Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

## 1. Overview

This document defines the data structures for the alloy oxidation prediction pipeline. It ensures separation between raw composition, derived thermodynamic features, and microstructural annotations, adhering to Constitution Principle VI.

## 2. Entity Definitions

### 2.1 AlloySample
Represents a single material entry.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | Unique identifier (UUID or hash) | Required, Unique |
| `composition` | dict | Elemental weight percentages | Keys: Ni, Cr, Al, Co, Ti, etc. Values: float (0.0-100.0). Sum ≈ 100. |
| `thermo_descriptors` | dict | Calculated thermodynamic properties | Keys: `enthalpy_Al2O3`, `enthalpy_Cr2O3`, `avg_atomic_radius`, etc. |
| `microstructure` | dict | Optional microstructural features | Keys: `grain_size_um`, `precipitate_vol_frac`. May be null/empty. |
| `observed_weight_gain` | float | Measured oxidation weight gain (mg/cm²) | Required for training. Must be > 0. |

### 2.2 PredictionResult
Output of the model inference.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | Reference to input sample | Required |
| `predicted_weight_gain` | float | Model prediction | Required |
| `confidence_interval` | tuple | (lower, upper) bounds | Optional (if GP or RF quantile) |
| `model_type` | string | Name of the model used | e.g., "RandomForest" |
| `feature_contributions` | dict | SHAP values or similar | Keys: feature names, Values: float |
| `warning_flags` | list | List of string warnings | e.g., "UNKNOWN_ELEMENT", "LOW_ALUMINUM" |

### 2.3 GapAnalysisReport
Summary of the comparative study.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `composition_only_rmse` | float | RMSE of model without microstructure | Required |
| `augmented_rmse` | float | RMSE of model with microstructure | Required (if n ≥ 30) |
| `error_reduction_pct` | float | Percentage reduction in error | Required (if n ≥ 30) |
| `microstructural_sample_count` | int | Number of samples with microstructure | Required |
| `sensitive_samples` | list | IDs of samples with high residuals | List of strings |
| `status` | string | "CONCLUSIVE" or "INCONCLUSIVE" | Depends on sample count |
| `calculated_power` | float | Statistical power for the effect size | Required (even if inconclusive) |

## 3. Data Flow

1.  **Raw Data**: Downloaded/Generated CSV/Parquet.
2.  **Processed Data**: `data/processed/feature_matrix.parquet` (Composition + Thermo + Microstructure + Target).
3.  **Model Artifacts**: `data/processed/model_best.joblib`, `data/processed/shap_values.npy`.
4.  **Reports**: `data/processed/gap_analysis_report.json`, `data/processed/predictions.csv`.

## 4. Validation Rules

- **Composition Sum**: Sum of elemental wt% must be within 99.0-101.0.
- **Zero Variance**: Features with 0 variance are excluded before training.
- **Missing Data**: Rows with missing `observed_weight_gain` or essential composition elements (Ni, Cr, Al) are excluded.
- **Unknown Elements**: Elements not in the training set > 0.5 wt% trigger exclusion/warning.
- **Data Gap**: If no real data is found, a `data_gap_report.txt` is generated instead of standard results.
