# Data Model: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Entities & Relationships

### 1. HEA Sample
Represents a single alloy instance.
- **Attributes**:
  - `sample_id`: Unique identifier (string).
  - `composition`: Dictionary of element:atomic_percent (e.g., `{"Fe": 0.2, "Co": 0.2...}`).
  - `bulk_modulus_observed`: Float (GPa).
  - `bulk_modulus_miedema`: Float (GPa) (Calculated).
  - `bulk_modulus_residual`: Float (GPa) (Target: Observed - Miedema).
  - `constituent_elements`: String (e.g., "FeCoNiCrMn") (Grouping key).
  - `source`: String ("OQMD" or "MaterialsProject").

### 2. Compositional Descriptor
Derived features for ML.
- **Attributes**:
  - `sample_id`: Foreign key to HEA Sample.
  - `mixing_enthalpy`: Float (eV/atom) (Calculated via Miedema).
  - `atomic_radius_variance`: Float.
  - `electronegativity_variance`: Float.
  - `valence_electron_concentration`: Float.
  - `entropy_of_mixing`: Float.
  - `ilr_features`: Array of Float (ILR-transformed composition).
- **Constraint**: If `target_type` == "residual", `mixing_enthalpy` MUST be excluded from the predictor matrix.

### 3. Model Performance Record
Evaluation output.
- **Attributes**:
  - `model_name`: String ("RF", "GB", "ElasticNet").
  - `r2`: Float.
  - `rmse`: Float.
  - `mae`: Float.
  - `r2_ci_lower`: Float (95% CI).
  - `r2_ci_upper`: Float (95% CI).
  - `p_value_null`: Float (Test vs $R^2=0$).
  - `significant`: Boolean.
  - `fdr_corrected_p`: Float (Pairwise comparison).

### 4. Source Metadata
Provenance record (FR-010).
- **Attributes**:
  - `dataset_name`: String.
  - `api_version`: String (e.g., "v1", "2024-05").
  - `query_parameters`: String (JSON encoded).
  - `timestamp`: ISO 8601.
  - `checksum`: String (SHA256).

## Data Flow

1. **Ingestion**: Raw JSON/CSV from APIs -> `data/raw/`.
2. **Validation**: Check for `bulk_modulus` and `>=5` elements.
3. **Transformation**:
   - Normalize composition (sum=1).
   - Calculate Miedema enthalpy.
   - Apply ILR to composition.
   - Calculate Residual Target.
   - **Filter**: Remove Miedema enthalpy from features if Target is Residual.
4. **Storage**: `data/processed/hea_dataset.csv`.
5. **Modeling**: Train -> Evaluate -> `results/metrics.yaml`.
6. **Reporting**: Generate `paper/report.md` with associational disclaimer.
