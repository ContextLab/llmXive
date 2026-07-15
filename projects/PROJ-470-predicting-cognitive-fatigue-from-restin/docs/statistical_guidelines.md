# Statistical Interpretation Guidelines

This document provides detailed guidance for interpreting the statistical results produced by the cognitive fatigue prediction pipeline.

## Overview of Statistical Methods

The pipeline employs several statistical techniques:

1. **Correlation Analysis**: Pearson and Spearman correlations between complexity metrics and fatigue scores
2. **Multiple Comparison Correction**: Benjamini-Hochberg procedure to control false discovery rate
3. **Sensitivity Analysis**: Results evaluated at multiple significance thresholds
4. **Effect Size Calculation**: Cohen's r and confidence intervals
5. **Collinearity Diagnostics**: Variance Inflation Factor for multivariate models

## Correlation Analysis

### Choosing Between Pearson and Spearman

**Pearson Correlation** assumes:
- Both variables are normally distributed
- Linear relationship between variables
- Homoscedasticity (constant variance)

**Spearman Correlation** (rank-based) is preferred when:
- Variables are not normally distributed
- Relationship is monotonic but not necessarily linear
- Data contains outliers

The pipeline automatically selects the appropriate method based on Shapiro-Wilk normality test (threshold p < 0.05).

### Interpreting Correlation Coefficients

| Coefficient (r) | Strength | Typical Interpretation |
|-----------------|----------|------------------------|
| 0.00 - 0.10 | Negligible | No practical relationship |
| 0.10 - 0.30 | Small | Weak but potentially meaningful |
| 0.30 - 0.50 | Medium | Moderate relationship |
| 0.50 - 1.00 | Large | Strong relationship |

**Important**: Always consider effect size alongside statistical significance. A large sample size can produce statistically significant but practically trivial correlations.

### Paired vs. Cross-Sectional Analysis

**Paired Analysis (Delta vs Delta)**:
- Compares changes in complexity with changes in fatigue
- Formula: ΔComplexity = Complexity_post - Complexity_pre
- Formula: ΔFatigue = Fatigue_post - Fatigue_pre
- Advantages: Controls for individual baseline differences
- Limitations: Requires both pre- and post-measures

**Cross-Sectional Analysis (Baseline vs Baseline)**:
- Correlates baseline complexity with baseline fatigue
- Advantages: Can be used when only baseline data is available
- Limitations: More susceptible to confounding variables

## Benjamini-Hochberg Correction

### Why Correction is Necessary

When testing multiple hypotheses (e.g., 19 EEG channels), the probability of false positives increases:

- Without correction: 5% of tests will be significant by chance at α = 0.05
- With 19 channels: Expected ~1 false positive per analysis
- With 64 channels: Expected ~3 false positives per analysis

### How Benjamini-Hochberg Works

1. Rank all p-values from smallest to largest
2. For each p-value at rank i (out of m tests), compute critical value: (i/m) × FDR_threshold
3. Find the largest p-value where p ≤ critical value
4. All tests up to and including this rank are significant

### Interpreting Corrected Results

- **q-value**: The Benjamini-Hochberg adjusted p-value
- A q-value < 0.05 means the test is significant after FDR correction
- Tests with q-value > 0.05 are not significant after correction

**Example**:
```
Channel P-value Rank Critical (α=0.05) Significant?
Fz 0.001 1 0.05/19 = 0.0026 Yes
Cz 0.015 5 0.25/19 = 0.013 No
Pz 0.008 3 0.15/19 = 0.0079 No
```

## Sensitivity Analysis

### Purpose

Sensitivity analysis evaluates how results change across different significance thresholds:

- **p ≤ 0.05**: Standard threshold for statistical significance
- **p ≤ 0.01**: More stringent threshold, reduces false positives

### Interpreting Sensitivity Tables

| Threshold | Significant Channels | Interpretation |
|-----------|---------------------|----------------|
| 0.05 | 8 channels | Moderate evidence of relationship |
| 0.01 | 3 channels | Strong evidence for these channels |

- Channels significant at both thresholds: Robust findings
- Channels significant only at 0.05: Weaker evidence, may require replication
- Channels significant only at 0.01: Unexpected; verify data quality

## Effect Size Calculation

### Cohen's r for Correlations

Cohen's r is calculated as:

```
r = sqrt(t² / (t² + df))
```

Where:
- t = t-statistic from correlation test
- df = degrees of freedom (n - 2)

### Confidence Intervals

95% confidence intervals are computed using Fisher's z-transformation:

1. Transform r to z: z = 0.5 × ln((1+r)/(1-r))
2. Compute SE: SE = 1 / sqrt(n - 3)
3. CI for z: z ± 1.96 × SE
4. Transform back to r

