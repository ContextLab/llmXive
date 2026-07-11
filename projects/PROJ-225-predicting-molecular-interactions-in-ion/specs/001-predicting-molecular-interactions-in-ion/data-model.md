# Data Model: Predicting Molecular Interactions in Ionic Liquids

## 1. Entity Overview
The core entity is the **IonPair**, representing a unique combination of a cation and an anion. The system tracks structural descriptors, computed interaction energy components, and statistical metadata.

## 2. Data Entities

### 2.1 IonPair
Represents a single row in the unified dataset.
- **Attributes**:
  - `cation_id`: Unique identifier for the cation (string).
  - `anion_id`: Unique identifier for the anion (string).
  - `cation_smiles`: SMILES string of the cation (string).
  - `anion_smiles`: SMILES string of the anion (string).
  - `structural_family_cation`: Categorical label (e.g., "imidazolium").
  - `structural_family_anion`: Categorical label (e.g., "BF4").
  - `electrostatic_energy`: Target variable (float, kcal/mol).
  - `dispersion_energy`: Target variable (float, kcal/mol).
  - `hbond_energy`: Target variable (float, kcal/mol).
  - `total_energy`: Sum of the above components (float, kcal/mol).
  - `tps_cation`: Topological Polar Surface Area of the cation (float, Å²).
  - `tps_anion`: Topological Polar Surface Area of the anion (float, Å²).
  - `molecular_surface_area`: Total molecular surface area (float, Å²).
  - `h_bond_count`: Integer (sum of donor/acceptor counts).
  - `graph_embedding`: Array of floats (Morgan fingerprint or similar).
  - `is_synthetic`: Boolean flag indicating if the row was generated via the synthetic protocol.

### 2.2 ModelArtifact
Serialized output of the training process.
- **Attributes**:
  - `model_id`: Unique identifier (e.g., "electrostatic_v1").
  - `component`: Target variable name ("electrostatic", "dispersion", "hbond").
  - `hyperparameters`: Dictionary of best parameters found by Optuna.
  - `mae_test`: Float (MAE on the held-out test set).
  - `feature_importance`: Dictionary mapping feature names to importance scores.
  - `timestamp`: ISO 8601 string.

### 2.3 ValidationRecord
Result of the independent DFT validation step.
- **Attributes**:
  - `ion_pair_id`: Reference to the IonPair.
  - `predicted_energy`: Float.
  - `dft_energy`: Float (from independent DFT calculation).
  - `error`: Float (absolute difference).
  - `structural_family`: Categorical label.

## 3. Data Flow
1.  **Raw Input**: SPICE JSONL + IL-SAPT (or Synthetic DFT) files.
2.  **Ingestion**: Parse, merge, validate, and generate descriptors (TPSA, Surface Area).
3.  **Split**: Stratified by `structural_family` (70/15/15).
4.  **Training**: XGBoost models saved as `.pkl` or `.json`.
5.  **Analysis**: ANOVA on raw data, DFT validation, reporting.

## 4. Constraints & Invariants
- **Non-Null**: `cation_smiles`, `anion_smiles`, and target energy columns must be non-null.
- **Uniqueness**: `(cation_id, anion_id)` must be unique in the dataset.
- **Range**: Energy values must be within physical bounds.
- **Stratification**: Train/Val/Test splits must maintain proportional representation of `structural_family`.
- **Descriptor Exclusion**: `partial_charge` columns are NOT included in the model input to prevent circular validation.