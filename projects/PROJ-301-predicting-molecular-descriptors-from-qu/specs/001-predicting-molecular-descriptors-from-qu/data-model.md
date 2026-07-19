# Data Model: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

## Overview

This document defines the data schemas, storage formats, and relationships for the molecular descriptor prediction pipeline. All data is stored in local files under `data/` and `artifacts/`, with strict versioning and checksums.

## Entities & Relationships

### 1. Molecule (Raw)
The atomic unit of the dataset. Contains the raw 3D coordinates and DFT labels.
- **Source**: QM9 Parquet (HuggingFace)
- **Attributes**:
  - `molecule_id`: Unique identifier (string).
  - `smiles`: Canonical SMILES string (string).
  - `xyz`: 3D coordinates (list of floats, shape `[N_atoms, 3]`).
  - `mu`: Dipole moment (float, Debye).
  - `homo`: HOMO energy (float, eV).
  - `lumo`: LUMO energy (float, eV).
  - `valid`: Boolean flag indicating if geometry and labels are present.

### 2. FeatureSet (Derived)
The input matrix for machine learning models.
- **Source**: `extract_features.py`
- **Attributes**:
  - `molecule_id`: Foreign key to Molecule.
  - `features_2d`: Binary vector (array, shape `[2048]`).
  - `features_3d`: Graph representation (stored as adjacency list + node/edge feature arrays, or flattened if feasible).
  - `labels`: Dictionary `{mu, homo, lumo}`.

### 3. ModelResult (Artifact)
The output of the training phase.
- **Source**: `train_models.py`
- **Attributes**:
  - `model_type`: "2D" or "3D".
  - `hyperparameters`: JSON object of used params.
  - `cv_metrics`: List of fold results (MAE, RMSE per fold).
  - `model_path`: Path to `.pkl` file.

### 4. AnalysisReport (Artifact)
The final comparative results.
- **Source**: `analyze_results.py`
- **Attributes**:
  - `descriptor`: "mu", "homo", or "lumo".
  - `mae_2d`, `mae_3d`: Mean Absolute Errors.
  - `reli`: Relative Error Increase.
  - `p_value`: Result of paired t-test.
  - `failure_boundary`: Boolean (True if REI ≥ 10% or p < 0.0167).

## Storage Formats

| Entity | Format | Location | Description |
| :--- | :--- | :--- | :--- |
| **Raw Data** | Parquet | `data/raw/qm9_full.parquet` (streamed) | Original QM9 dataset. |
| **Subset Data** | Parquet | `data/raw/qm9_subset.parquet` | Sampled molecules fitting memory constraints. |
| **Features** | NumPy (`.npy`) | `data/processed/features_2d.npy`, `features_3d.npy` | Pre-processed feature matrices. |
| **Labels** | NumPy (`.npy`) | `data/processed/labels.npy` | Target vectors. |
| **Models** | Pickle (`.pkl`) | `artifacts/models/` | Trained Random Forest objects. |
| **Metrics** | JSON | `artifacts/metrics/cv_metrics.json` | Cross-validation results. |
| **Analysis** | JSON | `artifacts/metrics/analysis_report.json` | Final REI and statistical test results. |
| **Plots** | PNG | `artifacts/plots/` | Parity plots and error distributions. |

## Data Flow

1. **Download**: Stream QM9 from HF to `data/raw/`.
2. **Sample**: Apply stratified random sampling (binary search for max N) to create `qm9_subset.parquet`.
3. **Extract**: Generate 2D fingerprints and 3D graph features. Save to `.npy`.
4. **Train**: Load `.npy` and `.pkl` models. Save metrics to JSON.
5. **Analyze**: Load metrics, compute REI, run t-tests, generate plots. Save final report.
