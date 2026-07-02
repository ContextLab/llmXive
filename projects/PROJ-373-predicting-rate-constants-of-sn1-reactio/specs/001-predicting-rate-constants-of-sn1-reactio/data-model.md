# Data Model: Predicting Rate Constants of SN1 Reactions

## 1. Entity Definitions

### Molecule
Represents a chemical substrate in the SN1 reaction context.
-   **smiles**: `string` - Canonical SMILES representation.
-   **substrate_class**: `enum` - One of `["secondary", "tertiary"]`. Derived from graph analysis.
-   **leaving_group**: `string` - e.g., "Cl", "Br", "I".
-   **steric_index**: `float` - Calculated steric hindrance metric (RDKit).
-   **gasteiger_charges**: `list[float]` - Partial charges for each atom.
-   **topological_indices**: `dict` - { "wiener": float, "zagreb": float, ... }.

### ReactionRate
Represents the experimental outcome.
-   **rate_constant**: `float` - Value in s⁻¹ (standardized).
-   **temperature**: `float` - Temperature in Kelvin.
-   **solvent**: `string` - Solvent name (optional, may be null).
-   **source_id**: `string` - ID from the source dataset (e.g., DTS-SN1 row ID).

### ModelConfiguration
Represents a trained model instance.
-   **config_id**: `string` - Unique hash of hyperparameters.
-   **hyperparameters**: `dict` - { "learning_rate": float, "hidden_dim": int, "dropout": float, "layers": int }.
-   **metrics**: `dict` - { "train_r2": float, "val_r2": float, "test_r2": float, "test_mae": float }.
-   **training_time**: `float` - Seconds.

## 2. Data Flow & Transformations

1.  **Raw Ingestion**:
    -   Input: `merged-file.jsonl` (DTS-SN1).
    -   Output: `raw_data.csv` (SMILES, rate, raw metadata).
2.  **Cleaning & Filtering**:
    -   Input: `raw_data.csv`.
    -   Logic:
        -   Parse SMILES.
        -   Compute steric index.
        -   Filter: `steric_index > 2.0` OR `substrate_class == "primary"`.
        -   Filter: Missing rate constant.
    -   Output: `cleaned_data.csv` + `exclusion_report.jsonl`.
3.  **Descriptor Computation**:
    -   Input: `cleaned_data.csv`.
    -   Logic: Compute Gasteiger charges, Topological indices.
    -   Output: `processed_data.csv` (includes all descriptors).
4.  **Splitting**:
    -   Input: `processed_data.csv`.
    -   Logic: Stratified split (70/15/15) by `substrate_class`.
    -   Output: `train.csv`, `val.csv`, `test.csv`.
5.  **Model Training**:
    -   Input: `train.csv`, `val.csv`.
    -   Output: `model_weights.pt`, `metrics.json`.

## 3. Schema Constraints

-   **SMILES**: Must be canonicalized. If canonicalization fails, row is excluded.
-   **Rate Constant**: Must be > 0. If 0 or negative, excluded (log error).
-   **Substrate Class**: Must be "secondary" or "tertiary". Any other value is excluded.
-   **Missing Values**: No missing values allowed in `train`, `val`, or `test` sets. Rows with missing descriptors are excluded.
