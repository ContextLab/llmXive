# Data Model: Predicting Molecular Surface Area from Graph Convolutional Networks

## Overview

This document defines the data structures, schemas, and transformation logic for the project. All data artifacts are stored in `data/` and must be checksummed.

## Entity Definitions

### Molecule
A chemical compound represented by its SMILES string and derived features.
- **Attributes**:
  - `smiles`: string (canonicalized)
  - `molecular_weight`: float
  - `num_atoms`: int
  - `num_bonds`: int
  - `sasa`: float (Solvent Accessible Surface Area in Å², computed from 3D conformer)
  - `graph_features`: dict (node features, edge features)
  - `conformer_failed`: boolean
  - `conformer_params`: dict (metadata: numThreads, maxAttempts, energy_min_steps)

### Graph
A 2D molecular topology representation.
- **Nodes**: Atoms. Features: [Atomic Number, Degree, Hybridization, Formal Charge, Aromaticity].
- **Edges**: Bonds. Features: [Bond Type, Conjugated, Ring].

### Model Artifact
- **GCN Model**: Weights and hyperparameters.
- **Evaluation Metrics**: MAE, RMSE, R², P-value, Effect Size.

## Data Flow

1.  **Raw Ingestion**: `data/raw/chembl_raw.parquet` (Downloaded from Hugging Face).
2.  **Preprocessing**: `data/processed/paired_dataset.parquet` (SMILES + 2D Graph + 3D SASA).
3.  **Splits**: `data/processed/train.parquet`, `data/processed/test.parquet`.
4.  **Results**: `data/results/metrics.json`, `data/results/sensitivity_analysis.csv`.
5.  **Metadata**: `data/processed/conformer_params.json` (RDKit parameters used).

## Schema Definitions

### Input Schema (Raw Dataset)
- Source: Hugging Face Parquet.
- Columns: `smiles`, `mol_wt`, `logp`, `...` (various RDKit descriptors).

### Processed Schema (Intermediate)
- File: `data/processed/paired_dataset.parquet`
- Columns:
  - `smiles`: string
  - `atom_features`: list[float] (flattened or list of lists)
  - `bond_features`: list[float]
  - `sasa`: float
  - `molecular_weight`: float
  - `num_atoms`: int
  - `conformer_failed`: boolean
  - `conformer_params`: dict (stored as JSON string or separate file reference)

### Output Schema (Results)
- File: `data/results/metrics.json`
- Structure:
  ```json
  {
    "gcn": { "mae": float, "rmse": float, "r2": float },
    "oracle": { "mae": 0.0, "rmse": 0.0, "r2": 1.0 },
    "comparison": { "p_value": float, "statistic": float, "test_type": "t-test" | "wilcoxon" },
    "sensitivity": [ ... ]
  }
  ```

## Transformation Logic

1.  **SMILES to Graph**:
    - Use `rdkit.Chem.rdmolfiles.MolFromSmiles`.
    - Extract atom/bond features.
    - Handle invalid SMILES: Log and exclude.
2.  **SMILES to SASA**:
    - Generate 3D conformer: `rdkit.Chem.AllChem.EmbedMolecule`.
    - Minimize: `rdkit.Chem.AllChem.UFFOptimizeMolecule`.
    - Calculate SASA: `rdkit.Chem.rdMolDescriptors.CalcSASA`.
    - Handle failure: If `EmbedMolecule` returns -1, mark `conformer_failed=True` and exclude from training. Log parameters to `conformer_params.json`.
3.  **Data Split**:
    - Stratify by `molecular_weight`.
    - Ensure KS test p-value > 0.05 between train/test distributions.

## Data Hygiene Rules

- **Checksums**: Every file in `data/` must have a corresponding `.sha256` file.
- **Immutability**: Raw files are never modified. Processed files are new versions.
- **PII**: No PII in chemical data.
- **Versioning**: All data files include a `version` field in metadata (e.g., `v1.0.0`).
