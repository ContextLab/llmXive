# Data Model: Predicting Molecular Surface Area from Graph Convolutional Networks

## Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to final evaluation. All data is stored in Parquet (for efficiency) or CSV (for interchange) formats. The graph features are formatted as **dense tensors** compatible with **PyTorch Geometric** (`torch-geometric`).

## Entity Definitions

### 1. Raw Molecule Record
*Source: ZINC15 Parquet*
- `smiles` (string): Canonical SMILES string.
- `mol_id` (string): Unique identifier (if available, else hash).

### 2. Processed Molecule (Graph + Label)
*Source: `data/processed/molecules.parquet`*
- `smiles` (string): Input SMILES.
- `mol_id` (string): Unique ID.
- `num_atoms` (int): Number of atoms in the molecule.
- `molecular_weight` (float): MW for stratification.
- `features_node` (list of floats): Flattened node feature matrix (Atom Type, Hybridization, etc.). **Format: Dense tensor compatible with PyG.**
- `features_edge` (list of floats): Flattened edge feature matrix (Bond Type, etc.). **Format: Dense tensor compatible with PyG.**
- `adjacency_matrix` (list of floats): Flattened adjacency matrix (dense). **Format: Dense tensor compatible with PyG.**
- `surface_area` (float): Ground truth 3D Surface Area (SASA, Å²) computed by RDKit on the lowest-energy conformer.
- `conformer_status` (string): "success", "failed", "minimized".
- `exclusion_reason` (string or null): Reason for exclusion (e.g., "invalid_smiles", "no_conformer", "too_large").
- `conformer_energy_variance` (float): Variance in energy across 5 generated conformers (used for stability check).

### 3. Conformer Configuration Log
*Source: `data/processed/conformer_config.json`*
- `batch_id` (string): Unique batch identifier.
- `rdkit_params` (object):
  - `numAttempts` (int): Number of conformer generation attempts.
  - `pruneRedundant` (bool): Whether to prune redundant conformers.
  - `maxIters` (int): Maximum minimization iterations.
  - `etkdg_version` (string): ETKDG version used (e.g., "ETKDGv3").
- `timestamp` (string): ISO 8601 timestamp.
- `success_count` (int): Number of molecules successfully processed in batch.
- `failure_count` (int): Number of molecules failed in batch.

### 4. Model Prediction Result
*Source: `data/processed/predictions.parquet`*
- `mol_id` (string): Unique ID.
- `true_surface_area` (float): Ground truth.
- `gcn_prediction` (float): GCN model output.
- `baseline_prediction` (float): Random Forest Baseline output (2D descriptors only).
- `gcn_error` (float): `|true - gcn_pred|`.
- `baseline_error` (float): `|true - baseline_pred|`.
- `split` (string): "train" or "test".

### 5. Sensitivity Analysis Result
*Source: `data/processed/sensitivity_results.parquet`*
- `threshold` (float): MAE cutoff (relative percentage of mean surface area: 0.01, 0.05, 0.10).
- `gcn_success_rate` (float): % of molecules with error <= threshold.
- `baseline_success_rate` (float): % of molecules with error <= threshold.
- `adjusted_p_value` (float): Bonferroni-corrected p-value for the difference.

## Data Flow

1.  **Ingest**: `raw/` (Parquet) -> `preprocess.py` -> `processed/molecules.parquet` + `conformer_config.json`.
    - *Filtering*: Invalid SMILES, failed conformers, >100 atoms.
    - *Labeling*: RDKit 3D generation (5 conformers, select lowest energy).
    - *Logging*: Exact RDKit parameters saved to `conformer_config.json`.
2.  **Split**: `processed/molecules.parquet` -> `splits/train.parquet`, `splits/test.parquet`.
    - *Method*: Stratified by `molecular_weight`.
3.  **Train**: `splits/train.parquet` -> `code/models/train.py` -> `results/gcn_model.pt`, `results/baseline_model.pkl`.
4.  **Eval**: `splits/test.parquet` + Models -> `eval/metrics.py` -> `processed/predictions.parquet`.
5.  **Sensitivity**: `processed/predictions.parquet` -> `eval/sensitivity.py` -> `processed/sensitivity_results.parquet`.

## Constraints & Validation

- **Missing Values**: `surface_area` must be non-null for all training records.
- **Range Checks**: `surface_area` > 0. `molecular_weight` > 0.
- **Consistency**: `mol_id` must be unique across splits.
- **Checksums**: All files in `data/` must have a recorded SHA256 hash in `state/`.
- **Format**: Graph features must be dense tensors compatible with PyTorch Geometric.
- **Logging**: `conformer_config.json` must be generated for every batch to satisfy Principle VII.