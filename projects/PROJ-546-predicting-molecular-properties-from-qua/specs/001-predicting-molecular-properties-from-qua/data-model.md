# Data Model Specification

## Input Data
- Source: Zenodo (Experimental Barrier Dataset)
- Format: CSV
- Required Columns:
 - `smiles`: String (SMILES notation)
 - `experimental_barrier`: Float (kcal/mol)
 - `net_charge`: Integer

## Intermediate Data
- DFTB Descriptors (`descriptors_semi.csv`):
 - `smiles`: String
 - `homo`: Float (eV)
 - `lumo`: Float (eV)
 - `mayer_order`: Float
 - `charges_sum`: Float
 - `geometry_optimized`: Boolean
- DFT Descriptors (`descriptors_dft.csv`):
 - Same structure as DFTB, computed via Psi4.

## Output Data
- Model Weights: Pickle files (`.pkl`)
- Evaluation Reports: JSON (`reports/evaluation.json`)
- Sensitivity Analysis: CSV (`reports/sensitivity.csv`)
