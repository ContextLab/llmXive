# Decision Record 003: Plan-Spec Alignment (SC-005 vs SC-004)

## Status
Accepted

## Context
During the verification of `spec.md` against the project plan (`plan.md`), a discrepancy was identified in the statistical testing requirements.

- The project `plan.md` (in the "Spec Amendments Required" section) referenced **SC-005** as the required amendment for statistical testing.
- The actual `spec.md` file defines the statistical testing requirement as **SC-004** (Paired t-test or Wilcoxon signed-rank test).
- There is no "SC-005" defined in the current specification document. This was likely a typo in the initial planning phase or an artifact of an older draft.

## Decision
We will update the project documentation to align with the authoritative source (`spec.md`).

1. The reference to "SC-005" in the `plan.md` "Spec Amendments Required" section is **removed**.
2. The `plan.md` is updated to explicitly reference **SC-004** as the governing requirement for statistical testing (paired t-test or Wilcoxon signed-rank test).
3. This decision record (DR-003) serves as the permanent log of this alignment correction.

## Consequences
- **Plan Consistency**: The project plan now accurately reflects the specification requirements, preventing confusion during implementation of T022 (Correlation Analysis) and T028 (Semantic Comparison).
- **Implementation Clarity**: Developers implementing statistical tests will look for SC-004, ensuring the correct tests (paired t-test/Wilcoxon) are applied as per the spec, rather than searching for a non-existent SC-005.
- **Audit Trail**: This record documents the correction for future reviewers, ensuring the rationale for the change is preserved.

## Related Tasks
- T036: Spec Verification (identified the discrepancy)
- T036b: Plan Alignment (implementation of this decision)
- T036c: Spec Update (formalizing deviations, though the SC reference itself was correct in the spec)
- T022: Implementation of correlation analysis using SC-004 logic
- T028: Implementation of semantic comparison using SC-004 logic