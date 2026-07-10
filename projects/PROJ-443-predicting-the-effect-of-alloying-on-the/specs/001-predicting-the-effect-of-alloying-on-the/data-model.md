# Data Model: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Entity Definitions

### 1. HEA Sample
Represents a single high-entropy alloy instance.
- **Attributes**:
  - `sample_id`: Unique string identifier (e.g., "OQMD_12345").
  - `composition`: Dictionary of element:atomic_fraction (e.g., `{"Fe": 0.2, "Co": 0.2, ...}`).
  - `element_set`: Sorted string of unique elements (e.g., "CrMnFeCoNi"). Used for grouping.
  - `elastic_constants`: Dictionary containing `bulk_modulus`, `shear_modulus`, `young_modulus`, `poisson_ratio`.
  - `formation_energy`: Float (eV/atom).

### 2. Compositional Descriptor
Derived features calculated from the composition.
- **Attributes**:
  - `mixing_entropy`: Float (J/mol·K).
  - `atomic_radius_variance`: Float (Å²).
  - `electronegativity_variance`: Float.
  - `miedema_mixing_enthalpy`: Float (kJ/mol).
  - `miedema_radius_variance`: Float (Å²).
  - `miedema_electronegativity_variance`: Float.
  - `ilr_features`: List of Floats (transformed composition coordinates).

### 3. Model Performance Record
Evaluation metrics for a specific model run.
- **Attributes**:
  - `model_type`: String (e.g., "RandomForest").
  - `target_variable`: String (e.g., "ResidualBulkModulus").
  - `r2_score`: Float.
  - `rmse`: Float.
  - `mae`: Float.
 - `r2_ci_lower`: Float ([deferred] lower bound).
 - `r2_ci_upper`: Float ([deferred] upper bound).
  - `permutation_p_value`: Float.
  - `significant`: Boolean.

### 4. Source Metadata
Provenance information for external data.
- **Attributes**:
  - `source_name`: String (e.g., "OQMD").
  - `api_version`: String.
  - `query_parameters`: Dictionary.
  - `timestamp`: ISO 8601 string.
  - `checksum`: SHA-256 hash of the raw file.

## Data Flow

1.  **Ingestion**: Raw JSON/CSV from OQMD/MP → `data/raw/`.
2.  **Cleaning**: Normalization of composition, filtering for ≥5 elements → `data/processed/heas_clean.csv`.
3.  **Engineering**: Calculation of descriptors and ILR transformation → `data/processed/heas_features.parquet`.
4.  **Modeling**: Training and evaluation → `results/metrics.yaml`.
5.  **Reporting**: Aggregation of metrics and plots → `results/report.md`.

## Constraints & Rules

-   **Closure Constraint**: Composition percentages MUST sum to 1.0 (normalized if not).
-   **Miedema Exclusion**: If `target_variable` contains "Residual", `$MIEDEMA_FEATURES$` MUST be removed from the feature set before training.
-   **Grouping**: All bootstrap resampling MUST be grouped by `element_set`.
-   **Null Handling**: Missing elastic constants result in sample exclusion.
