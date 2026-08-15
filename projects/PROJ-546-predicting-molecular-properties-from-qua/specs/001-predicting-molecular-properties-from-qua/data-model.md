# Data Model: Predicting Molecular Properties from Quantum Chemical Calculations

## Entities

### Molecule
- **Definition**: A chemical structure defined by a SMILES string and a unique identifier.
- **Attributes**:
  - `molecule_id`: Unique string (e.g., "mol_001").
  - `smiles`: Canonical SMILES string.
  - `experimental_barrier`: Float (eV), the ground truth target.
  - `geometry_path`: Relative path to the optimized XYZ file.
  - `status`: Enum {`success`, `failed_after_retry`, `oom`, `structural_failure`}.

### Descriptor
- **Definition**: A computed quantum chemical property derived from the optimized geometry.
- **Attributes**:
  - `molecule_id`: Foreign key to Molecule.
  - `method`: Enum {`dftb+`, `psi4`}.
  - `HOMO_energy`: Float (eV).
  - `LUMO_energy`: Float (eV).
  - `mayer_bond_order`: Float (dimensionless, sum of Mayer bond orders).
  - `computed_at`: Timestamp.

### Confound
- **Definition**: A structural property of the molecule used to control for bias.
- **Attributes**:
  - `molecule_id`: Foreign key to Molecule.
  - `molecular_weight`: Float (g/mol).
  - `atom_count`: Integer.
  - `functional_groups`: List of strings (e.g., `["carbonyl", "hydroxyl"]`).

## Data Flow

1. **Input**: `data/raw/barriers.csv` (Zenodo).
2. **Preprocessing**:
   - Validate SMILES (RDKit).
   - Generate 3D coordinates.
3. **Geometry Optimization**:
   - Output: `data/optimized_geometries/{molecule_id}.xyz`.
   - Log failures to `logs/convergence_failures.log`.
4. **Descriptor Calculation**:
   - DFTB+: `data/descriptors_semi.csv`.
   - Psi4: `data/descriptors_dft.csv` (subset).
   - Confounds: `data/confounds.csv`.
5. **Modeling**:
   - Input: Descriptors + Confounds.
   - Output: `reports/evaluation.json`, `reports/sensitivity.csv`.

## File Schemas

### `data/raw/barriers.csv`
- **Source**: Zenodo.
- **Columns**: `molecule_id`, `smiles`, `experimental_barrier`.

### `data/descriptors_semi.csv`
- **Source**: DFTB+ calculation.
- **Columns**: `molecule_id`, `HOMO_energy`, `LUMO_energy`, `mayer_bond_order`.

### `data/descriptors_dft.csv`
- **Source**: Psi4 calculation.
- **Columns**: `molecule_id`, `HOMO_energy`, `LUMO_energy`, `mayer_bond_order`.

### `data/confounds.csv`
- **Source**: RDKit analysis.
- **Columns**: `molecule_id`, `molecular_weight`, `atom_count`, `functional_groups`.

### `logs/convergence_failures.log`
- **Format**: CSV.
- **Columns**: `molecule_id`, `timestamp`, `error_code`, `error_message`.

### `reports/evaluation.json`
- **Format**: JSON.
- **Keys**:
  - `semi_empirical_mae`: Float.
  - `dft_mae`: Float.
  - `t_statistic`: Float.
  - `p_value`: Float.
  - `null_hypothesis`: String.
  - `significance_level`: Float (0.05).
  - `models_compared`: List of strings.

### `reports/sensitivity.csv`
- **Format**: CSV.
- **Columns**: `cutoff`, `noise_sigma`, `top_3_descriptors`, `rank_correlation`.
