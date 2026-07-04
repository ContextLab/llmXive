# Data Model: Predicting the Impact of Composition on the Glass Transition Temperature of Chalcogenide Glasses

## Entity Definitions

### ChalcogenideSample
Represents a single glass composition.
- `elemental_formula`: String (e.g., "Ge20Se80")
- `mean_coordination_number`: Float (Derived)
- `electronegativity_variance`: Float (Derived)
- `atomic_radius_variance`: Float (Derived)
- `residualized_electronegativity_variance`: Float (Derived, if VIF > 5)
- `residualized_atomic_radius_variance`: Float (Derived, if VIF > 5)
- `Tg_value`: Float (Target)
- `chemical_family`: String (e.g., "Ge-Se", "As-S")

### ModelPerformance
Represents evaluation results for a single model run.
- `model_type`: String ("GradientBoosting", "LinearRegression")
- `rmse`: Float
- `r_squared`: Float
- `cv_fold_scores`: List[Float]
- `training_time_seconds`: Float
- `ci_lower`: Float (95% CI lower bound for SHAP difference, SC-006)
- `ci_upper`: Float (95% CI upper bound for SHAP difference, SC-006)
- `is_significant`: Boolean (True if CI excludes 0, SC-006)
- `mdes`: Float (Minimum Detectable Effect Size for heterogeneity term)
- `power_achieved`: Float (Estimated power for MDES)
- `transferability_metrics`: Dict (Family name -> Feature Importance Difference CI)

### SHAPImportance
Represents feature attribution for a specific sample or aggregate.
- `feature_name`: String
- `mean_absolute_shap_value`: Float
- `shap_value_distribution`: Dict (min, max, mean)

### SHAPSample
**Derived Artifact**: Represents the sampled subset of data used for SHAP analysis to satisfy memory constraints.
- `sample_id`: String (Unique identifier for the sampling run)
- `source_hash`: String (Hash of the parent processed dataset)
- `sample_size`: Integer (Number of samples in this subset)
- `sampling_seed`: Integer (Random seed used for reproducibility)
- `checksum`: String (Content hash of this specific subset file)

### StateManifest
**Registry Artifact**: Tracks all artifacts and their hashes for Versioning Discipline (Constitution Principle V).
- `artifacts`: List[Object]
  - `path`: String (Relative path to file)
  - `type`: String (e.g., "raw", "processed", "derived", "report", "residualized")
  - `checksum`: String (SHA-256 hash)
  - `created_at`: String (ISO 8601 timestamp)

## Data Flow

1. **Raw Data**: Downloaded from supplementary source (CSV/Excel).
   - Columns: `composition`, `Tg`, `family` (if available).
   - **Action**: Checksum raw file. Record in `state/manifest.json`.
2. **Preprocessed Data**:
   - `features.csv`: Contains `elemental_formula` + derived features.
   - **Action**: Checksum processed file. Record in `state/manifest.json`.
3. **Residualized Data** (Conditional):
   - `residualized_features.csv`: If VIF > 5, contains orthogonalized features.
   - **Action**: Checksum residualized file. Record in `state/manifest.json`.
4. **SHAP Subset**:
   - `shap_subset.csv`: Sampled version of `features.csv` (≤5000 rows).
   - **Action**: Checksum subset file. Record in `state/manifest.json` with `SHAPSample` metadata.
5. **Model Artifacts**:
   - `model_gbr.pkl`: Trained Gradient Boosting model.
   - `shap_values.npy`: SHAP values array.
6. **Reports**:
   - `performance_metrics.json`: RMSE, R², VIF, CI (SC-006), MDES, Transferability metrics.
   - `shap_report.md`: Interpretability summary (with `causal_disclaimer` and `power_limitation` sections).

## Constraints

- **Missing Data**: Samples with incomplete formulas are excluded. Count logged. If columns missing, record `DATA_MISSING: Required column [column_name] not found` (SC-008).
- **Memory**: Dataset sampled to ≤5000 rows for SHAP if original size > 5000. The subset is a **new artifact** with its own hash.
- **Collinearity**: If VIF > 5, features are not removed but flagged in the report. Orthogonalization (Residualization) applied as mitigation strategy (SC-007).
- **Causal Claims**: All reports must include a disclaimer that findings are associative.
- **Versioning**: All artifacts recorded in `state/manifest.json` with checksums.