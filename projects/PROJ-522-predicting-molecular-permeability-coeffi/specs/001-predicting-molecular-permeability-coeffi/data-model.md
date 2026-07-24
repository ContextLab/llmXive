# Data Model: Predicting Molecular Permeability Coefficients

## Overview

This document defines the data structures, schemas, and transformation pipelines for the Molecular Permeability project. All data artifacts adhere to the Project Constitution (Data Hygiene, Reproducibility).

## Entities

### 1. Molecule
Represents a single chemical compound.
- **SMILES**: String (canonicalized).
- **Graph**: Adjacency list + Node features (Atomic Number, Hybridization, Degree, Formal Charge).
- **Descriptors**: Dictionary {MW: float, logP: float, PSA: float, RotatableBonds: int}.
- **Target**: Permeability Coefficient (float).
- **Status**: Valid, Invalid (parse error), MissingTarget.

### 2. ModelRun
Represents a single training iteration.
- **ModelType**: Enum {GCN, RF, LR}.
- **FoldID**: Integer (0-4).
- **Metrics**: Dictionary {R2: float, MAE: float, RMSE: float}.
- **Duration**: Float (seconds).
- **Seed**: Integer.

### 3. SensitivityResult
Represents the output of the uncertainty analysis.
- **Width**: Float (0.01, 0.05, 0.1).
- **MAE**: Float.
- **ConfidenceInterval**: String.

## File Formats

### Raw Data (`data/raw/*.parquet`)
- **Source**: HuggingFace datasets.
- **Format**: Apache Parquet.
- **Integrity**: SHA-256 checksum recorded in `state/...yaml`.
- **Content**: Raw SMILES and metadata.

### Processed Data (`data/processed/*.csv`, `*.json`)
- **Graph CSV**: `molecule_id, smi, adj_list_json, node_features_json`.
- **Descriptor CSV**: `molecule_id, MW, logP, PSA, RotatableBonds, target_permeability`.
- **Predictions CSV**: `fold_id, molecule_id, true_value, predicted_value, model_type`.

## Transformation Pipeline

1.  **Ingestion**:
    - Download `raw.parquet` from verified source.
    - Validate checksum.
    - Parse SMILES -> `Mol` (RDKit).
    - Filter: Remove rows with `NaN` in target column.
    - Handle Duplicates: Average target values for identical SMILES.
    - **Timeout**: Enforce 15-minute timeout for this step.
2.  **Graph Construction**:
    - Convert `Mol` to `torch_geometric.data.Data`.
    - Serialize to JSON/CSV for storage.
3.  **Splitting**:
    - Compute Murcko Scaffolds.
    - Split into 5 folds based on scaffold uniqueness.
4.  **Training**:
    - Iterate folds.
    - Train GNN, RF, LR.
    - Log metrics to `ModelRun` records.
    - **Timeout**: Enforce 2-hour timeout for this step.
5.  **Analysis**:
    - Compute sensitivity sweep.
    - Compute permutation importance.
    - Perform perturbation experiment (remove functional groups, check directionality).

## Constraints

- **Memory**: Graph data must fit in < 2GB RAM.
- **Time**: Graph construction < 15 mins; Training < 2 hours.
- **Reproducibility**: All random seeds pinned (default: a representative value).