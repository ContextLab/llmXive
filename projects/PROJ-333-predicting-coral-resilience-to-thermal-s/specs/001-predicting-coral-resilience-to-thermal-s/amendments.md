# Formal Spec Amendment Record

## Amendment Metadata
- **Amendment ID**: AMEND-001
- **Date**: 2023-10-27
- **Author**: llmXive Research Pipeline
- **Status**: Approved
- **Related Tasks**: T004b, T004c, T015, T018

## Change Description
**Original Value**: BioProject ID `PRJNA292777`
**New Value**: BioProject ID `PRJNA321023`

**Rationale**:
The original accession number `PRJNA292777` has been superseded. Literature review and NCBI database verification confirm that `PRJNA321023` is the current, active accession number for the *Acropora millepora* thermal stress expression dataset. This update ensures the pipeline accesses the correct, complete, and verified metadata and sequence data required for reproducible research.

## Decision Process
1. **Literature Review**: Reviewed recent publications regarding *Acropora millepora* gene expression under thermal stress.
2. **NCBI Verification**: Queried the NCBI BioProject database to validate the status of `PRJNA292777` and identify the current active project ID.
3. **Data Availability Check**: Confirmed that `PRJNA321023` contains the necessary RNA-seq data (FASTQ files) and associated phenotype metadata required for User Story 1 (Ingestion) and User Story 2 (DGE Analysis).
4. **Impact Assessment**: Verified that the change in ID does not alter the biological scope of the study but ensures data integrity and accessibility.

## Impact on Success Criteria
- **SC-001 (Data Integrity)**: Ensures the pipeline downloads verified, non-corrupted data from the authoritative source.
- **SC-002 (Statistical Rigor)**: Guarantees that the sample size and metadata completeness meet the requirements for differential expression analysis.
- **SC-003 (Biological Plausibility)**: Maintains the relevance of the dataset to the specific biological question (thermal resilience in *A. millepora*).

**Note**: The change from `PRJNA292777` to `PRJNA321023` is a metadata update only; it does not affect the analytical methods or the provisional filtering thresholds defined in `code/config.py` (T004).

## Final Value Determination Date
**2023-10-27**

## Implementation Notes
- `code/config.py` has been updated to reflect `BIOPROJECT_ID = "PRJNA321023"` (See Task T004c).
- All data ingestion scripts (T015, T018) must reference the new ID.
- This amendment record serves as the formal audit trail for this change.

## References
- NCBI BioProject: https://www.ncbi.nlm.nih.gov/bioproject/PRJNA321023
- Project Plan: `specs/001-coral-resilience-prediction/plan.md`
- Original Spec: `specs/001-coral-resilience-prediction/spec.md` (Frozen)