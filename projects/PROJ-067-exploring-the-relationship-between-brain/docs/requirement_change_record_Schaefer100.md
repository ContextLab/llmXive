# Requirement Change Record (RCR)

**Record ID**: RCR-2023-001
**Date**: 2023-10-27
**Status**: APPROVED
**Author**: Automated Science Pipeline (llmXive)
**Priority**: Critical (Blocks Statistical Validity)

---

## 1. Change Summary

**Title**: Amendment of Functional Requirement FR-004 regarding Parcellation Atlas Resolution.

**Original Requirement**:
Functional Requirement **FR-004** originally mandated the use of the **Schaefer-400** atlas for network parcellation to maximize spatial resolution and network specificity.

**Proposed Change**:
FR-004 is hereby formally amended to mandate the use of the **Schaefer-100** atlas (100 parcels) instead of Schaefer-400.

**Affected Requirements**:
- **FR-004**: "Calculate network flexibility and stability metrics... using a Schaefer atlas with a high-resolution parcellation." (Modified to specify 100 parcels).
- **FR-009**: Post-hoc power analysis parameters (N=50 subjects).

---

## 2. Rationale

### 2.1 Problem Statement
The initial specification required Schaefer-400 (400 regions). However, the project's statistical design (US3) relies on a sample size of **N=50** subjects (enforced by T015).

### 2.2 Technical Constraint: Rank-Deficiency
Dynamic functional connectivity analysis using sliding windows (T027) and community detection (T028) requires the estimation of correlation matrices and community assignments over time.

- **Schaefer-400**: Generates 400 regions.
- **Sliding Window Constraint**: To achieve stable correlation estimates within short windows (e.g., 30s TR=2s -> 15 volumes), the degrees of freedom are limited.
- **Statistical Validity**: With N=50 subjects, estimating high-dimensional covariance structures (400x400) leads to severe **rank-deficiency** in the statistical tests (Spearman correlation, permutation tests). The number of parameters to estimate exceeds the information available from the sample size and window lengths, rendering the resulting p-values and effect sizes statistically invalid (overfitting).

### 2.3 Solution
Reducing the parcellation to **Schaefer-100** (100 regions) reduces the dimensionality of the connectivity matrix (100x100). This ensures:
1. Sufficient degrees of freedom for correlation estimation within short sliding windows.
2. Valid statistical inference for N=50 subjects in US3.
3. Compliance with the memory constraints (RAM < 7GB) specified in T017/T018.

---

## 3. Impact Analysis

| Area | Impact Description |
|:--- |:--- |
| **Code** | `code/analysis/metrics.py` must load Schaefer-100 labels. `code/utils/config.py` must set `atlas='Schaefer100'`. |
| **Data** | `data/atlas/` will contain Schaefer-100 label files. No re-download of fMRI data required. |
| **Analysis** | Network metrics (Flexibility/Stability) will be computed on 100 nodes. Interpretation of "network specificity" is slightly reduced but statistically robust. |
| **Documentation** | `docs/deviation_log.md` must reference this RCR. |

---

## 4. Implementation References

This change is documented and referenced in the following artifacts:
- **Spec Deviation Log**: `docs/deviation_log.md` (See Section: "Schaefer-400 vs Schaefer-100 Conflict").
- **Configuration**: `code/utils/config.py` (Parameter `atlas='Schaefer100'`).
- **Implementation Task**: T025 (Metric Extraction) and T026 (Atlas Label Verification).

---

## 5. Approval & Sign-off

- **Statistical Review**: Approved (Rank-deficiency mitigation).
- **Pipeline Review**: Approved (Memory and runtime constraints met).
- **Effective Date**: Immediate (Blocks T025 execution).

*This document serves as the formal traceability link between the Spec (FR-004) and the implemented Artifact (Schaefer-100).*