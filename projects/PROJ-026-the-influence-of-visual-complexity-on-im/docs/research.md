# Research Methodology: The Influence of Visual Complexity on Implicit Bias

## Overview

This document outlines the statistical methodology and analytical framework used to investigate the relationship between visual complexity and implicit bias scores (D-scores).

## Methodological Shift: From ANOVA to Permutation Test

### Original Plan
The initial design proposed using Analysis of Variance (ANOVA) to compare D-scores across different levels of visual complexity (Low, Medium, High).

### Rationale for Change
ANOVA relies on several strict assumptions:
1. **Normality**: Residuals must be normally distributed.
2. **Homogeneity of Variance**: Variances across groups must be equal.
3. **Independence**: Observations must be independent.

In the context of this study, the **stimulus-set** introduces a significant confound. Images are not interchangeable; specific visual features of a single image can drive bias scores independently of the "complexity" category. ANOVA struggles to disentangle the effect of the *category* from the *specific stimulus* without a complex mixed-model design that may be underpowered given typical sample sizes.

### The Permutation Test Solution
We have adopted a **Permutation Test** (also known as a Randomization Test) as the primary inferential method.

**Justification:**
1. **Distribution-Free**: Does not assume normality of the data.
2. **Stimulus-Set Robustness**: By permuting the labels of complexity categories relative to the observed D-scores (while keeping the stimulus structure intact in the resampling logic), we can directly test the null hypothesis that the assignment of complexity levels to images has no effect on D-scores.
3. **Exact P-values**: Provides an exact p-value based on the empirical distribution of the test statistic under the null hypothesis.

**Citation & Reference:**
This approach aligns with recommendations for small-sample and complex-design behavioral studies, such as those discussed in:
- *Good, P. (2005). Permutation, Parametric, and Bootstrap Tests of Hypotheses.*
- *Edgington, E. S., & Onghena, P. (2007). Randomization Tests.*

## Analytical Pipeline

1. **Stimulus Quantification**:
 - Compute Edge Density, Shannon Entropy, and Fractal Dimension for each image.
 - Categorize images into Low/Medium/High complexity using quantile-based binning (`pandas.qcut`).

2. **D-Score Aggregation**:
 - Apply Greenwald D2 algorithm to raw IAT response times.
 - Filter trials based on latency (<300ms or >10000ms) and error rates.
 - Exclude participants with <10 valid trials.

3. **Statistical Inference**:
 - **Primary Test**: Permutation Test comparing mean D-scores across complexity groups.
 - **Effect Size**: Cohen's d calculated on the observed data.
 - **Sensitivity Analysis**:
 - **LOIO (Leave-One-Image-Out)**: Iteratively remove one image and re-run the test to assess stability.
 - **Threshold Sweep**: Vary complexity boundaries by ±0.05, ±0.10, ±0.15 SD to check robustness of categorization.

4. **Power Analysis**:
 - Post-hoc power calculation using `statsmodels` to determine the probability of detecting the observed effect size given the sample size.

## Assumptions and Limitations

- **Sample Size**: Permutation tests are computationally intensive; we limit permutations to a stable number (e.g., 10,000) suitable for CPU-only execution.
- **Stimulus Selection**: The validity of the "stimulus-set" assumption relies on the diversity of the image pool.
- **Null Effect Mode**: For CI/CD, a synthetic null-effect mode is available, which generates data where complexity has no relationship to D-scores.
