# Data Model: Predicting Molecular Properties from Quantum Chemical Calculations

## Overview

This document defines the data structures, schemas, and transformation logic used in the project. All data flows from raw sources to processed artifacts, with strict versioning and checksumming.

## Entities

### 1. Molecule
Represents a chemical entity.
- **Attributes**:
  - `smiles` (string): Canonical SMILES representation.
  - `molecule_id` (string): Unique identifier (hash of SMILES).
  - `dft_reference_energy` (float): DFT-calculated conformational energy in kcal/mol (from dataset).
  - `status` (string): "valid", "outlier", "failed_calc".

### 2. Descriptor
Electronic structure property calculated for a molecule.
- **Attributes**:
  - `molecule_id` (string): FK to Molecule.
  - `method` (string): "DFTB" or "DFT".
  - `homo_energy` (float): HOMO energy in eV.
  - `lumo_energy` (float): LUMO energy in eV.
  - `mulliken_charge_sum` (float): Sum of Mulliken charges (should be ~0 or net charge).
  - `mayer_bond_order` (float): Average or specific bond order (depends on calculation).
  - `calc_time` (float): CPU time in seconds.

### 3. ModelArtifact
Trained Random Forest model and metadata.
- **Attributes**:
  - `model_id` (string): Unique ID.
  - `method` (string): "DFTB" or "DFT".
  - `mae` (float): Mean Absolute Error on validation.
  - `feature_importance` (dict): Mapping of feature name to importance score.
  - `random_seed` (int): Pinning seed.

## Data Flow

1.  **Raw Data**: `data/raw/maestro_2004_synthetic.zip` (Downloaded from verified URL).
2.  **Parsed Data**: `data/processed/molecules.csv` (SMILES, DFT-calculated reference energies).
3.  **Descriptors (Semi-Empirical)**: `data/processed/descriptors_dftb.csv`.
4.  **Descriptors (High-Level)**: `data/processed/descriptors_dft.csv`.
5.  **Model Outputs**: `data/processed/model_results.json`.

## Constraints & Validation

- **SMILES Validation**: All SMILES must be valid RDKit molecules.
- **Charge Conservation**: Sum of Mulliken charges must be within ±0.01 of the net charge.
- **Energy Ranges**: HOMO/LUMO must be within physically plausible ranges (e.g., -20 to +10 eV).
- **Outlier Handling**: Molecules with DFT-calculated reference energies > 1.5 IQR above Q3 are flagged and excluded from training but retained in logs.