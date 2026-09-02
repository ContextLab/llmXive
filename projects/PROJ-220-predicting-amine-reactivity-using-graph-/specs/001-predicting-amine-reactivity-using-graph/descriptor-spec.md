# Descriptor Calculation Specification

## Overview
This document specifies the implementation of molecular descriptors required for
the amine reactivity prediction pipeline, specifically for the correlation test
defined in SC-003.

## Required Descriptors

### 1. Hammett Sigma Constants (T007a)
- **Function**: `compute_hammett(smiles: str)`
- **Outputs**:
 - `sigma_p`: Para substituent constant
 - `sigma_m`: Meta substituent constant
 - `sigma_plus`: Sigma plus (for electron-donating resonance)
 - `sigma_minus`: Sigma minus (for electron-withdrawing resonance)
- **Source**: Lookup table for common substituents, estimation via Mordred for others.
- **Validation**: Values must be non-NaN for all valid inputs. [UNRESOLVED-CLAIM: c_55cb03bf — status=not_enough_info]

### 2. Taft and Charton Parameters (T007b)
- **Function**: `compute_taft_charton(smiles: str)`
- **Outputs**:
 - `es`: Taft steric parameter
 - `es_s`: Taft steric parameter (simplified)
 - `charton_nu`: Charton steric parameter
- **Source**: Lookup table or molecular volume estimation.

### 3. Verloop Parameters (T007c)
- **Function**: `compute_verloop(smiles: str)`
- **Outputs**:
 - `b1`: Minimum width of substituent
 - `b5`: Maximum width of substituent
- **Source**: 3D molecular conformation analysis.

### 4. Molar Refractivity (T007d)
- **Function**: `compute_mr(smiles: str)`
- **Outputs**:
 - `mr`: Molar Refractivity
- **Source**: RDKit `Descriptors.MolMR`.

### 5. Aggregated Vector (T007e)
- **Function**: `aggregate_independent_vector(smiles_list: List[str])`
- **Outputs**: List of dictionaries containing all 10 descriptors per molecule.
- **Purpose**: Single input for the correlation test (SC-003).

## Implementation Notes
- All functions must raise `ValueError` for invalid SMILES.
- All returned values must be `float` and non-NaN for valid inputs.
- Lookup tables must be sourced from standard physical organic chemistry references.
- Fallback estimation methods must be documented and robust.

## Testing
- Unit tests must verify:
 - Correct dictionary structure.
 - Non-NaN values for all descriptors.
 - Accuracy against known literature values for common substituents.
 - Proper handling of invalid inputs.