# Research Methodology: Statistical Analysis Plan

## Executive Summary

This document outlines the statistical methodology employed to analyze the influence of visual complexity on implicit bias. A critical methodological decision was made to replace the originally proposed Analysis of Variance (ANOVA) with a **Permutation Test** (also known as a Randomization Test). This section details the justification for this shift, the theoretical basis for the chosen method, and the specific implementation strategy.

## 1. Original Proposal: Analysis of Variance (ANOVA)

The initial research plan (referenced in `specs/001-the-influence-of-visual-complexity-on-im/plan.md`) proposed using a standard ANOVA to compare mean D-scores across different levels of visual complexity (Low, Medium, High).

**Assumptions of ANOVA:**
1. **Normality**: The residuals of the dependent variable (D-scores) must be normally distributed within each group.
2. **Homogeneity of Variance (Homoscedasticity)**: The variance of the dependent variable must be equal across all groups.
3. **Independence**: Observations must be independent.

**The Problem:**
In studies involving Implicit Association Tests (IAT) and complex visual stimuli, these assumptions are frequently violated:
* **Non-Normality**: D-scores often exhibit skewed distributions or heavy tails, particularly with small-to-moderate sample sizes.
* **Heteroscedasticity**: Visual complexity may inherently increase response variability. High-complexity stimuli might induce more variable reaction times and error rates compared to low-complexity stimuli, violating the assumption of equal variance.
* **Stimulus-Set Confounds**: Standard ANOVA treats the specific set of images used as fixed effects or ignores the variability introduced by the specific selection of stimuli, potentially inflating Type I error rates if the stimulus set is not perfectly representative.

## 2. Methodological Shift: Permutation Test

To address these limitations and ensure the robustness of our findings, the analysis plan has been updated to utilize a **Permutation Test** for hypothesis testing. This decision aligns with best practices in psychometrics and experimental psychology where parametric assumptions are suspect (Efron & Tibshirani, 1993; Good, 2005). [UNRESOLVED-CLAIM: c_e4daa045 — status=not_enough_info]

### 2.1. Justification

The Permutation Test is chosen for the following reasons:

1. **Distribution-Free**: It makes no assumptions about the underlying distribution of the data (non-parametric). It derives the null distribution empirically by shuffling the observed data labels.
2. **Robustness to Heteroscedasticity**: While standard permutation tests can be sensitive to unequal variances, the implementation used here (mean difference of D-scores) is robust when combined with the specific experimental design of counterbalancing.
3. **Handling Stimulus-Set Variability**: By permuting the association between the complexity metric and the D-scores, we effectively test whether the observed relationship could have arisen by chance given the specific set of stimuli and responses collected, thereby controlling for stimulus-set confounds more effectively than a standard fixed-effects ANOVA.
4. **Exact p-values**: For a sufficiently large number of permutations, the p-value is an exact probability under the null hypothesis, rather than an approximation based on theoretical distributions (F-distribution). [UNRESOLVED-CLAIM: c_bfc482e1 — status=not_enough_info]

### 2.2. Implementation Details

The implemented test (see `code/analysis/permutation.py`) follows these steps:

1. **Observed Statistic**: Calculate the observed mean difference in D-scores between the High Complexity and Low Complexity groups.
2. **Permutation Procedure**:
 * Randomly shuffle the complexity labels (Low/Medium/High) assigned to the D-scores.
 * Recalculate the mean difference for the shuffled data.
 * Repeat this process $N$ times (where $N$ is sufficiently large, e.g., 10,000, to ensure stable p-value estimation).
3. **P-value Calculation**: The p-value is the proportion of permuted statistics that are as extreme or more extreme than the observed statistic.
 $$ p = \frac{1 + \sum_{i=1}^{N} I(T_{perm}^{(i)} \geq T_{obs})}{1 + N} $$
4. **Effect Size**: Cohen's $d$ is calculated based on the observed groups to quantify the magnitude of the effect, independent of the permutation logic.

## 3. Sensitivity Analysis

To further validate the robustness of the results, a **Leave-One-Image-Out (LOIO)** sensitivity analysis is performed (Task T035a). This involves:
* Iteratively removing one image stimulus from the dataset.
* Re-running the permutation test on the remaining data.
* Assessing whether the significance of the result depends heavily on any single outlier stimulus.

Additionally, a **Threshold Sweep** is conducted to ensure that the categorization of complexity (Low/Medium/High) does not arbitrarily influence the outcome.

## 4. Citations and References

* **Efron, B., & Tibshirani, R. J. (1993).** *An Introduction to the Bootstrap*. Chapman & Hall/CRC. (Foundational text on resampling methods).
* **Good, P. I. (2005).** *Permutation, Parametric, and Bootstrap Tests of Hypotheses* (3rd ed.). Springer. (Comprehensive guide to permutation testing).
* **Greenwald, A. G., Nosek, B. A., & Banaji, M. R. (2003).** Understanding and using the Implicit Association Test: I. An improved scoring algorithm. *Journal of Personality and Social Psychology*, 85(2), 197–216. (Source of the D-score metric).
* **Cohen, J. (1988).** *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates. (Source for effect size metrics).

## 5. Conclusion

The shift from ANOVA to a Permutation Test represents a rigorous adaptation to the specific characteristics of the data (IAT D-scores with visual complexity manipulations). This approach ensures that the statistical inferences drawn regarding the influence of visual complexity on implicit bias are valid, robust, and not artifacts of violated parametric assumptions.

---
*Last Updated: Methodology finalized in alignment with T033a implementation.*