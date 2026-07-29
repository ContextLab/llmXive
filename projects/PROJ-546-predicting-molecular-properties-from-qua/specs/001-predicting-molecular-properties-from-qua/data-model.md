# Data Model Specification

## Input Data
- **Source**: Zenodo (Experimental Barrier Dataset)
- **Format**: CSV
- **Columns**:
 - `smiles`: String (Molecular structure in SMILES format)
 - `experimental_barrier`: Float (Barrier height in kcal/mol)

## Derived Data: Semi-Empirical (DFTB+)
- **File**: `data/processed/descriptors_semi.csv`
- **Columns**:
 - `smiles`: String
 - `homo`: Float (eV)
 - `lumo`: Float (eV)
 - `mayer_bond_order`: Float
 - `net_charge`: Float
 - `convergence_status`: String (OK/FAILED)

## Derived Data: High-Level DFT
- **File**: `data/processed/descriptors_dft.csv`
- **Columns**:
 - `smiles`: String
 - `homo`: Float (eV)
 - `lumo`: Float (eV)
 - `mayer_bond_order`: Float
 - `net_charge`: Float
 - `convergence_status`: String (OK/FAILED)

## Model Outputs
- **File**: `data/processed/model_outputs/evaluation.json`
- **Structure**:
 ```json
 {
 "mae_semi": 0.0,
 "mae_dft": 0.0,
 "p_value": 0.0,
 "speedup_ratio": 0.0,
 "threshold_flags": {
 "semi_mae_high": false,
 "speedup_low": false
 }
 }
 ```
