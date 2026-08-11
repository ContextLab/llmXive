# Specification Override: SC-001 Correction

## Overview
This document formally amends the project specification regarding the measurement target for Success Criterion 001 (SC-001).

## Original Specification (Rejected)
**SC-001 (Original)**: The correlation coefficient and p-value between **CLR-transformed alpha diversity** and fluid intelligence are measured against the Spearman rank correlation test results.

**Reason for Rejection**:
The original specification incorrectly mandated the use of Centered Log-Ratio (CLR) transformed alpha diversity values. Alpha diversity (specifically the Shannon Index) is a scalar summary statistic calculated from raw counts. Applying CLR transformation to a scalar alpha diversity value is mathematically invalid and methodologically unsound, as CLR is designed for compositional data (vectors of relative abundances) to handle the constant sum constraint, not for summary diversity indices.

## Corrected Specification (Approved)
**SC-001 (Corrected)**: The correlation coefficient and p-value between **Raw Shannon Index** and fluid intelligence are measured against the Spearman rank correlation test results.

## Implementation Details
- **Input Data**: The `shannon_index` column in the processed dataset, calculated from **raw** OTU/ASV counts using `scikit-bio`.
- **Transformation**: No CLR transformation is applied to the `shannon_index` column.
- **Statistical Test**: Spearman rank correlation (`scipy.stats.spearmanr`).
- **Output**: Correlation results must reflect the relationship between the untransformed Shannon Index and fluid intelligence scores.

## Reference
This override supersedes the initial specification found in `specs/001-gene-regulation/spec.md` and aligns with the corrected requirements in `docs/spec_override_FR003.md`.
