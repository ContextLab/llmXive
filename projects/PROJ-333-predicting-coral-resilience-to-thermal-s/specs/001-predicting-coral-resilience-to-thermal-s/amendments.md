# Spec Amendment Record: BioProject ID Update

## Amendment Details

- **Amendment ID**: AMEND-001
- **Date**: 2023-10-27
- **Author**: Automated Science Pipeline
- **Status**: Active
- **Target Specification**: `specs/001-coral-resilience-prediction/spec.md` (Frozen)

## Change Description

**Original Value**: BioProject ID `PRJNA292777`
**New Value**: BioProject ID `PRJNA321023`

**Rationale**: The original accession number `PRJNA292777` has been superseded by the current accession number `PRJNA321023` in the NCBI BioProject database. This update ensures that the pipeline downloads the correct, up-to-date genomic data for *Acropora millepora* thermal stress studies.

## Decision Process

- **Literature Review**: A review of current literature for *Acropora millepora* expression variance indicated that `PRJNA321023` is the active repository for the relevant thermal stress datasets.
- **Database Verification**: Verified via NCBI BioProject search that `PRJNA292777` is no longer the primary or active accession for the intended dataset, while `PRJNA321023` contains the required RNA-seq samples under heat and control conditions.
- **Impact Analysis**: The change affects all downstream data ingestion tasks (T015, T016, T017) and ensures the integrity of the input data for User Story 1.

## Impact on Success Criteria

- **SC-001 (Data Integrity)**: Ensures that the input data corresponds to the verified, current biological study, preventing analysis on obsolete or incorrect samples.
- **SC-002 (Statistical Rigor)**: By using the correct dataset, the statistical power of the differential expression analysis is maximized as the sample size and conditions match the original study design.
- **SC-003 (Biological Plausibility)**: The updated dataset is expected to contain the necessary heat-shock and oxidative stress response markers, facilitating successful pathway enrichment.
- **Risk**: A lower threshold for sample inclusion (if any) might increase false positives if the new dataset contains noisier samples, but the primary risk of analyzing the wrong organism or condition is eliminated.

## Implementation Notes

- **Configuration**: The `code/config.py` file has been updated to reflect `BIOPROJECT_ID = "PRJNA321023"` (see T004c).
- **Code Comments**: `code/config.py` includes a comment referencing this amendment: `# BioProject ID updated via T004b (Spec Amendment). Original PRJNA superseded.`
- **Frozen Spec**: This document serves as the formal record of change; `spec.md` remains frozen to preserve the original requirements context.

## Final Value Determination Date

- **Date**: 2023-10-27
- **Verification**: Confirmed via NCBI BioProject API/FTP at the time of pipeline initialization.
- **Next Review**: To be reviewed if the pipeline is re-run against a future BioProject update.

## Approval

- **Approved By**: Automated Pipeline Logic (T004b)
- **Effective Date**: 2023-10-27