### Interpreting Effect Sizes

- **Small (r ≈ 0.1)**: May be meaningful in large samples; consider practical significance
- **Medium (r ≈ 0.3)**: Moderate effect; likely practically significant
- **Large (r ≈ 0.5)**: Strong effect; robust relationship

**Always report**: Effect size, confidence interval, and p-value together.

## Collinearity Diagnostics

### Variance Inflation Factor (VIF)

VIF measures how much the variance of a regression coefficient is inflated due to collinearity with other predictors.

```
VIF_i = 1 / (1 - R²_i)
```

Where R²_i is the R-squared from regressing predictor i on all other predictors.

### Interpreting VIF Values

| VIF | Interpretation |
|-----|----------------|
| 1.0 | No collinearity |
| 1.0 - 5.0 | Moderate collinearity (acceptable) |
| > 5.0 | High collinearity (problematic) |
| > 10.0 | Severe collinearity (requires remediation) |

### Handling High VIF

If VIF > 5:
1. Remove one of the highly correlated predictors
2. Combine correlated predictors (e.g., PCA)
3. Use regularization (ridge regression)
4. Collect more data to reduce standard errors

## Adaptive vs. Degenerative Complexity Changes

### Theoretical Framework

Cognitive fatigue may manifest as either:

1. **Adaptive Simplification**: The brain enters a more efficient, stereotyped state to conserve resources
2. **Degenerative Noise**: Loss of complex neural dynamics due to impaired cognitive function

### Distinguishing Between Mechanisms

**Evidence for Adaptive Simplification**:
- Decreased complexity with decreased performance
- Increased consistency across participants
- Correlation with sleep efficiency
- Reversibility after rest

**Evidence for Degenerative Noise**:
- Increased complexity with decreased performance
- Increased variability across participants
- Correlation with sleep disruption
- Persistence after rest

### Interpretation Guidelines

When complexity decreases with increasing fatigue:
- Consider adaptive simplification if:
 - Effect is consistent across channels
 - Effect size is moderate to large
 - Correlates with behavioral measures
- Consider degenerative noise if:
 - Effect is localized to specific channels
 - High variability across participants
 - No correlation with behavior

When complexity increases with increasing fatigue:
- Consider degenerative noise if:
 - Increased complexity is accompanied by performance decline
 - Effect is widespread across channels
- Consider compensatory mechanisms if:
 - Increased complexity correlates with maintained performance
 - Effect is localized to task-relevant networks

## Reporting Guidelines

### Required Elements

When reporting results, include:

1. **Correlation coefficient** (r or ρ) with 95% CI
2. **P-value** (both raw and corrected)
3. **Effect size** (Cohen's r)
4. **Sample size** (N)
5. **Correction method** (Benjamini-Hochberg, FDR threshold)
6. **Analysis type** (paired or cross-sectional)

### Example Report

"A paired correlation analysis revealed a significant negative relationship between changes in Lempel-Ziv complexity (Fz channel) and changes in fatigue scores (ΔLZC vs ΔFatigue), r(28) = -0.42, 95% CI [-0.63, -0.15], p = 0.003, q = 0.021 (Benjamini-Hochberg corrected, FDR = 0.05). This represents a medium-to-large effect size (Cohen's r = 0.42), suggesting that increased fatigue is associated with decreased signal complexity at the frontal midline. The effect remained significant at the stricter threshold of p ≤ 0.01 (q = 0.035), indicating robust evidence for this relationship."

### Limitations to Address

Always discuss:

1. **Causality**: Correlation does not establish causation
2. **Sample size**: Power limitations and confidence interval width
3. **Generalizability**: Population characteristics and external validity
4. **Measurement error**: Artifact rejection and data quality
5. **Multiple comparisons**: Risk of false positives despite correction
6. **Confounding variables**: Unmeasured factors that may influence results

## Common Statistical Pitfalls

### P-Hacking

Avoid:
- Testing multiple hypotheses without correction
- Selecting only significant results
- Trying different analysis methods until significant

### Overinterpreting Non-Significance

A non-significant result does not prove the null hypothesis:
- Check statistical power
- Consider effect size and confidence intervals
- Avoid "absence of evidence is not evidence of absence"

### Ignoring Effect Size

Statistical significance depends on sample size:
- Large N can produce significant but trivial effects
- Small N may miss meaningful effects
- Always report effect sizes with confidence intervals

### Multiple Testing Without Correction

Running many tests without correction inflates Type I error:
- Use Benjamini-Hochberg or Bonferroni correction
- Report both raw and corrected p-values
- Pre-register analysis plan when possible
