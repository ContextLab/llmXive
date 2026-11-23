# Data Model: Predicting Molecular Surface Charge Distribution

## Overview

This document defines the data schemas for the molecular charge prediction pipeline. The data flows from raw QM9 parquet files through a processing pipeline to model inputs and predictions.

## Entity Definitions

### Molecule
A single molecular instance in the dataset.
- **ID**: Unique identifier (string or integer).
- **Atoms**: List of atoms.
- **Coordinates**: 3D coordinates (x, y, z) for each atom.
- **Charges**: Ground truth Merz-Kollman charges for each atom.
- **Scaffold**: Bemis-Murcko scaffold identifier (string hash).

### ModelOutput
The prediction result for a molecule.
- **MoleculeID**: Reference to the input molecule.
- **PredictedCharges**: List of predicted scalar charges.
- **ActualCharges**: List of ground truth charges.
- **Errors**: List of absolute errors per atom.
- **AggregateMetrics**: MAE, RMSE, R for the molecule.

## Schema Definitions

### Dataset Schema (Input)
The raw data from QM9 (parquet) is expected to have the following columns:
- `mol_id`: string
- `atoms`: list of integers (atomic numbers)
- `positions`: list of lists (float32, [x, y, z])
- `charges_merkollman`: list of float32
- `connectivity`: list of lists (bond types)
- `scaffold`: string (derived)

### Model Input Tensor Schema
- **AtomicNumbers**: Shape `(N_atoms,)`, dtype `int64`.
- **Positions**: Shape `(N_atoms, 3)`, dtype `float32`.
- **EdgeIndex**: Shape `(2, N_edges)`, dtype `int64`.
- **EdgeAttr**: Shape `(N_edges,)`, dtype `float32` (bond types).

### Output Schema (JSON)
The final evaluation report will be a JSON object containing:
- `experiment_id`: string
- `model_type`: string ("3D-GNN" or "2D-GNN")
- `metrics`:
  - `mae`: float
  - `rmse`: float
  - `pearson_r`: float
- `samples_processed`: integer
- `timestamp`: ISO8601

## Data Flow

1. **Ingestion**: `loader.py` reads parquet, filters nulls, normalizes coordinates.
2. **Splitting**: `splits.py` computes Bemis-Murcko scaffolds and assigns train/val/test indices.
3. **Preprocessing**: Coordinates centered; charges standardized (optional, but recommended for GNNs).
4. **Training**: Batches of `(AtomicNumbers, Positions, EdgeIndex, Charges)` fed to model.
5. **Evaluation**: Predictions compared to ground truth; metrics aggregated.

## Constraints

- **Coordinate Normalization**: All coordinates MUST be centered to the molecule's center of mass before training (Constitution Principle VI).
- **Charge Scaling**: Charges MAY be scaled to unit variance if the model struggles with magnitude, but this must be recorded in the artifact.
- **Missing Values**: Any molecule with missing `charges_merkollman` for any atom is discarded.