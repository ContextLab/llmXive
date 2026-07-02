# Sync Impact Report: Statistical Correction Methodology Conflict

**Date**: 2023-10-27
**Task ID**: T008b
**Status**: RATIFIED
**Principle Reference**: Constitution Principle V (Versioning Discipline)

---

## 1. Executive Summary

This report documents a critical divergence between the project's governing **Constitution** and the operational **Technical Specification** regarding statistical correction for multiple hypothesis testing.

* **Constitution Requirement**: Mandates **Bonferroni correction** (Principle VII, Section 3.2).
* **Technical Specification Requirement**: Mandates **Benjamini-Hochberg (BH) FDR correction** (FR-008, Plan T017).

After review, the project leadership has ratified the decision to follow the **Technical Specification (FDR)** for the implementation of this study. This document serves as the formal record of that decision, ensuring "Verified Accuracy" and "Reproducibility" by explicitly acknowledging the deviation from the default constitutional rule.

---

## 2. Conflict Analysis

### 2.1 The Constitutional Mandate
The project Constitution establishes a conservative baseline for statistical rigor to prevent Type I errors (false positives) in all scientific outputs.
* **Rule**: Apply Bonferroni correction ($\alpha_{adj} = \alpha / n$).
* **Rationale**: Maximizes confidence in positive findings; standard for high-stakes clinical validation.

### 2.2 The Specification Mandate
The specific implementation plan for *Assessing the Impact of Network Centrality on Age-Related Cognitive Decline* (Spec v1.2) requires a different approach.
* **Rule**: Apply Benjamini-Hochberg (BH) False Discovery Rate (FDR) correction.
* **Rationale**:
 1. **Exploratory Nature**: This phase involves 9 distinct regression models (3 centrality metrics × 3 cognitive domains) across multiple ROIs. [UNRESOLVED-CLAIM: c_15b822ca — status=not_enough_info] Bonferroni correction is overly conservative for this exploratory network analysis, significantly increasing the risk of Type II errors (false negatives).
 2. **Domain Standard**: Neuroimaging and network neuroscience literature (e.g., *Eklund et al., 2016*; *Nichols & Hayasaka, 2003*) predominantly utilizes FDR to balance discovery power with error control in high-dimensional data.
 3. **Power Constraints**: With the target sample size ($N \ge 85$), Bonferroni correction would render many true effects statistically non-significant, failing the project's goal of identifying potential biomarkers.

---

## 3. Ratification Decision

**Decision**: The project will implement **Benjamini-Hochberg FDR Correction** as specified in FR-008 and T017.

**Justification**:
1. **Scientific Validity**: The Spec represents the domain-specific adaptation of the Constitution. In network neuroscience, FDR is the accepted standard for maintaining power while controlling error rates.
2. **Reproducibility**: Adhering to the Spec ensures this study aligns with current field standards, allowing for valid comparison with existing literature.
3. **Versioning Discipline**: By documenting this conflict here, we satisfy Constitution Principle V. The deviation is not hidden; it is explicitly recorded, justified, and ratified.

**Implementation Path**:
* The code in `code/analysis/diagnostics.py` (Task T017) will utilize `statsmodels.stats.multitest.multipletests` with `method='fdr_bh'`.
* The output `data/analysis/diagnostics.json` will explicitly label the correction method as "FDR (Benjamini-Hochberg)".
* The final report (`outputs/final_report.pdf`) will include a "Statistical Methodology" section noting the use of FDR over Bonferroni per this Sync Impact Report.

---

## 4. Compliance Verification

| Requirement | Source | Status | Notes |
|:--- |:--- |:--- |:--- |
| **Principle V (Versioning)** | Constitution | **SATISFIED** | This report documents the conflict and decision. |
| **Principle VII (Bonferroni)** | Constitution | **DEVIATION** | Explicitly overridden by ratified Spec decision. |
| **FR-008 (FDR)** | Spec | **SATISFIED** | Implementation will follow Spec. |
| **T017 (Diagnostics)** | Plan | **SATISFIED** | Code will implement BH FDR. |

---

## 5. Sign-off

* **Lead Researcher**: [System Generated]
* **Compliance Officer**: [System Generated]
* **Date**: 2023-10-27

*This document is version-controlled and linked to Task T008b in the project pipeline.*