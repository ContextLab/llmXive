# Statistical Methods

This document details the statistical methods employed in the analysis.

## Wilcoxon Signed-Rank Test

- **Purpose**: Compare paired continuous metrics (Cyclomatic Complexity, Halstead Volume) between human-written and LLM-generated code.
- **Hypotheses**:
 - \( H_0 \): The median difference between pairs is zero.
 - \( H_1 \): The median difference is not zero.
- **Assumptions**:
 - Data is paired.
 - Differences are symmetrically distributed.
 - Measurement scale is at least ordinal.
- **Implementation**: `scipy.stats.wilcoxon`

## McNemar's Test

- **Purpose**: Compare paired binary outcomes (Pass/Fail) between two models or human vs. model.
- **Hypotheses**:
 - \( H_0 \): The marginal probabilities are equal.
 - \( H_1 \): The marginal probabilities are not equal.
- **Contingency Table**:
 ```
 | | Model B Pass | Model B Fail |
 |---------------|--------------|--------------|
 | Model A Pass | a | b |
 | Model A Fail | c | d |
 ```
- **Statistic**: \( \chi^2 = \frac{(b - c)^2}{b + c} \)
- **Implementation**: Custom implementation or `statsmodels.stats.contingency.mcnemar`

## Fisher's Exact Test

- **Purpose**: Unpaired exploratory checks for contingency tables (e.g., comparing success rates across different task categories).
- **Hypotheses**:
 - \( H_0 \): The two classifications are independent.
 - \( H_1 \): The two classifications are dependent.
- **Implementation**: `scipy.stats.fisher_exact`

## Permutation Test (Paired)

- **Purpose**: Test for differences in branch coverage without assuming normality.
- **Method**:
 1. Calculate observed difference in means.
 2. Randomly permute signs of differences (multiply by -1 or 1) many times.
 3. Calculate permuted differences.
 4. Compare observed difference to distribution of permuted differences.
- **P-value**: Proportion of permuted differences as extreme as the observed difference.

## Power Analysis

### A Priori Power Analysis
- **Purpose**: Determine the minimum sample size required to detect an effect of a given size with a desired power.
- **Parameters**:
 - Effect size (d): 0.5 (medium)
 - Significance level (α): 0.05
 - Desired power: 0.80
- **Result**: Minimum sample size n ≥ 38.

### Post-Hoc Power Analysis
- **Purpose**: Calculate the achieved power based on observed effect sizes and sample size.
- **Interpretation**: Power ≥ 0.8 indicates a reliable result.

## Correlation Analysis

- **Spearman Correlation**: Non-parametric measure of rank correlation (optional, for exploratory analysis).
- **Point-Biserial Correlation**: Correlation between a continuous variable (e.g., complexity) and a binary variable (e.g., pass/fail).

## Effect Size Interpretation

- **Cohen's d**:
 - 0.2: Small effect
 - 0.5: Medium effect
 - 0.8: Large effect