# Methodological Note: Statistical Analysis Plan

## Overview

This document outlines the statistical approach for analyzing the influence of visual complexity on implicit bias (IAT D-scores). It details the decision to utilize a **Permutation Test** rather than a traditional Analysis of Variance (ANOVA) for the primary hypothesis testing.

## The Methodological Shift: ANOVA to Permutation Test

### Original Plan (ANOVA)
Initially, the analysis plan considered a standard Analysis of Variance (ANOVA) to compare mean D-scores across different levels of visual complexity (Low, Medium, High). ANOVA relies on several strict parametric assumptions:
1. **Normality**: Residuals must be normally distributed.
2. **Homogeneity of Variance**: Variances across groups must be equal.
3. **Independence**: Observations must be independent (often challenged in within-subject designs without specific corrections).

In the context of visual complexity research, these assumptions are frequently violated:
* **Stimulus-Set Confounds**: Visual stimuli are not interchangeable; a specific "complex" image may possess unique properties (e.g., color contrast, specific patterns) unrelated to the abstract metric of "complexity" that influence the D-score. Standard ANOVA treats stimuli as fixed effects or ignores this clustering, potentially inflating Type I error rates.
* **Non-Normal Distributions**: IAT D-scores often exhibit non-normal distributions, particularly with smaller sample sizes or specific demographic subgroups.
* **Small Sample Sizes**: Research constraints often limit the number of participants, making the Central Limit Theorem less effective at ensuring normality of the sampling distribution.

### Adopted Approach (Permutation Test)
To address these limitations and ensure robust inference, the analysis plan has been revised to employ a **Permutation Test** (also known as a Randomization Test).

**Justification:**
1. **Distribution-Free**: Permutation tests do not assume a specific underlying distribution (e.g., normal) for the data. They derive the null distribution empirically by reshuffling the observed data labels.
2. **Handling Stimulus-Set Confounds**: By implementing a **Leave-One-Image-Out (LOIO)** sensitivity analysis in conjunction with the permutation test, we can assess the stability of the effect across the specific set of stimuli used. This directly addresses the confound where results might be driven by a single outlier image rather than the complexity metric itself.
3. **Exact P-values**: For smaller sample sizes, permutation tests provide exact p-values based on the actual data permutations, offering greater precision than asymptotic approximations used in ANOVA.
4. **Flexibility**: The test statistic can be any metric of interest (e.g., mean difference, Cohen's d), allowing us to directly report the effect size alongside the significance.

### Implementation Details
* **Null Hypothesis ($H_0$)**: There is no difference in IAT D-scores between groups defined by visual complexity levels.
* **Test Statistic**: The mean difference of D-scores between the High-Complexity and Low-Complexity groups.
* **Procedure**:
 1. Calculate the observed test statistic from the actual data.
 2. Randomly shuffle the group labels (complexity categories) across the participants' D-scores.
 3. Recalculate the test statistic for the permuted data.
 4. Repeat steps 2-3 a large number of times (e.g., $N=10,000$) to build the null distribution.
 5. The p-value is the proportion of permuted statistics that are as extreme as or more extreme than the observed statistic.
* **Sensitivity Analysis**:
 * **Threshold Sweep**: Vary the complexity categorization thresholds ($\pm 0.05, \pm 0.10, \pm 0.15$ SD) to ensure results are not artifacts of arbitrary binning.
 * **LOIO**: Iteratively remove one image stimulus from the dataset and re-run the analysis to identify if any single image disproportionately drives the result.

## Conclusion

The shift from ANOVA to a Permutation Test represents a methodological improvement tailored to the specific challenges of visual complexity research. It provides a more robust, assumption-free framework for validating the relationship between visual complexity and implicit bias, ensuring that findings are driven by the complexity metric itself rather than stimulus-specific artifacts or distributional violations.

## References

* Good, P. I. (2005). *Permutation, Parametric, and Bootstrap Tests of Hypotheses*. Springer.
* Edgington, E. S., & Onghena, P. (2007). *Randomization Tests*. Chapman and Hall/CRC.
* Greenwald, A. G., Nosek, B. A., & Banaji, M. R. (2003). Understanding and using the Implicit Association Test: I. An improved scoring algorithm. *Journal of Personality and Social Psychology*, 85(2), 197–216. (Context for D-score usage).