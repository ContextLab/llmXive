# Amendment 001: Replacement of FR-003 (Repeated-Measures ANOVA) with Permutation Test

**Date**: 2023-10-27
**Status**: Ratified
**Author**: Research Implementation Team
**Reference**: Plan.md, Task T033

## 1. Summary

This amendment officially replaces **FR-003** (Statistical Analysis: Repeated-Measures ANOVA) in the original specification with a **Permutation Test** as the primary inferential statistical method for analyzing the difference in D-scores between Low and High visual complexity conditions.

## 2. Justification

The original specification (FR-003) mandated a Repeated-Measures ANOVA. However, the implementation plan (specifically Task T033) identified a methodological disconnect:

1. **Non-Normality**: Visual complexity metrics and derived D-scores may not strictly adhere to the normality assumptions required for parametric ANOVA, particularly with moderate sample sizes (N=60).
2. **Robustness**: Permutation tests provide a non-parametric alternative that relies on the empirical distribution of the data rather than theoretical distributions, offering greater robustness against violations of normality and homoscedasticity.
3. **Alignment**: The implementation plan explicitly requires a Permutation Test to ensure the analysis aligns with the "fail loud" and rigorous verification standards of the llmXive pipeline.

## 3. Technical Details

### 3.1. Original Requirement (FR-003)
> "Perform a Repeated-Measures ANOVA on the D-scores with 'Complexity Condition' (Low/High) as the within-subjects factor."

### 3.2. New Requirement (Permutation Test)
> "Perform a Permutation Test (n_permutations=1000) to assess the significance of the mean difference in D-scores between Low and High complexity conditions. The null hypothesis is that there is no difference in D-scores between conditions."

**Parameters**:
- **Metric**: Mean difference of D-scores (High - Low).
- **Permutations**: 1000.
- **Seed**: 42 (for reproducibility).
- **Output**: p-value, observed effect size (Cohen's d), and null distribution.

## 4. Implementation Impact

- **Task T033**: Implements the Permutation Test logic in `code/analysis/permutation.py`.
- **Task T034**: Calculates effect sizes and p-values based on the permutation distribution.
- **Task T035**: Includes sensitivity analysis (threshold sweep and LOIO) specific to the permutation framework.
- **Spec Update**: The `spec.md` file must be updated to reference this amendment and mark FR-003 as "Amended".

## 5. Verification

- The implementation must produce `data/results/permutation_results.json` containing the p-value and effect size.
- The `code/analysis/permutation.py` module must be unit-tested to ensure the null distribution approximates zero under the null hypothesis.
- The pipeline must fail loudly if real data is missing, preventing synthetic fallback (as per global constraints).

## 6. Conclusion

This amendment resolves the legal disconnect between the original spec and the implementation plan, ensuring the statistical analysis is robust, reproducible, and aligned with modern non-parametric best practices for this specific experimental design.

**Ratified by**: [Human Researcher Signature/Approval]
**Date**: 2023-10-27
