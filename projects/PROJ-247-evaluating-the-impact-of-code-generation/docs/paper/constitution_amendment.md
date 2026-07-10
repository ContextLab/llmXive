# Amendment to Constitution Principle VI: Statistical Test Selection

## Context

This document amends **Constitution Principle VI** of the research protocol to clarify the statistical methodology used for comparing maintainability metrics between LLM-generated and Human-generated code blocks.

## Original Principle VI

> "Comparisons between groups shall utilize non-parametric tests appropriate for the data structure, ensuring robustness against distributional assumptions."

## Amendment Rationale

The original principle was underspecified regarding the choice between the **Mann-Whitney U test** (Wilcoxon Rank-Sum) and the **Wilcoxon Signed-Rank test**. This amendment explicitly mandates the use of the **Wilcoxon Signed-Rank test** for this study.

### Why Wilcoxon Signed-Rank and not Mann-Whitney U?

The selection of the Wilcoxon Signed-Rank test over the Mann-Whitney U test is driven by the **experimental design** established in User Story 1 (Task T015), specifically the **Propensity Score Matching** protocol.

1. **Paired Data Structure**:
 - The research pipeline (Task T015) performs **1:1 nearest-neighbor propensity score matching**.
 - Each LLM-generated code block is explicitly matched with a Human-generated code block from the **same repository**, controlling for repository-level covariates (e.g., star count, age) and block-level complexity metrics.
 - This creates **dependent samples** (pairs), where the two observations in a pair are correlated by design.

2. **Inappropriateness of Mann-Whitney U**:
 - The Mann-Whitney U test (Wilcoxon Rank-Sum) assumes **independent samples**.
 - Applying Mann-Whitney U to matched pairs ignores the dependency structure introduced by the matching process.
 - Using an independent test on paired data reduces statistical power and fails to account for the variance reduction achieved by matching, potentially leading to inflated Type I error rates or missed effects.

3. **Appropriateness of Wilcoxon Signed-Rank**:
 - The Wilcoxon Signed-Rank test is designed specifically for **paired data**.
 - It tests the null hypothesis that the median difference between pairs is zero.
 - By analyzing the **differences** within each matched pair (LLM metric - Human metric), this test leverages the matched design to control for confounding variables more effectively than an independent test.

## Implementation Verification

The implementation of this amendment is verified in:
- **Code**: `code/03_analysis.py` function `run_wilcoxon_tests()`, which utilizes `scipy.stats.wilcoxon`.
- **Data**: `data/processed/matched_pairs.csv` contains the 1:1 matched structure required for this test.

## Conclusion

Constitution Principle VI is hereby amended to specify: **"For analyses involving propensity-score matched pairs, the Wilcoxon Signed-Rank test shall be used to compare metrics, as the data structure consists of dependent samples."** The Mann-Whitney U test is explicitly excluded for this comparison.