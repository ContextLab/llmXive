# Data Model: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## 1. Entity Definitions

### CompositionRecord
Represents a single metallic glass entry.
- **`record_id`**: `str` (UUID) - Unique identifier.
- **`family`**: `str` - Alloy family (e.g., "Zr-based", "Pd-based").
- **`elements`**: `dict` - Mapping of element symbol to atomic fraction (e.g., `{"Zr": 0.5, "Cu": 0.5}`).
- **`tg_value`**: `float` - Glass transition temperature in Kelvin.
- **`source`**: `str` - DOI of the source dataset.
- **`status`**: `str` - "valid", "dropped_missing_tg", "dropped_incomplete_composition".

### DescriptorSet
Computed atomic features for a `CompositionRecord`.
- **`record_id`**: `str` - FK to `CompositionRecord`.
- **`radius_mismatch`**: `float` - $\delta$.
- **`electronegativity_diff`**: `float` - $\Delta\chi$.
- **`vec`**: `float` - Valence Electron Concentration.
- **`weighted_mean_radius`**: `float` - Diagnostic only.
- **`vif_radius`**: `float` - VIF for radius mismatch (post-remediation).
- **`vif_electro`**: `float` - VIF for electronegativity (post-remediation).
- **`vif_vec`**: `float` - VIF for VEC (post-remediation).

### ModelArtifact
Trained model and metadata.
- **`artifact_id`**: `str` - UUID.
- **`model_type`**: `str` - "GradientBoostingRegressor".
- **`hyperparameters`**: `dict` - e.g., `{"n_estimators": 100, "max_depth": 5}`.
- **`performance_metrics`**: `dict` - `{"r2_mean": float, "mae_mean": float, "r2_std": float}`.
- **`feature_importances`**: `dict` - Mapping of feature name to importance score.
- **`sensitivity_variance`**: `float` - $\sigma^2$ of R² across `max_depth` sweep.
- **`fdr_corrected_pvalues`**: `dict` - Feature pair -> adjusted p-value (Bonferroni).

## 2. Data Flow

1. **Raw Ingestion**: `data/raw/*.csv` (or zip) -> `ingest.py` -> `data/processed/cleaned_data.csv`.
   - **Schema Enforcement**: `ingest.py` validates input against `specs/.../contracts/dataset.schema.yaml` using `jsonschema`.
2. **Descriptor Computation**: `cleaned_data.csv` -> `descriptors.py` -> `data/processed/descriptors.csv`.
3. **Model Training**: `descriptors.csv` -> `train.py` -> `artifacts/models/best_model.pkl`.
4. **Analysis**: `best_model.pkl` + `descriptors.csv` -> `analyze.py` -> `artifacts/metrics/stats.json`.
   - **Schema Enforcement**: `analyze.py` validates output against `specs/.../contracts/artifact.schema.yaml` using `jsonschema`.
5. **Reporting**: `stats.json` + `best_model.pkl` -> `report.py` -> `paper/report.md`.

## 3. Data Constraints

- **Missing Data**: Records with missing `tg_value` or incomplete `elements` are dropped immediately.
- **Imputation**: No imputation for composition/Tg (FR-001). Listwise deletion only.
- **Normalization**: Descriptors are not normalized (Gradient Boosting is scale-invariant), but `vec` and `radius` are kept in native units for interpretability.
- **Encoding**: All categorical data (family) used only for splitting, not as a model feature.
- **Collinearity Remediation**: If VIF > 5, the feature with the highest VIF is dropped iteratively until all remaining features have VIF < 5.