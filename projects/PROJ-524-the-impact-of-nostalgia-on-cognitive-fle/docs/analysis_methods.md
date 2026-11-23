# Statistical Analysis Methods

## Overview

This document describes the statistical methods employed in the analysis of nostalgia's impact on cognitive flexibility in aging adults.

## Primary Analysis

### Welch's Independent Samples t-test

The primary hypothesis test compares the means of two independent groups (nostalgia vs. control) on cognitive flexibility metrics:

- Perseverative Errors (WCST)
- Categories Completed (WCST)

**Rationale**: Welch's t-test is chosen over the Student's t-test because:
1. Groups may have unequal variances (heteroscedasticity)
2. Sample sizes between conditions may differ
3. It provides more robust Type I error control under these conditions

**Formula**:
$$t = \frac{\bar{X}_1 - \bar{X}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}}$$

Where:
- $\bar{X}_1, \bar{X}_2$: Group means
- $s_1^2, s_2^2$: Group variances
- $n_1, n_2$: Sample sizes

**Degrees of Freedom** (Welch-Satterthwaite equation):
$$df = \frac{(\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2})^2}{\frac{(\frac{s_1^2}{n_1})^2}{n_1-1} + \frac{(\frac{s_2^2}{n_2})^2}{n_2-1}}$$

### Effect Size: Cohen's d

Cohen's d is calculated to quantify the magnitude of the observed effect:

$$d = \frac{\bar{X}_1 - \bar{X}_2}{s_{pooled}}$$

Where $s_{pooled}$ is the pooled standard deviation.

**Confidence Intervals**: 95% CI calculated using non-central t-distribution approximation.

## Multiple Comparison Correction

### Bonferroni Correction

To control the family-wise error rate when testing multiple outcomes:

$$\alpha_{corrected} = \frac{\alpha}{k}$$

Where $k$ is the number of comparisons (2: perseverative errors, categories completed).

## Power Analysis

### Post-hoc Power Calculation

Statistical power is calculated based on:
- Observed effect size (Cohen's d)
- Sample size per group
- Significance level (α = 0.05)

### Minimum Detectable Effect Size (MDES)

The smallest effect size detectable with 80% power at α = 0.05 is computed.

## Sensitivity Analysis

### Threshold Sweep

Robustness is assessed by re-running analyses at multiple significance thresholds:
- α = 0.01 (strict)
- α = 0.05 (standard)
- α = 0.10 (lenient)

**Borderline Flagging**: P-values within ±0.01 of α are flagged as "borderline" to indicate sensitivity to threshold choice.

### Robustness Check: MMSE Filtering

Participants with Mini-Mental State Examination (MMSE) scores < 24 are excluded to assess whether results are driven by cognitively impaired individuals.

## Assumptions & Limitations

1. **Independence**: Observations are independent within and between groups.
2. **Normality**: Assumed for t-test; robust to moderate violations with large samples.
3. **Random Sampling**: Data assumed to be representative of the target population.
4. **No Outliers**: Extreme values may skew results; outlier detection recommended.

## Software Implementation

All analyses implemented in Python using:
- `scipy.stats`: t-tests, effect sizes
- `numpy`: Numerical operations
- `pandas`: Data manipulation

## References

1. Welch, B. L. (1947). The generalization of 'Student's' problem when several different population variances are involved. Biometrika.
2. Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences.
3. Cumming, G. (2012). Understanding the New Statistics: Effect Sizes, Confidence Intervals, and Meta-Analysis.