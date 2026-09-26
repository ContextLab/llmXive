# Data Model: Predicting Molecular Conductivity from Graph-Based Features

## Entities

### Molecule
A single chemical compound represented by a SMILES string and its associated properties.
-   **smiles**: String (Input)
-   **molecular_weight**: Float (Computed)
-   **log_conductivity**: Float (Target, log10 transformed)
-   **is_valid**: Boolean (Validation status)
-   **scaffold_id**: String (Cluster identifier for scaffold splitting)

### Descriptor
A numeric feature computed from the molecular graph.
-   **descriptor_name**: String (e.g., "aromaticity_index", "conjugation_length")
-   **value**: Float
-   **vif_score**: Float (Calculated during preprocessing)
-   **is_excluded**: Boolean (True if VIF > 10)

### ModelResult
Output of the training and evaluation phase.
-   **model_type**: String ("RandomForest" or "GradientBoosting")
-   **r2_test**: Float
-   **mae_test**: Float
-   **cv_r2_mean**: Float
-   **cv_r2_std**: Float
-   **feature_importance**: List of (feature_name, score) tuples

## Data Flows

1.  **Input**: `data/raw/input.csv` (SMILES, Conductivity) OR Hugging Face dataset.
2.  **Validation**: `code/preprocessing.py` checks for valid SMILES and non-missing conductivity. Invalid rows dropped.
3.  **Descriptor Computation**: `code/descriptors.py` computes 10+ features. Output: `data/processed/descriptors.csv`.
4.  **Collinearity Check**: `code/preprocessing.py` calculates VIF. Rows with VIF > 10 features are flagged/removed.
5.  **Splitting**: `code/split.py` performs scaffold split. Output: `data/processed/train.csv`, `data/processed/test.csv`.
6.  **Training**: `code/train.py` fits models. Output: `data/processed/models.pkl`, `data/processed/metrics.json`.
7.  **Evaluation**: `code/evaluate.py` computes FDR-corrected p-values, plots. Output: `data/processed/plots/`, `data/processed/reports/`.

## Schema Definitions (Contracts)

See `contracts/` directory for formal YAML schemas.

-   `input.schema.yaml`: Validates raw input CSV (SMILES, Conductivity columns).
-   `descriptor.schema.yaml`: Validates computed descriptor CSV (all numeric, no NaN).
-   `model_output.schema.yaml`: Validates JSON results (R², MAE, CV scores).
