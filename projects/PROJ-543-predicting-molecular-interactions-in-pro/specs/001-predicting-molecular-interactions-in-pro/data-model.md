# Data Model: Predicting Molecular Interactions in Protein-Ligand Complexes

## Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to model output and interpretability results. All data is versioned and checksummed.

## Core Entities

### 1. MolecularGraph (Internal Representation)
A heterogeneous graph representing a protein-ligand complex.
- **Nodes**:
  - `atom_type`: Integer (mapped from element symbol, e.g., C=6, N=7, O=8).
  - `charge`: Float (formal charge).
  - `hybridization`: Integer (SP, SP2, SP3, etc.).
  - `hydrophobicity`: Float (calculated logP contribution).
  - `coordinates`: List[float, float, float] (3D x, y, z).
  - `is_ligand`: Boolean (True if part of the ligand, False if protein).
- **Edges**:
  - `edge_type`: String ("covalent", "non-covalent", "water-mediated").
  - `distance`: Float (Euclidean distance in Å).
  - `source_node`: Integer (index).
  - `target_node`: Integer (index).
- **Global Properties**:
  - `complex_id`: String (PDB ID + chain).
  - `pKd`: Float (experimental binding affinity).
  - `resolution`: Float (Å).
  - `water_flagged`: Boolean (True if water-mediated interaction detected via heuristic).

### 2. FeatureImportanceMap
Output of Integrated Gradients.
- `complex_id`: String.
- `atom_importance`: List[float] (score for each atom).
- `interaction_importance`: List[float] (score for each edge, if computed).
- `baseline`: String (e.g., "zero", "mean").

### 3. SubstructureCluster
Output of DBSCAN clustering.
- `cluster_id`: Integer.
- `centroid`: List[float, float, float].
- `member_count`: Integer.
- `member_complex_ids`: List[String].
- `pharmacophore_match`: String (ID of matched pharmacophore, or "None").
- `rmsd`: Float (RMSD to matched pharmacophore).
- `p_value`: Float (raw p-value from permutation test).
- `fdr_q_value`: Float (Benjamini-Hochberg corrected).
- `is_significant`: Boolean (True if fdr_q_value < 0.01).

## Data Flow

1.  **Raw Data**: `data/raw/pdbbind.parquet` (Downloaded from Hugging Face).
2.  **Processed Graphs**: `data/processed/graphs/` (Directory containing one `.pt` or `.json` file per complex).
    - Filenames: `{complex_id}_graph.json`.
3.  **Model Artifacts**: `data/results/model/`
    - `best_model.pt` (PyTorch state dict).
    - `training_log.json` (Epoch, loss, val_loss).
4.  **Interpretability Results**: `data/results/interpret/`
    - `importance_maps.json` (Aggregated importance scores).
    - `motif_clusters.json` (Cluster definitions and statistics).
    - `sensitivity_analysis.json` (Edge count variance vs. cutoff distance).
    - `metrics.json` (SC-001, SC-003 metrics).

## Data Hygiene & Versioning

- **Checksums**: Every file in `data/raw/` and `data/processed/` is checksummed (SHA-256) and recorded in `state/projects/...yaml`.
- **Immutability**: Raw data is never modified. All transformations (graph construction, filtering) produce new files in `data/processed/`.
- **PII**: None expected in PDBbind structural data.

## Schema Definitions

The project uses the following schemas (detailed in `contracts/`):
- `dataset.schema.yaml`: Validates the raw/processed input data.
- `graph.schema.yaml`: Validates the internal graph structure.
- `result.schema.yaml`: Validates the final model and motif results.
