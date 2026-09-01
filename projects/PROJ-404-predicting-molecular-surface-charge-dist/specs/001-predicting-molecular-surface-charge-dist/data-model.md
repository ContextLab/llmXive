# Data Model: Predicting Molecular Surface Charge Distribution

## Overview
This document defines the data schemas for the molecular charge prediction pipeline. It ensures that data loading, training, and evaluation steps operate on consistent structures, adhering to the project's data hygiene and reproducibility principles.

## Entity Definitions

### Molecule
A single chemical entity represented as a graph with 3D attributes.
- **ID**: Unique identifier (e.g., `qm9_id`).
- **Atoms**: List of atomic numbers ($Z$).
- **Coordinates**: 3D Cartesian coordinates ($x, y, z$) in Angstroms.
- **Bonds**: List of edge indices and bond types (single, double, etc.).
- **Charges**: Ground-truth Merz-Kollman partial charges for each atom.

### Model Artifact
The trained GNN instance.
- **Weights**: PyTorch state dictionary.
- **Config**: Architecture hyperparameters (hidden_dim, num_layers, etc.).
- **Metadata**: Training seed, dataset version, timestamp.

### Prediction
The output of the model for a given molecule.
- **Molecule ID**: Reference to the input molecule.
- **Predicted Charges**: Vector of scalar charge predictions.
- **Ground Truth Charges**: Vector of actual Merz-Kollman charges.
- **Metrics**: MAE, RMSE, $R$ for the molecule (optional, aggregated at dataset level).

## Data Flow

1.  **Raw Input**: QM9 Parquet file (streamed).
2.  **Processed Input**: Normalized coordinates, scaffold split indices.
3.  **Model Input**: PyTorch Geometric `Data` objects (batched).
4.  **Output**: JSON report with aggregated metrics.

## Schema Details

### Input Schema (QM9 Subset)
Derived from the Hugging Face QM9 dataset.
- `atom_types`: `List[int]` (Atomic numbers)
- `positions`: `List[List[float]]` (3D coordinates)
- `bonds`: `List[List[int]]` (Edge indices)
- `charge`: `List[float]` (Merz-Kollman charges)

### Output Schema (Evaluation Report)
JSON structure for the final report.
- `model_version`: `string`
- `dataset_version`: `string`
- `metrics`:
  - `mae`: `float`
  - `rmse`: `float`
  - `pearson_r`: `float`
- `baseline_metrics`:
  - `mae`: `float`
  - `rmse`: `float`
  - `pearson_r`: `float`
- `hypothesis_validated`: `boolean` (True if 3D MAE ≤ 0.05 e AND 3D MAE < 2D MAE)
- `exit_code`: `integer`
