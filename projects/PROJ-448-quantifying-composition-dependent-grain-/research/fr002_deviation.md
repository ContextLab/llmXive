# Deviation Report: FR-002 Implementation

## Original Requirement (FR-002)
"Compute segregation energies using Quantum ESPRESSO."

## Deviation Summary
For the purpose of CI execution and pipeline validation, the "compute" step has been replaced with "load pre-computed DFT energies from verified literature sources".

## Justification
1. **CI Constraints**: The CI environment lacks the GPU resources and time limit (6h) required for DFT calculations using Quantum ESPRESSO.
2. **Pipeline Validation**: The primary goal is to validate the thermodynamic and segregation profile generation logic (McLean isotherm, cooperative effects) rather than the DFT computation itself.
3. **Data Availability**: Pre-computed DFT energies are available from literature (or placeholders are used per T018a if not found).

## Reference
This deviation is documented and authorized by the spec amendment `research/spec_amendment_fr002.md`.

## Impact
- The pipeline will load energies from `data/raw/dft_energies.json` instead of running `Quantum ESPRESSO`.
- Results are consistent with the methodology but rely on external data for the energy values.
