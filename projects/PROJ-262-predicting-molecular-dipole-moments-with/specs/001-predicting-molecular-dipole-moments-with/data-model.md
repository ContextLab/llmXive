# Data Model: Predicting Molecular Dipole Moments with Graph Neural Networks

## 1. Data Flow Overview

1.  **Raw Data**: QM9 Parquet file (downloaded from verified HF URL).
2.  **Preprocessed Data**:
    *   `processed/train.parquet`: Training set with features.
    *   `processed/val.parquet`: Validation set.
    *   `processed/test.parquet`: Test set.
    *   `reports/excluded_molecules.csv`: List of molecules with missing 3D coordinates.
3.  **Model Artifacts**:
    *   `models/schnet_seed_{N}.pt`: Trained GNN weights.
    *   `models/rf_seed_{N}.pkl`: Trained RF model.
4.  **Results**:
    *   `results/metrics.json`: MAE, RMSE, CIs per seed.
    *   `results/attribution.json`: Feature importance rankings.

## 2. Entity Definitions

### 2.1 Molecule
A single chemical entity in the dataset.
*   **ID**: Unique string (e.g., `qm9_00001`).
*   **Formula**: String (e.g., `C6H6`).
*   **Dipole Vector**: `[μx, μy, μz]` (float32).
*   **Dipole Magnitude**: `μ` (float32).
*   **Coordinates**: `[[x1, y1, z1], [x2, y2, z2], ...]` (float32).
*   **Atom Types**: `[type1, type2, ...]` (int/one-hot).
*   **Status**: `valid` or `excluded`.

### 2.2 Feature Vector
The input representation for the model.
*   **2D Features**:
    *   `morgan_fp`: Binary array (length 2048).
    *   `coulomb_eigen`: Sorted eigenvalues of Coulomb matrix (length ~100).
*   **3D Features**:
    *   `atom_types`: One-hot encoded.
    *   `edge_distances`: Pairwise distances (used internally by SchNet).
    *   `edge_types`: Bond types (if available).

### 2.3 Model Output
*   **Prediction**: Predicted dipole magnitude (float32).
*   **Error**: `|predicted - actual|`.
*   **Attribution**: Importance score per atom/feature.

## 3. Data Contracts

### 3.1 Input Dataset Contract
The raw dataset must contain the following columns:
*   `mol_id`: string
*   `dipole`: float (magnitude)
*   `dipole_vector`: array (3 floats)
*   `coordinates`: array (N x 3 floats)
*   `atom_numbers`: array (N ints)
*   `n_atoms`: int

### 3.2 Output Metrics Contract
The final metrics file must contain:
*   `seed`: int
*   `model_type`: string ("GNN" or "RF")
*   `mae`: float
*   `rmse`: float
*   `ci_lower`: float
*   `ci_upper`: float

### 3.3 Exclusion Report Contract
*   `mol_id`: string
*   `reason`: string (e.g., "missing_coords")
