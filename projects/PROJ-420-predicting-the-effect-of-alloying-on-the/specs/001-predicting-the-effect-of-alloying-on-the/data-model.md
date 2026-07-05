# Data Model: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Entities

### AlloyRecord
Represents a single aluminum alloy entry after cleaning and normalization.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier from source | Unique, Non-null |
| `source` | string | "Materials Project" or "NIST" | Enum |
| `poissons_ratio` | float | Poisson's ratio (dimensionless) | Range: 0.0 - 0.5 |
| `youngs_modulus_gpa` | float | Young's modulus in GPa | > 0 |
| `shear_modulus_gpa` | float | Shear modulus in GPa | > 0 (Required for FR-009 verification) |
| `measurement_method` | string | Method used (e.g., "Ultrasonic") | Required for FR-009 verification |
| `composition_cu` | float | Atomic fraction of Cu | 0.0 - 1.0 |
| `composition_mg` | float | Atomic fraction of Mg | 0.0 - 1.0 |
| `composition_si` | float | Atomic fraction of Si | 0.0 - 1.0 |
| `composition_zn` | float | Atomic fraction of Zn | 0.0 - 1.0 |
| `composition_mn` | float | Atomic fraction of Mn | 0.0 - 1.0 |
| `composition_al` | float | Calculated atomic fraction of Al | 1.0 - sum(others) |
| `is_independent_measurement` | boolean | True if Poisson's ratio is not derived from E | Required (derived from G and method) |
| `raw_vif_cu` | float | VIF for Cu in raw space | Diagnostic |
| `raw_vif_mg` | float | VIF for Mg in raw space | Diagnostic |
| `raw_vif_si` | float | VIF for Si in raw space | Diagnostic |
| `raw_vif_zn` | float | VIF for Zn in raw space | Diagnostic |
| `raw_vif_mn` | float | VIF for Mn in raw space | Diagnostic |

### ModelMetrics
Aggregated performance metrics from the training pipeline.

| Field | Type | Description |
| :--- | :--- | :--- |
| `cv_mae` | float | Mean Absolute Error from 5-fold CV |
| `test_mae` | float | Mean Absolute Error on held-out test set |
| `n_train` | int | Number of training samples |
| `n_test` | int | Number of test samples |
| `feature_importance` | object | Map of element name to importance score |
| `null_model_threshold` | float | 95th percentile of null importance scores |
| `is_associational` | boolean | True (always) |
| `high_vif_flag` | boolean | True if any VIF > 5 |
| `power_analysis_log` | string | Log of the power analysis (MDES) |
| `basis_sensitivity_flag` | boolean | True if rankings changed with alternative basis |

## Data Flow

1. **Raw Download**: `raw_data.csv` (Source: MP/NIST)
2. **Filtering**: `filtered_data.csv` (Monolithic, complete, unit-normalized, G present)
3. **Feature Engineering**: `processed_data.parquet` (ILR transformed, VIF calculated)
4. **Model Output**: `model_results.json` (Metrics, importance, null thresholds)