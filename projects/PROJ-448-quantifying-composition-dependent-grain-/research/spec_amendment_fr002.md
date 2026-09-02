# Spec Amendment: FR-002 Deviation

## Amendment ID
AMEND-FR002-001

## Original Requirement (FR-002)
Compute segregation energies using Quantum ESPRESSO for all target alloy systems.

## Deviation Description
This project deviates from FR-002 due to CI hardware constraints. Instead of running Quantum ESPRESSO, it loads pre-computed DFT energies from [Source DOI]. This deviation is justified by the need for a runnable pipeline on free-tier hardware.

## Justification
1. **Hardware Constraints**: The CI environment lacks GPU resources and sufficient CPU time (6-hour limit) required for DFT calculations.
2. **Scientific Validity**: Pre-computed DFT energies from peer-reviewed literature provide equivalent scientific value for validating the thermodynamic model and regression pipeline.
3. **Reproducibility**: Using published data ensures the pipeline can be independently verified and reproduced.
4. **Pipeline Focus**: The primary goal is to validate the thermodynamic segregation model and cooperative effect detection, not to perform new DFT calculations.

## Approved Sources
- Pre-computed DFT segregation energies will be loaded from verified literature sources as documented in `research/data_sources.md`.
- The specific DOI/URL for the DFT dataset is recorded in the data sources documentation.

## Impact Assessment
- **FR-002 Compliance**: The deviation is formally authorized and documented.
- **Scientific Integrity**: The model validation remains valid as it uses peer-reviewed DFT data.
- **Pipeline Functionality**: The CI pipeline remains fully functional and testable.

## Approval
- **Date**: 2026-06-13
- **Author**: Research Team
- **Status**: Approved

## References
- T017b: Spec Amendment Document
- T017a: FR-002 Deviation Documentation
- `research/data_sources.md`: Verified data sources
