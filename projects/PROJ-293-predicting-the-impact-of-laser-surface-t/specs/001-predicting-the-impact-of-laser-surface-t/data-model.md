# Data Model: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## 1. Canonical Schema

The system operates on a canonical schema derived from the spec's `LSTRecord` entity. All source data is mapped to this schema during ingestion.

| Field Name | Type | Description | Source Mapping Logic |
| :--- | :--- | :--- | :--- |
| `pulse_duration` | float | Laser pulse duration (µs) | Map `pulse_duration`, `pulse_width`, `duration` |
| `power` | float | Laser power (W) | Map `power`, `laser_power`, `avg_power` |
| `scanning_speed` | float | Scanning speed (mm/s) | Map `scanning_speed`, `scan_speed`, `velocity` |
| `pattern_geometry` | string | Texturing pattern (e.g., "grid", "dot") | Map `pattern`, `geometry`, `shape` |
| `hardness` | float | Material hardness (HV) | Map `hardness`, `hv`, `material_hardness` |
| `elastic_modulus` | float | Elastic modulus (GPa) | Map `elastic_modulus`, `youngs_modulus`, `E` |
| `wear_rate` | float | Raw wear rate (mm³/Nm or mg) | Map `wear_rate`, `wear`, `volume_loss` |
| `contact_load` | float | Contact load (N) | Map `load`, `force`, `normal_load` (Optional) |
| `sliding_speed` | float | Sliding speed (m/s) | Map `sliding_speed`, `velocity`, `speed` (Optional) |
| `density` | float | Material density (g/cm³) | Map `density`, `rho` (Optional) |
| `material_class` | string | Broad material category (e.g., "Steel", "Al") | Derived from `material_name` or metadata |
| `normalization_method` | string | "normalized" or "raw" | Set by Archard logic |
| `source_id` | string | Unique source identifier | Derived from filename/URL |
| `contact_area` | float | Contact area (mm²) | Derived or mapped (Optional) |
| `sliding_distance` | float | Sliding distance (m) | Derived or mapped (Optional) |

## 2. Derived Entities

### 2.1 `ModelPerformance`
Record of model evaluation metrics.
- `model_type`: string (e.g., "RandomForest")
- `r2_train`: float
- `r2_test`: float
- `mae_test`: float
- `rmse_test`: float
- `loo_r2`: float (if LOMO applied)
- `loo_ratio`: float (test_r2_loo / test_r2_standard)
- `fallback_active`: boolean (True if K-Fold used instead of LOMO)
- `within_material_scope`: boolean (True if research question shifted to within-material)

### 2.2 `FeatureImportance`
Mapping of feature to importance.
- `feature_name`: string
- `mean_abs_shap`: float
- `shap_p_value`: float (from permutation test)
- `is_significant`: boolean (p < 0.05)
- `vif_score`: float
- `dropped_reason`: string (if dropped due to VIF)

### 2.3 `DataSufficiency`
Record of data validation results.
- `total_records`: int
- `normalized_count`: int
- `raw_count`: int
- `missing_record_count`: int
- `source_count`: int
- `material_class_count`: int
- `study_scope`: string ("full_study", "pilot_study", "halt")
- `power_insufficiency_warning`: boolean
- `data_source_limitation_warning`: boolean

## 3. Data Flow

1.  **Raw Ingestion**: `data/raw/*.parquet` → `ingest.py` → `data/intermediate/merged.csv`
2.  **Validation**: `validate.py` checks column presence and record count (SC-004).
3.  **Preprocessing**: `preprocess.py` handles missing values, Archard normalization, VIF reduction → `data/processed/cleaned.csv`
4.  **Modeling**: `train.py` splits data, trains models, runs CV → `models/best_model.pkl`
5.  **Interpretation**: `interpret.py` computes SHAP → `reports/shap_summary.png`, `reports/feature_importance.json`

## 4. Constraints & Rules

- **No Imputation**: Missing predictors (except optional load/speed) result in row deletion.
- **Archard Fallback**: If `contact_load` or `sliding_speed` missing, `normalization_method` = "raw".
- **VIF Threshold**: Max VIF = 5. Iterative removal required.
- **Material Classes**: Minimum 3 for LOMO. If < 3, fallback to K-Fold.
- **Pipeline Enforcement**: All preprocessing steps must be inside a `Pipeline` to prevent leakage.
- **State Update**: Checksums must be recorded in `state/` after ingestion.