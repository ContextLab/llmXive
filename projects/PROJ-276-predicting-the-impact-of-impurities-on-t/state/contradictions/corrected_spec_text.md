# Corrected Specification Text

This document contains the exact text replacements required for `spec.md` to resolve critical contradictions identified in the pre-flight phase.

## Replacement for FR-006 (Runtime Limit)

**Original Spec Value:** [Variable/Undefined]
**Constitution Value:** 30 minutes
**Resolution:** Enforce 30-minute runtime limit as per Constitution Principle VII.

**Corrected Text for spec.md (FR-006):**
> **FR-006: Runtime Limit.** The entire data processing, modeling, and validation pipeline MUST complete within a maximum wall-clock time of 30 minutes. This limit enforces resource efficiency and ensures rapid iteration cycles. If a process exceeds this limit, it MUST terminate with a non-zero exit code and a clear error message.

---

## Replacement for FR-004 (Statistical Validation Method)

**Original Spec Value:** "Target Permutation Test" (shuffling Y)
**Constitution Value:** Methodological Validity
**Resolution:** Replace "Target Permutation Test" with "Feature Permutation Test" as the target permutation is methodologically invalid for assessing feature importance.

**Corrected Text for spec.md (FR-004):**
> **FR-004: Feature Permutation Test.** To validate the statistical significance of impurity impact on superconductivity, the system MUST implement a **Feature Permutation Test**. This involves shuffling the values of a specific feature (impurity type or concentration) in the validation set, re-predicting the target variable (Tc), and comparing the resulting performance degradation against the baseline model performance. A significant drop in performance indicates the feature is important. This method replaces the originally specified "Target Permutation Test" which was deemed methodologically unsound for this use case.

---

## Implementation Notes

1. **FR-006**: This text must replace the existing FR-006 section in `spec.md` verbatim.
2. **FR-004**: This text must replace the existing FR-004 section in `spec.md` verbatim.
3. These changes align the specification with the project's Constitution and the implementation plan, ensuring methodological correctness and resource constraints are met.