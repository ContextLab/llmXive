# Data Model: Molecular Permeability Prediction

## 1. Overview
This document defines the data schemas for the molecular permeability prediction pipeline. All data flows from raw SMILES to processed feature matrices and finally to model predictions.

## 2. Data Entities

### 2.1 Raw Molecule (Input)
- **Source**: Public datasets (SMILES + optional coefficients).
- **Format**: Parquet/CSV.
- **Fields**:
  - `smiles`: string (SMILES notation).
  - `permeability`: float (experimental coefficient, if available).
  - `polymer_type`: string (stratification key, if available).
  - `logP`: float (calculated logP, used as target in Proxy Mode).

### 2.2 Processed Molecule (Intermediate)
- **Source**: Derived from Raw Molecule via RDKit.
- **Format**: Parquet.
- **Fields**:
  - `smiles`: string.
  - `mol_valid`: boolean.
  - `descriptors`: dict (or flattened columns: `mw`, `logp`, `tpsa`, `hba`, `hbd`, `rotatable_bonds`).
  - `graph_nodes`: list (atomic features).
  - `graph_edges`: list (bond features).
  - `ablation_features`: list (flattened graph statistics for RF ablation baseline: mean node degree, graph connectivity, substructure counts).
  - `target`: float (permeability or proxy target value, e.g., calculated logP).

### 2.3 Model Output (Results)
- **Source**: Trained models.
- **Format**: JSON/CSV.
- **Fields**:
  - `molecule_id`: string.
  - `true_value`: float.
  - `predicted_gnn`: float.
  - `predicted_rf`: float.
  - `predicted_rf_ablation`: float.
  - `error_gnn`: float.
  - `error_rf`: float.

## 3. Transformation Logic

### 3.1 SMILES to Graph
1. Parse SMILES using `rdkit.Chem.MolFromSmiles`.
2. If `None`, mark `mol_valid=False`, log warning, exclude.
3. Extract node features: `[atomic_num, degree, formal_charge, hybridization, is_aromatic]`.
4. Extract edge features: `[bond_type, is_conjugated]`.

### 3.2 Descriptor Calculation
- Calculate `MW`, `logP` (Crippen), `TPSA`, `HBA`, `HBD`, `RotatableBonds` using `rdkit.Chem.Descriptors`.
- Handle missing values: Median imputation or row exclusion (per FR-003).

### 3.3 Ablation Feature Extraction
- Derive `ablation_features` from the graph structure:
  - Mean node degree.
  - Graph connectivity (number of edges / number of nodes).
  - Substructure counts (e.g., number of aromatic rings, number of specific functional groups).
- These features are flattened into a vector for the Random Forest ablation baseline.

### 3.4 Stratified Split
- Group by `polymer_type`.
- If `polymer_type` missing, use `logP` bins or random split.
- Ensure [deferred] train, [deferred] test.

## 4. Constraints
- **No NaNs**: Final input matrices must be NaN-free.
- **Consistency**: Graph structure must match SMILES exactly (Constitution Principle VI).
- **Target Integrity**: Target must not be derived from the input descriptors (Constitution Principle VII). **Exception**: In Proxy Mode, the target is calculated logP, which is derived from SMILES. This is explicitly flagged as a limitation.