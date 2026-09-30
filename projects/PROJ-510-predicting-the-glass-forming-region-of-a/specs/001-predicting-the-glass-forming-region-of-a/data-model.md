# Data Model: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Entity Definitions

### 1. AlloyRecord
Represents a single ternary alloy entry after feature engineering.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `alloy_id` | string | Unique identifier from BMG dataset | Raw Data (BMG) |
| `elements` | string | Comma-separated element symbols (e.g., "Fe,Cr,Ni") | Raw Data (BMG) |
| `compositions` | array(float) | Atomic fractions [c1, c2, c3] | Raw Data (BMG) |
| `critical_cooling_rate` | float | Target variable (K/s) | Raw Data (BMG) |
| `mixing_enthalpy` | float | $\Delta H_{mix}$ (kJ/mol) | Derived (mendeleev) |
| `atomic_size_mismatch` | float | $\delta$ (dimensionless) | Derived (mendeleev) |
| `electronegativity_variance` | float | $\Delta \chi$ (dimensionless) | Derived (mendeleev) |
| `source_label` | string | Label from dataset (e.g., "glass", "crystal") | Raw Data (BMG) |

### 2. ModelMetrics
Aggregated performance metrics from the training and validation process.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `mean_cv_rmse` | float | Mean RMSE from 5-fold CV |
| `cv_rmse_std` | float | Standard deviation of fold RMSEs |
| `test_rmse` | float | RMSE on held-out test set |
| `dummy_rmse` | float | RMSE of dummy baseline |
| `p_value_baseline` | float | **p-value from two-sided t-test** against dummy (SC-002) |
| `feature_importance` | object | Map of feature name to importance score |
| `feature_p_values` | object | Map of feature name to permutation p-value |
| `final_dataset_size` | integer | **Count of valid entries after filtering (SC-001)** |
| `valid_entry_count` | integer | **Redundant check for SC-001** |

### 3. SensitivityReport
Results of the threshold sensitivity analysis.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `thresholds` | array(float) | **Must be exactly [50, 100, 150]** (K/s) |
| `rmse_at_thresholds` | array(float) | RMSE corresponding to each threshold |
| `rmse_variance` | float | **Variance of RMSE across thresholds** (SC-003) |
| `collinearity_flags` | array(object) | List of flagged collinear pairs and correlation coefficients |

## Data Flow

1.  **Ingestion**: Raw BMG CSV -> `data/raw/bmg_targets.csv`
2.  **Filtering**: Raw CSV -> `data/logs/exclusion_log.txt` + `data/processed/processed_alloys.csv`
3.  **Modeling**: Processed CSV -> `data/models/random_forest_model.pkl` + `data/models/cv_metrics.json`
4.  **Analysis**: Model + Processed CSV -> `data/models/sensitivity_report.json`

## Constraints

- **Missing Values**: Rows with missing `critical_cooling_rate` or elemental data are excluded.
- **Zero Enthalpy**: Valid numeric value; not an error.
- **Collinearity**: If correlation > 0.8, the model is re-run excluding one feature, and the result is flagged.
- **Associational**: All findings must be framed as associations, not causation.
- **Random State**: All splits and sampling MUST use `random_state=42`.
- **Thresholds**: Sensitivity analysis MUST use thresholds {50, 100, 150} K/s.
- **T-Test**: `p_value_baseline` MUST be calculated via a two-sided t-test.
- **Dataset Size**: `final_dataset_size` MUST be >= 500 for the pipeline to succeed.