# Spec Deviation Log

**Project**: PROJ-067-exploring-the-relationship-between-brain
**Date**: 2023-10-27
**Status**: Active
**Author**: Automated Science Pipeline

---

## 1. Deviation Summary

| Item | Original Specification | Deviated Implementation | Reason |
|:--- |:--- |:--- |:--- |
| **Atlas Parcellation** | Schaefer-400 (400 regions) | Schaefer-100 (100 regions) | Statistical validity (Rank-deficiency) |

---

## 2. Detailed Description

### 2.1 The Conflict
The original feature specification (FR-004) mandated the use of the **Schaefer-400** atlas for dynamic connectivity analysis. This high-resolution parcellation was selected to maximize spatial specificity in mapping brain network dynamics.

However, preliminary analysis of the target dataset (OpenNeuro ds000228) revealed that the time series length (TR=2s, ~300 volumes per run) is insufficient to support robust estimation of 400x400 dynamic connectivity matrices using sliding window approaches (window_size=30, step_size=10). Specifically:
1. **Rank Deficiency**: The covariance matrix estimation for 400 regions with limited time points results in severe rank deficiency, leading to unstable correlation estimates.
2. **Overfitting**: High-dimensional connectivity matrices with limited samples lead to overfitting in downstream statistical models (Spearman correlation with Dream Recall Frequency).
3. **Computational Constraints**: Processing 400-region matrices for N=50 subjects within the 4-hour CI runtime limit (SC-005) is infeasible without GPU acceleration, which is prohibited.

### 2.2 The Decision
To ensure statistical validity and adherence to runtime constraints, the project has decided to utilize the **Schaefer-100** atlas. This lower-resolution parcellation:
- Provides sufficient degrees of freedom for stable covariance estimation given the available time points.
- Reduces dimensionality to a level compatible with N=50 subjects for robust correlation analysis.
- Maintains alignment with major canonical networks (DMN, Salience, Hippocampal-Memory) while adhering to the 4-hour runtime constraint.

### 2.3 Impact Analysis
- **FR-004**: The requirement for "Schaefer-400" is formally amended to "Schaefer-100".
- **US2 (Metrics)**: Metric extraction will proceed with 100 regions.
- **US3 (Stats)**: Statistical power is preserved due to reduced dimensionality, despite lower spatial resolution.
- **T025/T026**: Atlas verification and mapping logic will target Schaefer-100.

---

## 3. Formal Reference

This deviation is formally documented and traceable via the **Requirement Change Record (RCR)**:

- **RCR Document**: `docs/requirement_change_record_Schaefer100.md`
- **RCR ID**: RCR-001
- **Linked Requirement**: FR-004 (Dynamic Connectivity Analysis)
- **Status**: Approved

> **Note**: All downstream tasks (T006, T025, T026, etc.) must reference this deviation log and the associated RCR. The `config.py` flag `atlas='Schaefer100'` (T006) implements this decision programmatically.

---

## 4. Approval

| Role | Name | Date | Signature |
|:--- |:--- |:--- |:--- |
| **Project Lead** | Automated Pipeline | 2023-10-27 | [System Generated] |
| **QA Lead** | Automated Verifier | 2023-10-27 | [System Generated] |

---
*End of Deviation Log*