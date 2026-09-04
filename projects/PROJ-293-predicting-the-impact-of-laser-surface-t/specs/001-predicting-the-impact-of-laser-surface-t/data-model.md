# Data Model: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## 1. Entity Definitions

### 1.1 LSTRecord
Represents a single experimental observation.
*   **Source**: Aggregated from OpenML, HuggingFace, Literature.
*   **Cardinality**: 1:N (One study can produce many records).

**Attributes**:
| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `record_id` | string | Unique identifier (hash of source + row) | PK |
| `pulse_duration` | float | Laser pulse duration (ns, µs, etc.) | Required, >0 |
| `power` | float | Laser power (W) | Required, >0 |
| `scanning_speed` | float | Scanning speed (mm/s) | Required, >0 |
| `pattern_geometry` | string | Geometry type (e.g., "dimple", "line", "grid") | Required, categorical |
| `hardness` | float | Material hardness (HV) | Required, >0 |
| `elastic_modulus` | float | Elastic modulus (GPa) | Required, >0 |
| `wear_rate` | float | Raw wear rate (mm³/Nm or similar) | Required |
| `contact_load` | float | Contact load (N) | Optional (nullable) |
| `sliding_speed` | float | Sliding speed (m/s) | Optional (nullable) |
| `material_class` | string | Material category (e.g., "Steel", "Aluminum") | Required |
| `normalization_method` | string | "archard" or "raw" | Computed (derived from load/speed presence) |
| `specific_wear_coef` | float | Calculated K value (Archard) | Computed (nullable if raw) |
| `is_valid_for_normalized_analysis` | boolean | True if `contact_load` and `sliding_speed` are present | Computed |

### 1.2 ModelPerformance
Stores evaluation metrics for a specific model configuration.
*   **Source**: `train.py` output.

**Attributes**:
| Field | Type | Description |
| :--- | :--- | :--- |
| `model_id` | string | Unique hash of model config |
| `algorithm` | string | "Linear", "RF", "GB" |
| `hyperparameters` | json | Dict of params (e.g., `{"n_estimators": 100}`) |
| `cv_r2_mean` | float | Mean R² from cross-validation |
| `cv_r2_std` | float | Std dev of R² |
| `test_r2` | float | R² on held-out test set |
| `test_mae` | float | Mean Absolute Error |
| `test_rmse` | float | Root Mean Squared Error |
| `loo_r2_ratio` | float | `test_R²_loo / test_R²_standard` (if LOMO performed) |
| `transferability_failure` | boolean | True if `loo_r2_ratio` < 0.8 |
| `loo_class_sample_sizes` | json | Map of class name to sample size (for small sample check) |

### 1.3 FeatureImportance
Mapping of features to their contribution.
*   **Source**: `interpret.py` (SHAP + Conditional Permutation).

**Attributes**:
| Field | Type | Description |
| :--- | :--- | :--- |
| `feature_name` | string | Feature name |
| `mean_abs_shap` | float | Mean absolute SHAP value |
| `p_value_perm` | float | P-value from conditional permutation test |
| `permutation_count` | integer | Actual number of permutations performed (e.g., 2000) |
| `rank` | integer | Rank by mean absolute SHAP |
| `vif_score` | float | Variance Inflation Factor (pre-filter) |
| `validation_status` | string | "validated", "associational_only", or "validation_target_unavailable" |

## 2. Data Flow

1.  **Raw Ingestion**: `data/raw/*.csv` -> `ingest.py` -> `data/processed/raw_merged.csv` (with source tags).
2.  **Pre-Check**: `raw_merged.csv` -> `ingest.py` (count `contact_load`/`sliding_speed`) -> `reports/pre_check.json`. **If normalized_count < 100, halt primary analysis.**
3.  **Cleaning**: `raw_merged.csv` -> `preprocess.py` (drop missing predictors, flag raw) -> `data/processed/cleaned.csv`.
4.  **Normalization**: `cleaned.csv` -> `preprocess.py` (Archard calc) -> `data/processed/normalized.csv`. **Exclude `contact_load` and `sliding_speed` from predictors if target is `K`.**
5.  **Feature Engineering**: `normalized.csv` -> `preprocess.py` (VIF, Scaling, Interactions) -> `data/processed/features_ready.csv`.
6.  **Modeling**: `features_ready.csv` -> `train.py` -> `models/` + `reports/model_performance.json`.
7.  **Interpretation**: `models/` + `features_ready.csv` -> `interpret.py` -> `reports/interpretation.html`.

## 3. Schema Constraints & Validation

*   **Missing Predictors**: Any row with `NULL` in `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, or `elastic_modulus` is **dropped** before model training.
*   **Missing Test Parameters**: Rows with missing `contact_load` or `sliding_speed` are **retained** with `normalization_method='raw'`.
*   **Material Class**: Must be a non-empty string.
*   **Normalization**: `normalization_method` must be either "archard" or "raw".
*   **VIF Filter**: Features with VIF > 5 are excluded from the final model input matrix for permutation tests.
*   **Circular Validation**: When `target` is `specific_wear_coef`, the features `contact_load` and `sliding_speed` are **excluded** from the feature matrix.
