# Spec Deviation Log

## Project: PROJ-067-exploring-the-relationship-between-brain

### Deviation Record: DR-001

**Date**: 2023-10-27
**Author**: Automated Pipeline System
**Status**: Accepted

#### Description of Deviation

**Original Requirement**: The initial specification (FR-004) mandated the use of the **Schaefer-400** atlas for network parcellation.

**Issue**: Statistical analysis of the relationship between brain network dynamics and dream recall frequency requires a sufficient number of data points relative to the number of parameters. Using Schaefer-400 (400 regions) with the short sliding windows (30s) and limited subjects (N=50) results in rank-deficiency and unstable covariance estimates.

**Decision**: The project will use the **Schaefer-100** atlas (100 regions) instead of Schaefer-400. This reduces the dimensionality of the connectivity matrices, ensuring statistical validity for the correlation and permutation tests planned in User Story 3.

#### Impact Analysis

- **Data Processing**: The pipeline must load Schaefer-100 parcellations.
- **Metrics**: Network flexibility and stability calculations will be based on 100 regions.
- **Networks**: The mapping of regions to DMN, Salience, and Hippocampal-Memory networks must be verified for the 100-parcel version.
- **Traceability**: This deviation is formally recorded in the Requirement Change Record (RCR).

#### References

- **Requirement Change Record**: `docs/requirement_change_record_Schaefer100.md`
- **Plan Document**: `plan.md` (Section: Atlas Choice)
- **Task**: T005 (Spec Deviation Log)
- **Task**: T005b (Formal Requirement Change Record)

---

## Deviation Record: DR-002 (Runtime Constraint)

**Date**: 2023-10-27
**Status**: Accepted

#### Description

**Original Constraint**: No specific runtime limit was initially defined for the full pipeline in the MVP scope.

**Issue**: The CI environment has a strict 4-hour wall-clock time limit (SC-005). The full pipeline (Download -> Preprocess -> Metrics -> Stats) on 50 subjects with ICA-AROMA can exceed this limit if not optimized.

**Decision**:
1. Implement runtime monitoring in `main.py` (T045).
2. Enforce a hard limit of 4 hours, raising a `RuntimeError` if exceeded (T049).
3. Update CI configuration to treat this error as a build failure (T050).

#### Impact

- **Pipeline Design**: Must be efficient. Intermediate files must be cleaned up (T021).
- **Subject Selection**: May need to be further restricted if runtime is still too high, but N=50 is the target.
- **Task Dependencies**: T049 and T050 are critical for compliance.

---

## Deviation Record: DR-003 (Hippocampal Labeling)

**Date**: 2023-10-27
**Status**: Accepted

#### Description

**Original Assumption**: The Schaefer atlas contains a "Hippocampal-Memory" label.

**Issue**: The standard Schaefer-2018 atlas does not have an explicit "Hippocampal-Memory" network label. It uses 7 or 17 Yeo networks.

**Decision**: Implement a dynamic mapping step (T026) to identify regions associated with the hippocampus or memory functions based on source labels or external mappings, and map them to the "Hippocampal-Memory" ROI. If no explicit mapping exists, the pipeline will fall back to a heuristic or report missing data.

#### Impact

- **Task T026**: Must run before T025 to generate `network_label_map.csv`.
- **Task T025**: Must handle the case where the mapping file exists or is missing.

---

*End of Deviation Log*
