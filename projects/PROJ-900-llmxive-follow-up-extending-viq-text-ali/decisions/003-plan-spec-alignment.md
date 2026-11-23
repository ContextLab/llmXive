# Decision Record 003: Plan-Spec Alignment (SC-005 vs SC-004)

**Date**: 2024-05-21
**Status**: Accepted
**Deciders**: llmXive Research Team
**Context**:
During the verification of the project plan (`plan.md`) against the feature specification (`spec.md`), a discrepancy was identified regarding the statistical testing methodology for User Story 2 (Fidelity Measurement).

The `plan.md` file, in the "Spec Amendments Required" section, referenced a requirement labeled "SC-005" (One-sample t-test). However, the official `spec.md` document defines the statistical requirement as "SC-004", which mandates a **paired t-test** or **Wilcoxon signed-rank test** to compare texture complexity against reconstruction error.

The reference to "SC-005" in the plan was identified as a typographical error or an artifact of an outdated draft, as no such requirement exists in the current approved specification.

**Decision**:
The `plan.md` file has been updated to remove the erroneous reference to "SC-005". The "Spec Amendments Required" section now correctly references **SC-004** as the governing requirement for statistical analysis.

This decision aligns the project execution plan with the official specification, ensuring that the statistical analysis (Task T022) implements the correct paired t-test/Wilcoxon logic rather than a one-sample test.

**Consequences**:
1. The `plan.md` file is now consistent with `spec.md`.
2. Task T022 (Correlation Analysis) will proceed based on the SC-004 requirement (paired t-test/Wilcoxon).
3. No changes to the actual statistical logic in code are required, as the implementation was already targeting the paired test logic per the spec; only the documentation reference was corrected.

**References**:
- `spec.md`: Section SC-004 (Statistical Testing)
- `plan.md`: Section "Spec Amendments Required" (Updated)
- Decision Record 002: Native Ground Truth & Paired Tests
