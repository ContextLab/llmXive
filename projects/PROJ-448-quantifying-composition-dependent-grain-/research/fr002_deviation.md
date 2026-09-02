# FR-002 Deviation Documentation

## Overview
This document explicitly documents the deviation from the original specification requirement FR-002, which mandated computing segregation energies using Quantum ESPRESSO.

## Deviation Statement
Instead of computing segregation energies using Quantum ESPRESSO, this project loads pre-computed DFT energies from verified literature sources. Additionally, a Reduced CALPHAD Parameter Set is used due to CI constraints (no GPU, 6-hour limit).

## Justification

### Hardware Constraints
The continuous integration (CI) environment has the following limitations:
- No GPU resources available
- CPU time limited to 6 hours per run
- Memory constraints (~7 GB RAM)

Running full DFT calculations for multiple alloy systems would exceed these constraints by orders of magnitude.

### Scientific Rationale
1. **Model Validation Focus**: The primary objective is to validate the thermodynamic segregation model (McLean isotherm) and detect cooperative effects in multicomponent systems. This can be achieved using pre-computed DFT energies from peer-reviewed literature.

2. **Data Quality**: Published DFT datasets undergo rigorous peer review and provide reliable reference values for model validation.

3. **Pipeline Reproducibility**: Using static, published data ensures the pipeline is fully reproducible and testable in CI environments.

### Operational Necessity
The "compute" step using Quantum ESPRESSO is deferred to HPC resources in a separate branch or workflow. The current pipeline validates the methodology and logic using surrogate data.

## Single Source of Truth
This document references `research/spec_amendment_fr002.md` as the Single Source of Truth for the deviation. All implementation decisions regarding FR-002 must align with that document.

## Implementation Details
- **DFT Energy Loading**: The `code/services/surrogate_service.py` module loads pre-computed DFT energies from `data/raw/dft_energies.json`.
- **CALPHAD Parameters**: A reduced set of CALPHAD parameters is used, focusing on binary and essential ternary interactions.
- **Error Handling**: If the DFT data file is missing, the pipeline halts with a `DataNotFoundError`.

## Verification
The deviation has been verified through:
1. Successful pipeline execution on CI with pre-computed data
2. Validation of model outputs against literature expectations
3. Formal approval via the spec amendment process (T017b)

## Future Work
Once the methodology is validated, full DFT calculations will be performed on HPC resources to generate system-specific energies for final scientific publication.

## References
- Spec Amendment: `research/spec_amendment_fr002.md`
- Data Sources: `research/data_sources.md`
- T017b: Spec Amendment Task
- T017a: Deviation Documentation Task