# Data Model Specification

## Raw Data
- **Source**: Zenodo (Experimental Barrier Heights)
- **Format**: CSV
- **Fields**:
 - `molecule_id`: Unique identifier (string)
 - `smiles`: Canonical SMILES string
 - `experimental_barrier`: Reaction barrier height in kcal/mol (float)

## Processed Data
- **Semi-Empirical Descriptors** (`data/descriptors_semi.csv`)
 - `molecule_id`
 - `smiles`
 - `HOMO_energy` (eV)
 - `LUMO_energy` (eV)
 - `mayer_bond_order` (float)
 - `total_energy` (eV)
 - `geometry_file`: Path to XYZ file in `data/optimized_geometries/`

- **DFT Descriptors** (`data/descriptors_dft.csv`)
 - Same schema as semi-empirical, but derived from Psi4/B3LYP.

## Logs
- `logs/convergence_failures.log`: JSON lines of failed DFTB+ runs.
- `logs/dftb_execution.log`: JSON lines of execution metrics (wall_time, peak_memory).
- `logs/structural_failures.log`: CSV of molecules with invalid physical ranges.
