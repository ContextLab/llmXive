# Data Model: Predicting Molecular Conformational Landscapes with Variational Autoencoders

## Overview

This document defines the data structures, schemas, and relationships used in the project. It ensures that all data artifacts (raw, processed, model outputs) are consistent and traceable.

## Core Entities

### 1. Molecule
Represents a chemical entity.
*   **Attributes**:
    *   `id` (str): Unique identifier (e.g., ZINC15 ID or generated UUID).
    *   `smiles` (str): Canonical SMILES string.
    *   `graph` (dict): RDKit graph representation (nodes, edges, features).
    *   `latent_vector` (list[float]): 64-dimensional vector from VAE encoder.
    *   `conformers` (list[Conformer]): List of associated conformers.
    *   `calculation_metadata` (dict): Metadata for the energy calculation (GFN2-xTB version, flags, convergence criteria) as per Constitution Principle VI.

### 2. Conformer
Represents a 3D geometry of a molecule.
*   **Attributes**:
    *   `id` (str): Unique identifier (e.g., `molecule_id_conformer_idx`).
    *   `molecule_id` (str): Foreign key to Molecule.
    *   `geometry` (list[list[float]]): 3D coordinates (N_atoms x 3).
    *   `xtb_energy` (float): Energy from GFN2-xTB (in Hartree or eV).
    *   `rank` (int): Rank based on `xtb_energy` (1 = lowest energy).

### 3. ModelCheckpoint
Serialized VAE weights.
*   **Attributes**:
    *   `path` (str): File path to `vae_checkpoint.pt`.
    *   `epoch` (int): Training epoch.
    *   `loss` (float): Final reconstruction loss.
    *   `config` (dict): Hyperparameters (latent_dim, learning_rate, etc.).

### 4. Metrics
Aggregated evaluation results.
*   **Attributes**:
    *   `vae_ranking` (dict): Spearman ρ, p-value, adjusted p-value.
    *   `baselines` (dict): ECFP4 and Random ρ values.
    *   `ablation_3d` (dict): ρ with 3D descriptors, Δρ.
    *   `sensitivity_analysis` (list): ρ and p-values for different α thresholds.
    *   `power_analysis` (dict): Minimum sample size, effect size, power.
    *   `workflow_success_rate` (float): Percentage of molecules where conformer generation and energy calculation succeeded (FR-011).

## Data Flow

1.  **Raw Data**: `data/raw/zinc_processed.parquet` (SMILES only).
2.  **Processed Data**:
    *   `data/processed/graphs.json` (Molecule graphs).
    *   `data/processed/conformers.json` (Geometry + Energy + `calculation_metadata`).
3.  **Model Output**: `data/processed/predictions.json` (Latent vectors + Predicted ranks).
4.  **Results**: `data/processed/metrics.json` (Spearman ρ, p-values, `workflow_success_rate`).

## Schema Definitions

See `contracts/` for formal YAML schemas.