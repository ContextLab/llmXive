# Data Model: Predicting Molecular Crystal Packing

## Entity-Relationship Overview

The data model consists of three primary entities: `Molecule`, `CrystalStructure`, and `ModelResult`.

### 1. Molecule
Represents the chemical entity.
- **Attributes**:
  - `id`: Unique string (COD ID).
  - `smiles`: String (canonical).
  - `molecular_weight`: Float (Da).
  - `formula`: String.
  - `volume`: Float (Å³, computed).
  - `surface_area`: Float (Å², computed).
  - `dipole_moment`: Float (Debye, computed).
  - `h_bond_donor_count`: Integer.
  - `h_bond_acceptor_count`: Integer.
  - `polar_surface_area`: Float (Å², computed).
  - `missing_data_flag`: Boolean (True if any auxiliary descriptor was imputed).

### 2. CrystalStructure
Represents the experimental lattice.
- **Attributes**:
  - `id`: Unique string (matches Molecule ID).
  - `unit_cell_volume`: Float (Å³, from CIF).
  - `space_group`: String.
  - `packing_coefficient`: Float (Derived: `volume` / `unit_cell_volume`).
  - `interaction_type`: String (e.g., "H-bond", "Van der Waals", "Heuristic Proxy").

### 3. ModelResult
Represents the output of a training run.
- **Attributes**:
  - `model_type`: String ("RandomForest", "GradientBoosting", "MeanBaseline", "Control_NoVolume").
  - `hyperparameters`: JSON object.
  - `r_squared`: Float.
  - `mae`: Float.
  - `rmse`: Float.
  - `feature_importance`: Array of floats (Permutation Importance).
  - `p_value_vs_baseline`: Float.
  - `bonferroni_corrected_p`: Float.

## Data Flow

1. **Raw Input**: CIF files from COD.
2. **Processed**: `data/processed/descriptors.csv` (Molecule + CrystalStructure attributes merged, with missing data flags).
3. **Model Input**: `data/processed/train.csv`, `val.csv`, `test.csv` (stratified by `packing_coefficient`).
4. **Output**: `results/metrics.json`, `results/feature_importance.png`, `results/sensitivity_report.md`.
