# Data Model: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Key Entities

### 1. HEA Sample
Represents a single high-entropy alloy instance.
- **Attributes**:
  - `sample_id`: Unique identifier (string).
  - `composition`: Dictionary of element: atomic_fraction (e.g., `{"Fe": 0.2, "Co": 0.2, ...}`).
  - `bulk_modulus`: Float (GPa).
  - `shear_modulus`: Float (GPa) [Optional, for future expansion].
  - `crystal_structure`: String (e.g., "FCC", "BCC").
  - `source`: String (e.g., "OQMD").
  - `is_valid`: Boolean (True if sum(composition) ≈ 1.0 and has bulk_modulus).

### 2. Compositional Descriptor
Represents a derived feature calculated from the raw composition.
- **Attributes**:
  - `sample_id`: FK to HEA Sample.
  - `delta_H_mix`: Float (kJ/mol).
  - `atomic_radius_variance`: Float.
  - `entropy_mix`: Float (J/mol/K).
  - `vec`: Float.
  - `electronegativity_variance`: Float.
  - `ilr_components`: List of Floats (ILR-transformed composition vector).
  - `target_residual`: Float (Bulk Modulus - Miedema Baseline).

### 3. Model Performance Record
Represents the evaluation output for a specific model configuration.
- **Attributes**:
  - `model_name`: String (e.g., "RandomForest", "ElasticNet").
  - `r2_score`: Float.
  - `rmse`: Float.
  - `mae`: Float.
  - `r2_ci_lower`: Float (95% CI lower bound).
  - `r2_ci_upper`: Float (95% CI upper bound).
  - `is_significant`: Boolean (True if 95% CI excludes 0).
  - `p_value_permutation`: Float (from permutation test).

### 4. Sensitivity Analysis Record
Represents the output of the threshold sweep (FR-006).
- **Attributes**:
  - `threshold`: Float (0.25, 0.30, 0.35).
  - `false_positive_rate`: Float.
  - `sample_count`: Integer.

### 5. Causal Language Check Record
Represents the result of the language validation scan (SC-004).
- **Attributes**:
  - `report_id`: String.
  - `causal_keywords_found`: List of Strings (e.g., "cause", "effect").
  - `is_clean`: Boolean (True if no causal keywords found).

### 6. Feature Importance Record
Represents the output of the interpretability module (SHAP/Permutation).
- **Attributes**:
  - `model_name`: String.
  - `feature_name`: String.
  - `mean_abs_shap`: Float.
  - `direction`: String (positive/negative/unknown).

## Data Flow

1.  **Raw Data**: Downloaded from OQMD (CSV) -> `data/raw/oqmd_targets.csv`.
2.  **Ingestion**: Filter for HEAs (≥5 elements) and valid elastic constants -> `data/processed/hea_samples_raw.csv`.
3.  **Normalization**: Enforce sum=1.0 -> `data/processed/hea_samples_normalized.csv`.
4.  **Feature Engineering**: Calculate descriptors + ILR (for linear) + Residuals -> `data/processed/hea_features.csv`.
5.  **Modeling**: Train models -> `results/predictions.json`.
6.  **Evaluation**: Bootstrap + FDR + Sensitivity + Language Check -> `results/metrics.yaml`, `results/sensitivity.yaml`, `results/causal_check.yaml`.
7.  **State Update**: Hash results and update `state/projects/...yaml`.

## Storage Strategy

- **Raw Data**: Stored as CSV/Parquet in `data/raw/`. Read-only.
- **Processed Data**: Stored as Parquet in `data/processed/`.
- **Results**: Stored as YAML/JSON in `results/`.
- **Checksums**: All files in `data/` have corresponding checksums recorded in `data/source_metadata.yaml`.