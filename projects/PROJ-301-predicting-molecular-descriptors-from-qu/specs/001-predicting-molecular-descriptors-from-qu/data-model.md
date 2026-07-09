# Data Model: Predicting Molecular Descriptors

## Overview

This document defines the data structures, schemas, and storage formats used throughout the pipeline. All data is stored in efficient, columnar formats (Parquet, NumPy) to minimize I/O overhead and memory footprint.

## Entities

### 1. Molecule
Represents a single chemical entity with its associated properties and identifiers.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `molecule_id` | `str` | Unique identifier (e.g., QM9 index or hash) | Dataset |
| `smiles` | `str` | Canonical SMILES string | Dataset |
| `mu` | `float` | Dipole moment (Debye) | Dataset (DFT) |
| `homo` | `float` | HOMO energy (eV) | Dataset (DFT) |
| `lumo` | `float` | LUMO energy (eV) | Dataset (DFT) |
| `geometry` | `dict` | Dictionary of atomic symbols and 3D coordinates | Dataset (XYZ) |

### 2. FeatureSet
Represents the input matrix for a specific model type.

| Field | Type | Description |
| :--- | :--- | :--- |
| `molecule_id` | `str` | Foreign key to Molecule |
| `features` | `ndarray` | Flattened feature vector (2D: 2048 bits; 3D: variable length graph) |
| `feature_type` | `str` | Enum: `"2D_morgan"`, `"3D_graph"` |

### 3. ModelResult
Stores the output of the training and evaluation process.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_id` | `str` | Unique identifier (e.g., `RF_2D_dipole`) |
| `feature_type` | `str` | `"2D_morgan"` or `"3D_graph"` |
| `target` | `str` | Target property (`mu`, `homo`, `lumo`) |
| `fold_metrics` | `list` | List of dicts: `{"fold": int, "mae": float, "rmse": float}` |
| `mean_mae` | `float` | Average MAE across folds |
| `std_mae` | `float` | Standard deviation of MAE (Stability metric) |
| `model_path` | `str` | Relative path to `.pkl` file |

## Storage Formats

- **Raw Data**: Parquet (compressed, columnar).
- **Processed Features**: NumPy (`.npy`) for dense matrices (2D) and Pickle (`.pkl`) for complex graph structures (3D).
- **Metrics**: JSON for structured metadata, CSV for tabular summaries.
- **Plots**: PNG (high resolution, 300 DPI).

## Data Flow

1. **Ingestion**: Raw QM9 Parquet -> `data/raw/qm9_subset.parquet`.
2. **Extraction**:
   - 2D: `data/processed/2d_features.npy` (Shape: [N, 2048]).
   - 3D: `data/processed/3d_graphs.pkl` (List of graph dicts).
   - Labels: `data/processed/labels.npy` (Shape: [N, 3]).
3. **Training**:
   - Models: `artifacts/models/*.pkl`.
   - Metrics: `artifacts/metrics/cv_results.json`.
4. **Analysis**:
   - Comparisons: `artifacts/metrics/comparison_table.csv`.
   - Plots: `artifacts/plots/parity_*.png`.
