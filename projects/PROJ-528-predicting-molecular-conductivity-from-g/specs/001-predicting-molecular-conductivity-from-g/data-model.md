# Data Model: Predicting Molecular Conductivity from Graph-Based Features

## Entity Definitions

### Molecule
A chemical compound represented by a SMILES string and associated properties.
*   `smiles`: String (Canonical SMILES).
*   `id`: String (Unique identifier).
*   `target_value`: Float (Log-transformed HOMO-LUMO gap).
*   `is_valid`: Boolean (Flag for valid SMILES and non-missing target).

### Descriptor
A numeric feature computed from the molecular graph.
*   `name`: String (e.g., "aromaticity_index", "conjugation_path_length").
*   `value`: Float.
*   `source`: String ("rdkit" or "quantum").

### Model
A trained regression model.
*   `model_type`: String ("RandomForest" or "GradientBoosting").
*   `hyperparameters`: JSON (e.g., `{"n_estimators": 100}`).
*   `metrics`: JSON (e.g., `{"r2": 0.85, "mae": 0.12}`).
*   `feature_importance`: List of tuples (feature_name, score).

## Data Flow

1.  **Raw Input**: `data/raw/` contains downloaded Parquet/CSV files (QM9).
2.  **Descriptor Computation**: `02_compute_descriptors.py` reads SMILES, computes 10+ descriptors, writes `data/processed/descriptors_base.csv`.
    *   **Schema Mapping**: Computes `degree_mean` and `degree_std` as separate columns.
3.  **Preprocessing**: `03_preprocess.py` merges descriptors with target, handles missing values, applies log-transform, performs scaffold split, writes `data/processed/cleaned.csv`.
    *   **Validation**: Checks dynamic range (FR-011) and target type (FR-014).
4.  **Training**: `04_train_models.py` trains models, writes `data/processed/model_results.json`.
5.  **VIF Analysis**: `05_vif_analysis.py` calculates VIF, drops high-VIF features, retrains, writes `data/processed/vif_iteration_log.json`.
6.  **Importance**: `06_feature_importance.py` computes permutation importance, applies BH correction, writes `data/processed/feature_importance.csv`.
7.  **Sensitivity**: `07_sensitivity_analysis.py` sweeps outlier thresholds, writes `data/processed/sensitivity_results.json`.

## Schema Definitions

### Input Schema (SMILES)
*   `smiles`: string (required)
*   `homo_lumo_gap`: float (optional, if available in raw dataset)

### Output Schema (Descriptors)
*   `smiles`: string
*   `aromatic_ring_count`: integer
*   `conjugation_path_length`: float
*   `average_path_length`: float
*   `degree_mean`: float
*   `degree_std`: float
*   `ring_count`: integer
*   `molecular_weight`: float
*   `homo_lumo_gap`: float (if available)
*   `is_valid`: boolean

### Output Schema (Model Results)
*   `model_type`: string
*   `r2_test`: float
*   `mae_test`: float
*   `r2_cv_mean`: float
*   `r2_cv_std`: float
*   `feature_importance_ranking`: list of strings
*   `vif_excluded_features`: list of strings
*   `target_type`: string ("homo_lumo_gap" or "topological_proxy")

### Output Schema (Feature Importance)
*   `feature_name`: string
*   `importance_score`: float
*   `p_value_raw`: float
*   `p_value_adjusted`: float (Benjamini-Hochberg corrected)
*   `is_significant`: boolean (based on adjusted p-value)

## Data Hygiene Rules
*   **Checksums**: All files in `data/raw/` and `data/processed/` must have corresponding SHA-256 checksums in `state/`.
*   **Immutability**: Raw files are never modified. All transformations create new files.
*   **Logging**: Every script logs its input/output file paths and row counts to `logs/`.