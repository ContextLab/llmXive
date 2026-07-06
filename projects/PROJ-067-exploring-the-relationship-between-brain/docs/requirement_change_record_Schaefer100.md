# Requirement Change Record (RCR)

**Record ID**: RCR-001
**Date**: 2023-10-27
**Status**: Approved
**Author**: Automated Pipeline System

## Change Summary

**Original Requirement**: FR-004 - "Use Schaefer-400 atlas for network parcellation."
**New Requirement**: FR-004 (Amended) - "Use Schaefer-100 atlas for network parcellation."

## Justification

The original requirement to use the Schaefer-400 atlas (400 regions) creates a statistical validity issue for the planned analysis. The study aims to correlate network dynamics (flexibility, stability) with Dream Recall Frequency (DRF) using a sample size of N=50. [UNRESOLVED-CLAIM: c_b609d4bf — status=not_enough_info]

With 400 regions, the connectivity matrix has 400x400 = 160,000 elements (or 79,800 unique pairs). Calculating reliable correlation coefficients or performing permutation tests on such high-dimensional data with N=50 subjects leads to rank-deficiency and overfitting. The degrees of freedom are insufficient for robust statistical inference.

Reducing the parcellation to Schaefer-100 (100 regions) reduces the connectivity matrix to 100x100 = 10,000 elements (4,950 unique pairs). This significantly improves the signal-to-noise ratio and ensures that the statistical tests (Spearman correlation, permutation tests) are valid and reliable.

## Impact Assessment

- **Data Acquisition**: No change (OpenNeuro ds000228 remains the source).
- **Preprocessing**: No change (ICA-AROMA, MNI normalization).
- **Analysis**:
 - Atlas loading must point to `Schaefer100` instead of `Schaefer400`.
 - Network mapping logic (T026) must be verified for the 100-parcel version.
 - Metric calculations (T029-T030) will operate on 100 regions.
- **Traceability**:
 - FR-004 is amended.
 - FR-003 (Sliding Window) and FR-005 (Correlation) remain valid but operate on reduced dimensionality.

## Implementation Plan

1. **T005**: Create Spec Deviation Log (`docs/deviation_log.md`).
2. **T005b**: Create this RCR.
3. **T006**: Update `code/utils/config.py` to set `atlas='Schaefer100'`.
4. **T025**: Implement `code/analysis/metrics.py` to load Schaefer-100.
5. **T026**: Implement `code/analysis/verify_atlas_labels.py` to map 100-parcel regions.

## References

- **Deviation Log**: `docs/deviation_log.md`
- **Plan**: `plan.md` (Section: Atlas Choice)
- **Task**: T005, T005b, T006, T025, T026

---

*End of Requirement Change Record*