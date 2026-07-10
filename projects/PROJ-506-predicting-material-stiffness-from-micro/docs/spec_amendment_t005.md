# Specification Amendment: Statistical Methodology Update (T005)

## Summary
This document records the amendment to `spec.md` and `plan.md` to align the statistical analysis methodology with the project plan. The primary change is the replacement of "paired t-tests" with "One-way ANOVA and Tukey HSD" for evaluating model performance across density bins.

## Changes to `spec.md`

### 1. Functional Requirement FR-007
**Original Text:**
> FR-007: The system shall compare model prediction errors across different inclusion density bins using paired t-tests to determine statistical significance.

**Amended Text:**
> FR-007: The system shall compare model prediction errors across different inclusion density bins using **One-way ANOVA** followed by **Tukey HSD** post-hoc analysis to determine statistical significance and pairwise differences.

### 2. Success Criteria SC-004
**Original Text:**
> SC-004: The model is considered successful if paired t-tests show no statistically significant difference (p > 0.05) in prediction errors between the training density range and the held-out test density range.

**Amended Text:**
> SC-004: The model is considered successful if **One-way ANOVA** indicates no statistically significant difference (p > 0.05) in prediction errors across density bins, and **Tukey HSD** post-hoc tests confirm no significant pairwise degradation for out-of-distribution densities.

### 3. User Story 3 Acceptance Scenario 2
**Original Text:**
> Acceptance Scenario 2: The evaluation report displays p-values from paired t-tests comparing error distributions of in-distribution vs. out-of-distribution samples.

**Amended Text:**
> Acceptance Scenario 2: The evaluation report displays F-statistics and p-values from **One-way ANOVA** comparing error distributions across all density bins, along with a **Tukey HSD** matrix highlighting significant pairwise differences.

## Changes to `plan.md`

### 1. Phase 3, Task 3.2 (Statistical Test)
**Original Text:**
> Task 3.2: Perform paired t-tests on prediction errors between density groups to verify generalization.

**Amended Text:**
> Task 3.2: Perform **One-way ANOVA** on prediction errors across density groups. If the ANOVA result is significant, follow up with **Tukey HSD** post-hoc tests to identify specific bin pairs with significant differences.

### 2. Success Criteria (General)
**Update:**
All references to "paired t-tests" in the Success Criteria section have been updated to "One-way ANOVA and Tukey HSD" to ensure consistency with the new methodology.

## Justification
The shift to One-way ANOVA is necessary because:
1. **Multiple Comparisons:** We are comparing errors across *multiple* density bins (>2), not just two groups. Paired t-tests are insufficient for >2 groups without inflating Type I error rates.
2. **Variance Homogeneity:** ANOVA allows for testing the null hypothesis that all group means are equal simultaneously, which is the correct approach for stratified k-fold validation results across density strata.
3. **Post-hoc Precision:** Tukey HSD provides a robust method for controlling the family-wise error rate when making all pairwise comparisons between density bins.

This change aligns the specification with the rigorous statistical requirements outlined in Plan Task 0.5 and ensures the project meets scientific best practices for material property prediction validation.
