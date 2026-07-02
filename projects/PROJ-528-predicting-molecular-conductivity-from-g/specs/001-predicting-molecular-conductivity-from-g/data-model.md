# Data Model: Predicting Molecular Conductivity from Graph-Based Features

## Entities and Relationships

### Molecule
The core entity representing a chemical compound.
- **Attributes**:
  - `smiles`: String (Canonical SMILES).
  - `molecular_weight`: Float (g/mol).
  - `target_value`: Float (log-transformed conductivity, HOMO-LUMO gap, or raw value).
  - `target_type`: String ("conductivity" or "homo_lumo_gap").
  - `source_dataset`: String (e.g., "HOMO-LUMO", "SMILES-Transformers").
  - `is_valid`: Boolean (True if SMILES parsed and descriptors computed successfully).

### Descriptor
A numeric feature derived from the molecular graph.
- **Attributes**:
  - `molecule_id`: Foreign Key (links to Molecule).
  - `feature_name`: String (e.g., "aromatic_ring_count", "conj_path_len").
  - `feature_value`: Float.
  - `vif_score`: Float (calculated during analysis).
  - `is_excluded`: Boolean (True if VIF > 10).

### ModelRun
A record of a specific training experiment.
- **Attributes**:
  - `run_id`: UUID.
  - `model_type`: String ("RandomForest", "GradientBoosting").
  - `outlier_threshold`: Float (e.g., 3.0).
  - `r2_test`: Float.
  - `mae_test`: Float.
  - `r2_cv_mean`: Float.
  - `r2_cv_std`: Float.
  - `timestamp`: DateTime.

## Data Flow

1.  **Ingestion**: Raw datasets (Parquet) are downloaded to `data/raw/`.
2.  **Cleaning**:
    -   SMILES validation (RDKit).
    -   Target variable filtering (remove NaN, check distribution).
    -   Conditional log-transformation based on distribution.
    -   Merging datasets if multiple sources are used.
    -   **Halt Check**: If no valid target variable found, stop pipeline.
3.  **Transformation**:
    -   Descriptor computation (RDKit).
    -   **Correlation Pre-check**: Validate proxy hypothesis.
    -   VIF calculation and iterative feature filtering/retraining.
4.  **Modeling**:
    -   Scaffold splitting.
    -   Retraining loop for sensitivity analysis.
5.  **Output**:
    -   `data/processed/descriptors.csv` (Intermediate)
    -   `data/processed/model_results.json` (Final Contract)
    -   `data/processed/feature_importance.csv` (Intermediate)
    -   `data/processed/correlation_plots/`

## Schema Definitions (Contracts)

The data model is enforced via the following schema contracts:
-   `contracts/dataset_schema.yaml`: Validates the input processed dataset.
-   `contracts/model_output_schema.yaml`: Validates the JSON results of model training.
-   `contracts/feature_schema.yaml`: Validates the feature importance and VIF output.

## Storage Format Clarification
-   **Intermediate Files**: CSV/Parquet formats are used for descriptors and splits for efficiency.
-   **Final Contract Outputs**: JSON format is used for `model_results.json` and `feature_importance.csv` (converted to JSON structure) to align with `contracts/*.schema.yaml`.