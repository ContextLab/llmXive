# Contracts & Validation Rules

## Data Contracts
- **Input**: CSV with `smiles`, `experimental_barrier`, `net_charge`.
- **Output**: CSV with `smiles`, `homo`, `lumo`, `mayer_order`, `charges_sum`.

## Physical Constraints
- **HOMO < LUMO**: Always true for stable molecules.
- **Charge Sum**: Sum of atomic charges must equal `net_charge` (within tolerance).
- **Barrier Range**: Experimental barriers must be positive.

## Error Handling
- **ConvergenceError**: Raised if DFTB+ or Psi4 fails to converge.
- **OOMError**: Raised if memory limit exceeded.
- **ValidationError**: Raised if output data violates physical constraints.
