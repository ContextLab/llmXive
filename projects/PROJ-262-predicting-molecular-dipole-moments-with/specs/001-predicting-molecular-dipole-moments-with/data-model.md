# Data Model: Predicting Molecular Dipole Moments with Graph Neural Networks

## 1. Overview

This document defines the data structures, schemas, and transformation flows for the molecular dipole moment prediction pipeline. All data artifacts are derived from the QM9 dataset and must adhere to the contracts defined in `contracts/`.

## 2. Data Flow

1.  **Raw Data**: `data/raw/qm9_subset.parquet`
    *   Source: QM9 (PyTorch Geometric loader).
    *   Content: A large-scale dataset of molecules with `mol_id`, `z` (atom types), `pos` (3D coords), `edge_index`, `mu` (dipole).
2.  **Processed Features**: `data/processed/features_2d.parquet` and `data/processed/features_3d.parquet`
    *   Derivation: `code/preprocess.py`.
    *   Content: 2D descriptors (fingerprints, topological counts) and 3D graph features.
3.  **Model Outputs**: `results/predictions.csv`
    *   Content: Predicted dipole moments, errors, and feature attribution scores.

## 3. Schema Definitions

### 3.1 Input Schema (QM9 Subset)
*Derived from the verified QM9 PyTorch Geometric loader. See `contracts/molecule.schema.yaml`.*

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `mol_id` | string | Unique molecule identifier | Non-null, unique |
| `z` | int[] | Atomic numbers (e.g., [6, 1, 8]) | Length > 0 |
| `pos` | float[][] | 3D coordinates (Angstroms) | Shape: (N_atoms, 3) |
| `edge_index` | int[][] | Bond connectivity (2 x N_edges) | Valid graph topology |
| `mu` | float | Dipole moment magnitude (Debye) | >= 0.0 |

### 3.2 Feature Set Schema
*Output of `preprocess.py`. See `contracts/feature_set.schema.yaml`.*

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `mol_id` | string | Molecule ID | Non-null |
| `morgan_fp` | int[] | Morgan fingerprint (2048 bits) | Length = 2048 |
| `topo_counts` | int[] | Topological counts (atoms, bonds, etc.) | Length = 10 |
| `atom_types_onehot` | float[][] | One-hot encoded atom types | Shape: (N_atoms, 6) |
| `pos_norm` | float[][] | Normalized 3D coordinates | Shape: (N_atoms, 3) |

### 3.3 Prediction Output Schema
*Output of `evaluate.py`. See `contracts/prediction_output.schema.yaml`.*

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `mol_id` | string | Molecule ID | Non-null |
| `true_mu` | float | Ground truth dipole | >= 0.0 |
| `pred_mu_gnn` | float | GNN prediction | Any |
| `pred_mu_rf` | float | Random Forest prediction | Any |
| `error_gnn` | float | `abs(true - pred_gnn)` | >= 0.0 |
| `error_rf` | float | `abs(true - pred_rf)` | >= 0.0 |
| `seed` | int | Random seed used | 0-4 |

## 4. Data Hygiene Rules

*   **Checksumming**: Every file in `data/raw` must be checksummed (SHA-256) upon download.
*   **Immutability**: Raw data files are never modified. All transformations produce new files in `data/processed`.
*   **NaN Handling**: Molecules with missing 3D coordinates or NaN dipole values are excluded during preprocessing and logged in `data/processed/exclusion_log.txt`.
*   **Versioning**: Each processed dataset file includes a `source_hash` and `transform_date` in its metadata.