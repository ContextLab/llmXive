# Statistical Analysis Guide

This document describes the statistical methods and procedures used in the Visual Detail and False Memory research pipeline.

## 1. Power Analysis

### Purpose
To determine the minimum sample size required to detect a statistically significant effect with a specified level of confidence.

### Parameters
- **Alpha (α)**: 0.05 (Significance level)
- **Power (1-β)**: 0.80 (Probability of correctly rejecting the null hypothesis)
- **Effect Size (f)**: 0.25 (Medium effect size, Cohen's convention)
- **Test**: Repeated-measures ANOVA

### Implementation
- **Module**: `code/analysis/stats.py`
- **Function**: `calculate_anova_power()`
- **Library**: `statsmodels.stats.power.FTestAnovaPower`

### Output
- **File**: `data/processed/power_analysis.json`
- **Contents**: Required sample size, effect size, power, alpha.

## 2. Repeated-Measures ANOVA

### Purpose
To test for differences in false memory rates across different levels of visual detail (e.g., baseline, enhanced, reduced) within the same participants.

### Hypotheses
- **Null Hypothesis (H₀)**: There is no difference in false memory rates across conditions.
- **Alternative Hypothesis (H₁)**: At least one condition differs from the others.

### Implementation
- **Module**: `code/analysis/stats.py`
- **Function**: `run_repeated_measures_anova()`
- **Library**: `scipy.stats.f_oneway` (or `statsmodels` for full repeated-measures)

### Assumptions
- Normality of residuals.
- Sphericity (if violated, apply Greenhouse-Geisser correction).
- Homogeneity of variance.

## 3. Multiple Comparison Correction

### Purpose
To control the family-wise error rate when performing multiple pairwise comparisons (e.g., Enhanced vs. Reduced, Enhanced vs. Baseline).

### Method
- **Bonferroni Correction**: Adjusted p-value = p-value × number of comparisons.

### Implementation
- **Module**: `code/analysis/stats.py`
- **Function**: `apply_bonferroni_correction()`

### Output
- **File**: `data/processed/bonferroni_results.json`
- **Contents**: Original p-values, adjusted p-values, significance flags.

## 4. False Memory Rate Calculation

### Definition
False Memory Rate = (Number of False Alarms to Lures) / (Total Number of Lure Trials)

- **True Alarm**: Correctly identifying a present detail.
- **False Alarm**: Incorrectly identifying an absent detail as present.
- **Miss**: Failing to identify a present detail.
- **Correct Rejection**: Correctly identifying an absent detail as absent.

### Implementation
- **Module**: `code/analysis/viz.py`
- **Function**: `calculate_false_memory_rates()`

## 5. Visualization

### Purpose
To present the results in an interpretable format, showing mean false memory rates with confidence intervals.

### Method
- **Plot Type**: Bar chart with error bars (95% Confidence Interval).
- **Conditions**: Baseline, Enhanced Detail, Reduced Detail.

### Implementation
- **Module**: `code/analysis/viz.py`
- **Function**: `plot_false_memory_rates()`
- **Library**: `matplotlib.pyplot`

### Output
- **File**: `figures/false_memory_rates.png`
- **Format**: PNG (high resolution).

## 6. Dataset Fit Check

### Purpose
To verify that the simulated data distribution matches the expected theoretical distribution (e.g., normal distribution of false memory rates).

### Method
- **Test**: Kolmogorov-Smirnov test or Shapiro-Wilk test.
- **Comparison**: Simulated data vs. target distribution.

### Implementation
- **Module**: `code/analysis/stats.py`
- **Function**: `check_dataset_fit()`

## 7. Interpretation Guidelines

- **p < 0.05**: Reject the null hypothesis; there is a statistically significant difference.
- **Effect Size**: Report partial eta-squared (η²) for ANOVA.
 - Small: 0.01
 - Medium: 0.06
 - Large: 0.14
- **Confidence Intervals**: If the 95% CI for the difference between conditions does not include zero, the difference is significant.

## 8. Reporting Results

When reporting results in a manuscript:
1. State the statistical test used.
2. Report the F-statistic, degrees of freedom, p-value, and effect size.
3. Include a figure with means and confidence intervals.
4. Discuss the implications in the context of the research question.

**Example**:
> "A repeated-measures ANOVA revealed a significant effect of visual detail on false memory rates, F(2, 58) = 5.67, p =.006, η² = 0.16. Post-hoc tests with Bonferroni correction indicated that false memory rates were significantly higher in the Enhanced condition (M = 0.45, SD = 0.12) compared to the Reduced condition (M = 0.30, SD = 0.10), p =.002."
