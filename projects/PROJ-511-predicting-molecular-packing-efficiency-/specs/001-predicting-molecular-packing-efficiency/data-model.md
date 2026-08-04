# Data Model: Predicting Molecular Packing Efficiency in Crystals

## Overview

This document describes the data structures used in the pipeline, from raw CIF downloads to the final processed dataset and model outputs.

## Entities

### 1. Raw CIF File
*   **Format**: Crystallographic Information File (`.cif`)
*   **Source**: Crystallography Open Database (COD)
*   **Key Fields**:
    *   `_chemical_formula_sum`: Molecular formula.
    *   `_cell_length_a`, `_cell_length_b`, `_cell_length_c`, `_cell_angle_alpha`, `_cell_angle_beta`, `_cell_angle_gamma`: Unit cell parameters.
    *   `_atom_site_label`, `_atom_site_type_symbol`, `_atom_site_fract_x`, `_atom_site_fract_y`, `_atom_site_fract_z`: Atomic coordinates.
    *   `_chemical_structure_SMILES`: Optional SMILES string (if provided by depositor).
    *   `_space_group_IT_number`: Lattice system.
    *   `_exptl_crystal_growth_temperature`: Measurement temperature.

### 2. Processed Dataset (`dataset.csv`)
*   **Format**: CSV
*   **Columns**:
    *   `cod_id`: Unique COD identifier (string).
    *   `smiles`: Canonical SMILES string (string).
    *   `smiles_source`: "extracted" or "generated" (string).
    *   `unit_cell_volume`: Calculated unit cell volume in Å³ (float).
    *   `vdw_volume_sum`: Sum of Bondi van der Waals volumes in Å³ (float).
    *   `packing_coefficient`: Raw PC = `unit_cell_volume` / `vdw_volume_sum` (float).
    *   `cape`: Composition-Adjusted Packing Efficiency (float).
    *   `num_non_hydrogen_atoms`: Count of non-H atoms (int).
    *   `radius_of_gyration`: Radius of gyration in Å (float).
    *   `asphericity`: Asphericity descriptor (float).
    *   `principal_moment_1`: Principal moment of inertia 1 (float).
    *   `principal_moment_2`: Principal moment of inertia 2 (float).
    *   `principal_moment_3`: Principal moment of inertia 3 (float).
    *   `lattice_system`: Crystal system (string).
    *   `temperature_K`: Measurement temperature in Kelvin (float, or NaN).
    *   `has_solvent`: Boolean flag for solvent presence (bool).
    *   `atom_type_counts`: Comma-separated counts of each atom type (string).

### 3. Model Weights (`mlp.pt`)
*   **Format**: PyTorch state dictionary (`.pt`)
*   **Contents**: Weights and biases for the 2-layer MLP.
*   **Metadata**: Training configuration (seed, learning rate, epochs) stored in a separate JSON file.

### 4. Validation Report (`validation_report.json`)
*   **Format**: JSON
*   **Schema**: `contracts/validation_report.schema.yaml`
*   **Contents**:
    *   `mae`: Mean Absolute Error (float).
    *   `pearson_r`: Pearson correlation coefficient (float).
    *   `spearman_rho`: Spearman rank correlation (float).
    *   `shapiro_wilk_p`: p-value from Shapiro-Wilk test (float).
 * `permutation_test_p`: Two-sided p-value from [deferred] shuffles (float).
    *   `vif_flags`: List of features with VIF > 5 (list of strings).
    *   `partial_corr`: Partial correlation coefficient (float).

## Data Flow

1.  **Ingestion**: `download_cif.py` fetches CIFs → `data/raw_cif/`.
2.  **Processing**: `parse_cif.py` reads CIFs → computes features → writes `data/dataset.csv`.
3.  **Training**: `train.py` reads `dataset.csv` → trains model → writes `models/mlp.pt`.
4.  **Evaluation**: `evaluate.py` reads `dataset.csv` and `models/mlp.pt` → computes metrics → writes `results/validation_report.json`.
5.  **Reporting**: `report.py` reads `validation_report.json` and `dataset.csv` → generates `results/report.html`.
