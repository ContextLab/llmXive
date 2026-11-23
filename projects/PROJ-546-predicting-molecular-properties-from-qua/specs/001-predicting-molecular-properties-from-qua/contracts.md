# Contracts and Validation Rules

## Data Validation Contracts
- **Input CSV**: Must contain columns `smiles`, `experimental_barrier`.
- **Descriptor CSV**: Must contain `HOMO_energy`, `LUMO_energy`, `mayer_bond_order`.
- **Physical Range**: `HOMO_energy < LUMO_energy` for all valid entries.

## Model Contracts
- **Training**: 5-fold cross-validation.
- **Evaluation**: MAE must be reported in kcal/mol.
- **Threshold**: Semi-empirical MAE ≤ 2.0 kcal/mol (spec US2).

## Execution Contracts
- **Convergence**: Failures must be logged, not raise unhandled exceptions.
- **Memory**: OOM events must be detected and logged.
- **Atomicity**: Output files (JSON/CSV) must be written atomically to prevent partial writes.
