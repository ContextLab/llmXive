# Data Model: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

## Overview
Three core data entities flow through the pipeline. Each entity has a JSON schema stored under `contracts/`. The schemas are used by the test suite to validate artifact conformity.

## Entity Definitions

### 1. TreatmentRecord
Represents a single experimental observation after ingestion and preprocessing.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `treatment_type` | string | Canonical treatment label (e.g., `"Oxygen Plasma"`). | Yes |
| `plasma_power_w` | number | Plasma power in **watts** (SI). | Yes |
| `exposure_time_s` | number | Exposure time in **seconds** (SI). | Yes |
| `chemical_concentration_pct` | number | Chemical concentration as a **percentage** (0‑100). | Yes |
| `polymer_surface_energy` | number | Surface energy of the polymer in **mJ / m²**. | Yes |
| `substrate_roughness_nm` | number | Roughness of substrate in **nanometers**. | Yes |
| `adhesion_strength_mj_m2` | number | Measured adhesion strength in **mJ / m²** (target variable). | Yes |
| `pair_id` | string | Identifier for the polymer‑substrate pair (e.g., `"PE‑Glass"`). | Yes |
| `source` | string | Identifier of the originating dataset (e.g., `"synthetic"`). | Yes |

### 2. ModelArtifact
Encapsulates a trained regression model and its metadata.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `model_type` | string | `"RandomForest"`, `"GradientBoosting"` or `"LinearRegression"`. | Yes |
| `hyperparameters` | object | JSON dictionary of the hyper‑parameter values used. | Yes |
| `validation_r2` | number | R² on the validation split. | Yes |
| `validation_rmse` | number | RMSE on the validation split. | Yes |
| `test_r2` | number | R² on the held‑out test set. | Yes |
| `test_rmse` | number | RMSE on the test set. | Yes |
| `test_mae` | number | MAE on the test set. | Yes |
| `artifact_path` | string | Relative path to the serialized model file (e.g., `"models/rf.pkl"`). | Yes |
| `training_timestamp` | string | ISO‑8601 timestamp of training completion. | Yes |

### 3. AnalysisResult
Aggregates the final scientific findings.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `best_model_type` | string | Model type selected as best (matches `ModelArtifact.model_type`). | Yes |
| `final_r2` | number | Test‑set R² of the best model. | Yes |
| `r2_ci_95` | array[number] | Two‑element list `[lower, upper]` for the 95 % bootstrapped confidence interval. | Yes |
| `final_rmse` | number | Test‑set RMSE of the best model. | Yes |
| `final_mae` | number | Test‑set MAE of the best model. | Yes |
| `permutation_p_value` | number | Empirical p‑value from the 1 000‑shuffle permutation test. | Yes |
| `top_predictors` | array[string] | Ordered list of the three most important features by mean absolute SHAP value. | Yes |
| `per_predictor_significance` | object | Mapping `feature_name → p_value` for linear‑model coefficients where applicable. | Yes |
| `visualizations` | object | Mapping `name → relative_path` for the four required PNG files (`predicted_vs_actual`, `residual_histogram`, `shap_summary`, `parameter_response_curves`). | Yes |
| `run_timestamp` | string | ISO‑8601 timestamp of the complete analysis run. | Yes |
| `checksum_report` | object | SHA‑256 checksums for all output files (report JSON, PNGs, model artifact). | Yes |

## Schema Files
The concrete YAML schemas are provided in the `contracts/` directory:

- `contracts/treatment_record.schema.yaml`  
- `contracts/model_artifact.schema.yaml`  
- `contracts/analysis_result.schema.yaml`

These schemas are used by `pytest` contract tests to ensure every artifact conforms to the defined structure.

---
