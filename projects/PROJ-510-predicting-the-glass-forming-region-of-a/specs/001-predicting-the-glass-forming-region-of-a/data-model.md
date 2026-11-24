# Data Model: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Entity Definitions

### 1. AlloyRecord
Represents a single ternary alloy and its associated thermodynamic features.
- **Storage**: `data/processed/processed_alloys.csv`
- **Fields**:
    - `composition` (string): e.g., "Zr0.5Cu0.3Al0.2"
    - `critical_cooling_rate` (float): Target variable in K/s.
    - `mixing_enthalpy` (float): Computed $\Delta H_{mix}$ (eV/atom).
    - `atomic_size_difference` (float): Computed $\delta$ (dimensionless).
    - `electronegativity_variance` (float): Computed $\sigma_{\chi}$ (dimensionless).
    - `source_label` (string): Original experimental label.

### 2. ModelMetrics
Captures the performance of the regressor.
- **Storage**: `data/models/cv_metrics.json`
- **Fields**:
    - `fold_scores` (list[float]): RMSE for each of the 5 folds.
    - `mean_rmse` (float): Average RMSE across folds.
 - `test_rmse` (float): RMSE on the [deferred] held-out test set.
    - `dummy_rmse` (float): RMSE of the mean-predictor baseline.
    - `p_value` (float): Significance of RF vs Dummy.

### 3. FeatureImportance
Ranked contribution of descriptors.
- **Storage**: `data/reports/feature_importance.csv`
- **Fields**:
    - `feature_name` (string): Descriptor name.
    - `importance_mean` (float): Mean decrease in score.
    - `p_value` (float): Significance against shuffled baseline.

### 4. SensitivityReport
Performance stability across binary thresholds.
- **Storage**: `data/reports/sensitivity_report.json`
- **Fields**:
    - `thresholds` (list[int]): `[50, 100, 150]`
    - `f1_scores` (list[float]): F1-score for each threshold.
    - `stability_status` (string): "PASS" if F1 variance is low.

### 5. ModelOutput
Registry of all final research artifacts and their integrity hashes.
- **Storage**: `data/models/model_output.json`
- **Fields**:
    - `model_path` (string): Path to the serialized .pkl model.
    - `cv_metrics_path` (string): Path to the metrics JSON.
    - `feature_importance_path` (string): Path to the importance CSV.
    - `sensitivity_report_path` (string): Path to the sensitivity JSON.
    - `model_sha256` (string): Checksum of the model file.

## Contract Summary
| Artifact | Schema | Key Constraint |
|-----------|--------|-----------------|
| `processed_alloys.csv` | `processed_alloys.schema.yaml` | `row_count >= 500` |
| `cv_metrics.json` | `metrics.schema.yaml` | `fold_scores` length == 5 |
| `feature_importance.csv`| `feature_importance.schema.yaml` | All 3 descriptors present |
| `sensitivity_report.json`| `sensitivity.schema.yaml` | Thresholds == `[50, 100, 150]` |