# Data Model: Predicting Molecular Reactivity Using Graph Neural Networks

## Overview

This document defines the data structures, schemas, and transformation rules for the molecular reactivity prediction pipeline. The model ensures compatibility with PyTorch Geometric (for GNNs) and scikit-learn (for baselines), while adhering to the project's data hygiene and reproducibility principles.

## Entity Definitions

### 1. RawReaction
**Description**: A raw entry from the USPTO dataset containing SMILES strings and yield.
**Source**: `data/raw/uspto_*.parquet`
**Schema**:
- `reaction_smiles`: string (SMILES string representing the reaction)
- `yield`: float (0.0 to 100.0)
- `reaction_class`: string (Optional, for stratification)
- `source_id`: string (Unique identifier from dataset)

### 2. MolecularGraph (Processed)
**Description**: A molecular graph representation derived from a reaction. Contains nodes (atoms) and edges (bonds) with extracted features.
**Source**: `data/processed/graphs_*.pt` (PyTorch Geometric Data objects)
**Structure**:
- `x` (Node Features): Tensor of shape `[Num_Atoms, Num_Node_Features]`
  - Features: Atomic Number, Formal Charge, Hybridization, Degree, Aromaticity, Valence.
- `edge_index` (Edge Indices): Tensor of shape `[2, Num_Edges]`
- `edge_attr` (Edge Features): Tensor of shape `[Num_Edges, Num_Edge_Features]`
  - Features: Bond Type (Single, Double, Triple, Aromatic), Conjugation, In Ring.
- `y` (Target): Tensor of shape `[1]` (Normalized yield, 0.0-1.0)
- `reaction_center_mask`: Tensor of shape `[Num_Atoms]` (Boolean mask for atoms involved in reaction)
- `smiles`: string (Original SMILES for reference)

### 3. PredictionResult
**Description**: Output of the model inference, including point prediction and uncertainty interval.
**Source**: `results/predictions.json`
**Schema**:
- `model_type`: string ("GNN" or "Baseline")
- `reaction_id`: string
- `actual_yield`: float
- `predicted_yield`: float
- `lower_bound`: float (95% CI)
- `upper_bound`: float (95% CI)
- `error`: float (Absolute error)

### 4. MetricsReport
**Description**: Aggregated performance metrics for the entire experiment.
**Source**: `results/metrics.json`
**Schema**:
- `gnn`:
  - `r2_mean`: float
  - `r2_std`: float
  - `mae`: float
  - `rmse`: float
- `baseline`:
  - `r2_mean`: float
  - `r2_std`: float
  - `mae`: float
  - `rmse`: float
- `comparison`:
  - `relative_error_reduction`: float
  - `p_value`: float (from statistical test)
- `sensitivity`:
  - `noise_levels`: list[float]
  - `mae_values`: list[float]

## Transformation Rules

### SMILES to Graph
1. **Parse**: Use `rdkit.Chem.MolFromSmiles`.
2. **Validate**: Check `rdkit.Chem.rdmolops.SanitizeMol`. If fails, log and exclude.
3. **Extract Nodes**: Iterate atoms.
   - `atomic_num`: `atom.GetAtomicNum()`
   - `formal_charge`: `atom.GetFormalCharge()`
   - `hybridization`: `atom.GetHybridization()` (mapped to int)
   - `degree`: `atom.GetDegree()`
   - `is_aromatic`: `atom.GetIsAromatic()`
4. **Extract Edges**: Iterate bonds.
   - `bond_type`: `bond.GetBondType()` (mapped to int)
   - `is_conjugated`: `bond.GetIsConjugated()`
5. **Reaction Center**: Compare reactant and product atom environments to identify changed bonds/atoms.

### Normalization
- **Yield**: `y_normalized = y_raw / 100.0` (Range 0.0 to 1.0).
- **Inverse Transform**: `y_raw = y_normalized * 100.0`.

### Splitting
- **Stratified**: If `reaction_class` exists, split by class.
- **Random**: Otherwise, random split (Seed=42).
- **Ratio**: [deferred] Train (for CV), [deferred] Test.
- **CV**: 5-fold on Training set.

## Data Hygiene & Versioning

- **Checksums**: Every file in `data/raw/` and `data/processed/` must have a SHA-256 checksum recorded in `state/.../artifact_hashes`.
- **Immutability**: Raw data is never modified. Processed graphs are written to new files with version suffixes (e.g., `graphs_v1.pt`).
- **PII**: Chemical data is non-PII. No special handling required beyond standard data security.
