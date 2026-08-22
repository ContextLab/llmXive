# Data Model: Predicting Molecular Interactions in Protein-Ligand Complexes

## Overview

This document defines the data structures, schemas, and relationships used throughout the project. It ensures consistency between data ingestion, model training, and result reporting, adhering to the Constitution's Data Hygiene and Versioning principles.

## Key Entities

### MolecularGraph

Represents a single protein-ligand complex.

- **Attributes**:
  - `id`: Unique identifier (PDB ID + chain).
  - `nodes`: List of atom nodes.
    - `atom_type`: String (e.g., "C", "N", "O", "H").
    - `charge`: Float (formal charge).
    - `hydrophobicity`: Float (derived from atom type).
    - `coordinates`: List of 3 floats [x, y, z].
  - `edges`: List of edge connections.
    - `source`: Integer (node index).
    - `target`: Integer (node index).
    - `bond_type`: String (covalent, non-covalent).
    - `distance`: Float (Å).
  - `global_properties`:
    - `pKd`: Float (target variable).
    - `resolution`: Float (Å).
    - `water_flagged`: Boolean (true if water-mediated interaction detected).

### SubstructureCluster

Represents a group of high-importance substructures identified via clustering.

- **Attributes**:
  - `cluster_id`: Integer.
  - `centroid_coordinates`: List of 3 floats.
  - `member_count`: Integer.
  - `pharmacophore_id`: String (matched reference ID, or null).
  - `rmsd`: Float (overlap with pharmacophore).
  - `p_value`: Float (statistical significance).
  - `fdr_corrected_p`: Float (Benjamini-Hochberg adjusted).

### FeatureImportanceMap

Maps atom indices to their attribution scores.

- **Attributes**:
  - `atom_index`: Integer.
  - `score`: Float (Integrated Gradients score).
  - `interaction_type`: String (covalent, non-covalent).

### MemoryProfile

Records memory usage during data processing.

- **Attributes**:
  - `timestamp`: String (ISO 8601).
  - `peak_memory_mb`: Float (peak RAM usage).
  - `dataset_size_mb`: Float (size of raw dataset).
  - `graph_construction_overhead_mb`: Float (additional memory during graph building).
  - `total_memory_mb`: Float (sum of dataset and overhead).

### InferenceBenchmark

Records inference time per complex.

- **Attributes**:
  - `complex_id`: String.
  - `inference_time_ms`: Float.
  `hardware`: String (e.g., "CPU").

## Data Flow

1. **Ingestion**: Raw PDBbind data (`data/raw/pdbbind.parquet`) is streamed and converted to `MolecularGraph` objects.
2. **Processing**: Graphs are saved to `data/processed/` in a serialized format (e.g., `.pt` or `.pkl`).
3. **Training**: Graphs are loaded into the GNN; predictions are stored in `data/results/predictions.csv`.
4. **Interpretation**: Feature importance scores are generated and clustered; results stored in `data/results/motifs.json`.
5. **Validation**: Statistical tests are run; results stored in `data/results/statistical_validation.json`.
6. **Benchmarking**: Memory and inference metrics are stored in `data/results/memory_profile.json` and `data/results/inference_benchmark.json`.

## File Structure

```text
data/
├── raw/
│   └── pdbbind.parquet          # Original dataset (checksummed)
├── processed/
│   ├── graph_001.pt             # Serialized MolecularGraph
│   ├── graph_002.pt
│   └── ...
├── reference/
│   └── pharmacophores.json      # Reference pharmacophore definitions (T038a)
└── results/
    ├── predictions.csv          # Model predictions vs. actual pKd
    ├── sensitivity_analysis.json # 3D edge sensitivity results
    ├── motifs.json              # Clustered substructures
    ├── statistical_validation.json # Permutation test and FDR results
    ├── memory_profile.json      # Memory usage metrics
    └── inference_benchmark.json # Inference time metrics
```

## Data Hygiene

- **Checksums**: All files in `data/raw/` and `data/processed/` are checksummed (SHA-256) and recorded in the project state file.
- **Immutability**: Raw data is never modified. Derivations are written to new files.
- **Versioning**: Each artifact carries a content hash; state updates on change.
