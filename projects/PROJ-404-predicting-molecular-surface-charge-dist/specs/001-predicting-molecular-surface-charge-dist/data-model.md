# Data Model: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

## Overview

This document defines the data structures, schemas, and transformation pipelines required for the project. The data flows from raw Hugging Face Parquet files through preprocessing (normalization, splitting) to model input tensors.

## Entities

### 1. Molecule
Represents a single chemical entity in the dataset.

**Attributes**:
- `molecule_id`: Unique identifier (string).
- `atomic_numbers`: List of integers (atomic number for each atom).
- `coordinates`: 2D array of floats (N_atoms x 3).
- `connectivity`: 2D array of integers (N_atoms x N_atoms) or edge list (N_edges x 2).
- `charges`: 1D array of floats (N_atoms). Ground truth Merz-Kollman charges.
- `scaffold_id`: Integer identifier for the Bemis-Murcko scaffold.
- `split`: String ('train', 'val', 'test').

**Constraints**:
- `len(atomic_numbers) == len(coordinates) == len(charges)`
- No null values in `charges`.
- Coordinates normalized to center of mass.

### 2. ModelArtifact
Represents the trained model state.

**Attributes**:
- `model_id`: Unique identifier (hash).
- `architecture`: String ('SchNet', 'DimeNet', 'Baseline').
- `weights_path`: Relative path to `.pt` file.
- `training_config`: JSON blob (epochs, lr, seed, batch_size).
- `metrics`: JSON blob (train_loss, val_mae, test_mae, test_rmse, test_r).

### 3. PredictionBatch
Intermediate output of the model inference.

**Attributes**:
- `batch_id`: Integer.
- `predictions`: 2D array (N_molecules x N_atoms).
- `ground_truth`: 2D array (N_molecules x N_atoms).
- `molecule_ids`: List of strings.

## Data Flow

1. **Ingestion**: `data/raw/` -> `data/loader.py` (streaming) -> `Molecule` objects.
2. **Preprocessing**: `Molecule` -> `data/preprocess.py` (normalize coords, extract scaffold) -> `Molecule` (enriched).
3. **Splitting**: `Molecule` -> `data/splitter.py` (Bemis-Murcko) -> `train/val/test` sets.
4. **Model Input**: `train/val/test` -> `data/dataset.py` (PyTorch Dataset) -> `Data` objects (PyG).
5. **Training**: `Data` -> `models/schnet.py` -> `ModelArtifact`.
6. **Evaluation**: `ModelArtifact` + `test` -> `eval.py` -> `metrics` report.

## Constraints & Validation

- **Memory**: The total size of the `train` set in memory must not exceed a manageable threshold consistent with available system resources.
- **Schema**: All `Molecule` objects must match the `contracts/molecule.schema.yaml`.
- **Numerical Stability**: Coordinates must be normalized (mean=0, std=1 or center of mass=0).
- **Split Integrity**: No scaffold overlap between train, val, and test.

## File Formats

- **Raw**: Parquet (from Hugging Face).
- **Processed**: JSONL or Pickle (for intermediate splits, if needed).
- **Model**: PyTorch `.pt` (state dict).
- **Reports**: Markdown/JSON.
