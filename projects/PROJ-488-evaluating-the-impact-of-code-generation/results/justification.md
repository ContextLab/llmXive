# Justification of Statistical Thresholds and Effect Size Interpretations

This document provides the community-standard justification for all statistical thresholds
and effect size interpretations used in the evaluation of code generation impact (Project PROJ-488).
These standards align with guidelines from the American Statistical Association (ASA),
the *Journal of Machine Learning Research* (JMLR), and established software engineering
empirical research practices.

## 1. Significance Level (Alpha)

**Selected Threshold:** α = 0.05

**Justification:**
The 0.05 significance level is the standard convention in scientific research, including
software engineering and empirical studies of programming languages. It represents a
balance between Type I error (false positive) and Type II error (false negative) rates.

- **Source:** Wasserstein, R. L., & Lazar, N. A. (2016). "The ASA Statement on p-Values:
 Context, Process, and Purpose." *The American Statistician*.
- **Context:** In the context of comparing human-written vs. LLM-generated code metrics
 (e.g., cyclomatic complexity, bug density), a p-value < 0.05 indicates that the observed
 difference is unlikely to have occurred by random chance alone, assuming the null hypothesis
 (no difference) is true.

**Sensitivity Analysis:**
As per Task T033, we performed sensitivity analysis across {0.01, 0.05, 0.1} to ensure
robustness. Results are reported in `results/sensitivity.md`.

## 2. Multiple Comparison Correction

**Selected Method:** Benjamini-Hochberg (BH) Procedure

**Justification:**
When testing multiple metrics simultaneously (e.g., Cyclomatic Complexity, Maintainability Index,
Bug Count), the probability of false positives increases. The BH procedure controls the
False Discovery Rate (FDR), which is more appropriate than the Bonferroni correction for
exploratory research where some false positives are acceptable if the overall rate is controlled.

- **Source:** Benjamini, Y., & Hochberg, Y. (1995). "Controlling the False Discovery Rate:
 A Practical and Powerful Approach to Multiple Testing." *Journal of the Royal Statistical Society*.
- **Application:** We apply BH correction to the set of p-values obtained from Mann-Whitney U tests
 across all metrics. Adjusted p-values (q-values) < 0.05 are considered statistically significant.

## 3. Effect Size Interpretation (Cliff's Delta)

**Selected Metric:** Cliff's Delta (δ)

**Justification:**
Unlike Cohen's d, Cliff's Delta is a non-parametric measure of effect size that does not assume
normality of the data distributions. Given that code metrics (e.g., complexity scores) often
exhibit skewed distributions, Cliff's Delta is the preferred metric for the Mann-Whitney U test.

**Thresholds and Magnitude Labels:**

| | Cliff's Delta (|δ|) | Magnitude | Interpretation |
|---|---|---|---|
| Negligible | < 0.147 | Negligible | No practical difference |
| Small | 0.147 – 0.330 | Small | Minor difference, potentially negligible in practice |
| Medium | 0.330 – 0.474 | Medium | Noticeable difference, warrants attention |
| Large | ≥ 0.474 | Large | Substantial difference, likely practically significant |

**Source:** Romano, J., Kromrey, J. D., Coraggio, J., Skowronek, J., & Devine, L. (2006).
"Appropriate Statistics for Ordinal Level Data: Determining the Practical Significance of
Differences in Ordinal Data." *Florida Association of Institutional Research*.
(Note: These thresholds are widely adopted in empirical software engineering literature,
e.g., *Empirical Software Engineering* journal).

**Application:**
We only generate review guidelines (Task T032) for metrics where:
1. Adjusted p-value < 0.05 (statistically significant)
2. |Cliff's Delta| ≥ 0.1 (Small effect size or larger)

This dual-criteria approach ensures that guidelines are triggered only when differences are
both statistically reliable and practically meaningful.

## 4. Statistical Power

**Target Power:** ≥ 0.80

**Justification:**
A power of 0.80 (80%) is the standard minimum threshold in empirical research to ensure
that the study has a high probability of detecting an effect if one truly exists.

- **Source:** Cohen, J. (1992). "A Power Primer." *Psychological Bulletin*.
- **Implementation:** Task T026 computes achieved power based on observed effect sizes and
 sample sizes. If power < 0.80, a warning is logged, and results are interpreted with caution.
 The study design targets n ≥ 1000 per group (Task T019) to ensure sufficient power for
 detecting small-to-medium effects.

## 5. Independence Assumption

**Mitigation Strategy:** Subsampling by Repository OR Cluster-Robust SE

**Justification:**
Code snippets from the same repository may be correlated, violating the independence assumption
of standard statistical tests. To address this:
- **Preferred:** Subsample to one snippet per repository (if metadata available).
- **Alternative:** Use cluster-robust standard errors if subsampling reduces power too much.

This approach aligns with recommendations in *Empirical Software Engineering* for handling
nested data structures.

## 6. Conclusion

All thresholds and methods selected for this study adhere to established community standards
in software engineering research and statistics. The combination of:
- α = 0.05
- Benjamini-Hochberg correction for multiple comparisons
- Cliff's Delta for non-parametric effect size with established magnitude thresholds
- Power analysis ensuring ≥ 0.80

ensures that the findings regarding the impact of code generation on code quality metrics
are both statistically rigorous and practically interpretable.