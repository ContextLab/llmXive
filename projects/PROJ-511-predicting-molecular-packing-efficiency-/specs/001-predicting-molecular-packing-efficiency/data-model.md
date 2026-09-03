# Data Model: Predicting Molecular Packing Efficiency

## Overview
This document defines the data schemas and transformations for the molecular packing efficiency pipeline. All data artifacts are stored in `data/` and validated against `contracts/`.

## Entity Relationships

1.  **Raw CIF** (Downloaded) -> **Filtered Record** (JSON/CSV)
2.  **Filtered Record** -> **Feature Vector** (SMILES Embedding + 3D Descriptors)
3.  **Feature Vector** -> **Model Prediction** (Target: PC_raw)
4.  **Model Prediction** + **Ground Truth** -> **Validation Report**

## Dataset Schemas

### 1. Raw Download (JSONL)
Source: Verified COD JSONL (`cod/cod`).
*   `_cod_id`: string (Unique ID)
*   `_cell_length_a`, `_cell_length_b`, `_cell_length_c`: float
*   `_cell_angle_alpha`, `_cell_angle_beta`, `_cell_angle_gamma`: float
*   `_symmetry_space_group_name_H-M`: string
*   `_chemical_formula_sum`: string
*   `_chemical_structure_SMILES`: string (optional)
*   `_exptl_crystal_growth_temperature`: float (optional)

### 2. Intermediate CSV (`data/processed/full_feature_matrix.csv`)
*   `cod_id`: string
*   `smiles`: string (Canonical)
*   `smiles_source`: string ("extracted" or "generated")
*   `unit_cell_volume`: float (Å³)
*   `pc_raw`: float (Raw Packing Coefficient - **Primary Target**)
*   `cape`: float (Composition-Adjusted Packing Efficiency - **Diagnostic Only**)
*   `radius_of_gyration`: float (Å)
*   `asphericity`: float
*   `principal_moments`: string (JSON array of 3 floats)
*   `lattice_system`: string
*   `temperature_K`: float (or null)
*   `has_solvent`: boolean
*   `atom_count`: int (Non-H atoms - **Excluded from primary regression**)
*   `atom_type_counts`: string (JSON object, e.g., `{"C": 10, "N": 2}` - **Excluded from primary regression**)
*   `fingerprint_vector`: string (Base64 encoded or space-separated float list)

### 3. Model Output (`data/artifacts/model.pt`)
*   Serialized PyTorch state dict.
*   Metadata: `{"seed": 42, "train_split": 0.8, "params": <count>, "target": "pc_raw"}`.

### 4. Validation Report (`data/artifacts/validation_report.json`)
*   `mae`: float
*   `pearson_r`: float
*   `spearman_rho`: float
*   `shapiro_wilk_stat`: float
*   `shapiro_wilk_p`: float
*   `permutation_p_value`: float (10k shuffles)
*   `bonferroni_corrected_p`: float
*   `vif_flags`: list of strings (features with VIF > 5)
*   `sensitivity_results`: list of dicts (threshold, r, p)
*   `residual_composition_corr`: float (Correlation of residuals with atom counts)

## Transformation Logic

1.  **PC_raw Calculation**:
    $$ \text{PC}_{\text{raw}} = \frac{\text{Unit‑cell volume}}{\sum_{i}{V_{\text{vdW},i}}} $$
    Where $V_{\text{vdW},i}$ are atomic van der Waals volumes taken from Bondi radii.

2.  **CAPE Calculation (Diagnostic)**:
    $$ \text{CAPE} = \frac{\text{PC}_{\text{raw}}}{\frac{1}{N_{\text{atoms}}}\sum_{i}{V_{\text{vdW},i}}} $$
    *Note: CAPE is calculated for diagnostic reporting only. It is NOT used as the regression target to avoid tautology.*

3.  **SMILES Generation**:
    If `_chemical_structure_SMILES` is missing:
    *   Parse CIF to 3D Mol object (RDKit).
    *   `MolToSmiles(Mol, isomericSmiles=True)`.
    *   Flag as "generated".

4.  **3D Descriptors**:
    *   `radius_of_gyration`: $\sqrt{\frac{1}{N} \sum |r_i - r_{cm}|^2}$
    *   `asphericity`: $\frac{3}{2} \frac{\lambda_3 - \lambda_1}{\lambda_1 + \lambda_2 + \lambda_3}$ (where $\lambda$ are eigenvalues of gyration tensor).

## Constraints
*   **Atom Count Filter**: Exclude records where `atom_count` > 50.
*   **Volume Sanity**: Exclude records where `unit_cell_volume` < 10 or > 100000.
*   **PC_raw Bounds**: Flag records where `PC_raw` < 0 or > 10 (likely error).
*   **Schema Validation**: Phase 0 includes a check to ensure all required fields (`_cell_volume`, etc.) are present in the source dataset before proceeding.
