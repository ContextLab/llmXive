# Data Model: Predicting Molecular Packing Efficiency in Crystals

## 1. Data Entities

### 1.1 Raw Input (COD CIF Archive)
-   **Source**: `ftp://ftp.ccdc.cam.ac.uk/pub/structures/cod/` (Official COD FTP).
-   **Format**: CIF (Crystallographic Information File).
-   **Key Fields**:
    -   `_cod_id`: String (Unique identifier).
    -   `_cell_length_a`, `_cell_length_b`, `_cell_length_c`: Float (Å).
    -   `_cell_angle_alpha`, `_cell_angle_beta`, `_cell_angle_gamma`: Float (deg).
    -   `_chemical_formula_sum`: String (e.g., "C10 H8 O2").
    -   `_atom_site_label`: Array (Atomic labels).
    -   `_atom_site_type_symbol`: Array (Element symbols).
    -   `_atom_site_fract_x`, `_atom_site_fract_y`, `_atom_site_fract_z`: Arrays (Fractional coordinates).
    -   `_chemical_structure_SMILES`: String (Optional).

### 1.2 Intermediate (Dataset CSV)
-   **File**: `data/processed/dataset.csv`
-   **Schema**:
    -   `cod_id`: String (Primary Key).
    -   `smiles`: String (Canonical SMILES, generated from 2D graph).
    -   `smiles_source`: Enum ["extracted", "generated"].
    -   `unit_cell_volume`: Float (Å³).
    -   `sum_vdw_volume`: Float (Å³).
    -   `pc_raw`: Float (Target Variable).
    -   `n_atoms`: Int (Non-hydrogen count).
    -   `mean_atomic_volume`: Float (Sum V_vdw / N_atoms, Covariate).
    -   `cape`: Float (Diagnostic, PC_raw / mean_atomic_volume).
    -   `radius_of_gyration`: Float (From experimental coords).
    -   `asphericity`: Float (From experimental coords).
    -   `principal_moments`: String (Comma-separated list of 3 floats, from experimental coords).
    -   `lattice_system`: String (e.g., "monoclinic").
    -   `temperature_K`: Float or Null.
    -   `has_solvent`: Boolean.
    -   `atom_counts`: String (Comma-separated counts of C, N, O, S, etc.).

### 1.3 Feature Matrix (Numpy/Parquet)
-   **File**: `data/processed/feature_matrix.parquet`
-   **Schema**:
    -   `smiles_embedding`: Array (Float, fixed length, e.g., 768).
    -   `radius_of_gyration`: Float.
    -   `asphericity`: Float.
    -   `moments_1`, `moments_2`, `moments_3`: Float.
    -   `lattice_one_hot`: Array (Float, length = num_lattice_types).
    -   `has_solvent`: Float (0/1).
    -   `temperature_scaled`: Float.
    -   `mean_atomic_volume`: Float.
    -   `atom_counts_vector`: Array (Float, counts of each element).
    -   `target_pc_raw`: Float.

### 1.4 Model Artifacts
-   **File**: `results/model.pt`
-   **Content**: PyTorch state dict for the 2-layer MLP.
-   **Metadata**: Hyperparameters, seed, training timestamp.

### 1.5 Validation Report
-   **File**: `results/validation_report.md`
-   **Content**: Markdown table of metrics, p-values, VIF diagnostics.

## 2. Data Flow Diagram

```mermaid
graph TD
    A[COD CIF Archive] -->|Stream & Filter| B(Intermediate DataFrame)
    B -->|Extract 2D Graph| C{SMILES Source?}
    C -->|Extracted| D[Use Metadata]
    C -->|Missing| E[Generate 2D from CIF bonds -> SMILES]
    D --> F[Feature Calculation]
    E --> F
    F -->|Volume, Descriptors from EXP 3D| G[Dataset CSV]
    G -->|Embed & Augment| H[Feature Matrix]
    H -->|Train Baseline (3D Only)| I[Geometry Model]
    H -->|Train Full (3D+SMILES)| J[Full Model]
    I -->|Compare| K[Incremental Signal]
    J -->|Evaluate| L[Validation Report]
    L -->|HTML| M[Final Report]
```

## 3. Constraints & Validations

-   **Atom Count**: Must be $\le 50$ (Non-H).
-   **Volume**: $V_{cell} > 0$.
-   **PC_raw**: Must be positive.
-   **SMILES**: Must be valid RDKit molecule (sanity check).
-   **Missing Data**: `temperature_K` and `has_solvent` can be Null/False, but `smiles` and `pc_raw` cannot.
-   **3D Coordinates**: All 3D descriptors must be derived from **experimental** CIF coordinates (no gas-phase minimization). SMILES must be derived from **2D** graphs only.