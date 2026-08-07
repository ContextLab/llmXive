# Methodology: P-Value Distribution Analysis

## Overview

This document outlines the statistical methods used to analyze the distribution of p-values obtained from hypothesis tests on synthetic data. The goal is to quantify deviations from the expected uniform distribution under the null hypothesis, indicating anti-conservative bias.

## Reference Standard: Permutation Test

To establish a ground truth (Gold Standard) that respects the specific correlation structure of the data, we employ a permutation-based reference.

**Procedure:**
1. **Data Pooling**: Combine observations from both groups.
2. **Permutation**: Randomly shuffle group labels $B$ times (e.g., $B=1000$).
3. **Re-calculation**: For each permutation, compute the test statistic (t-statistic or F-statistic).
4. **P-Value Construction**: The empirical p-value for a given permutation is the proportion of permuted statistics as extreme as or more extreme than the observed statistic.
5. **Distribution**: The collection of these permuted p-values forms the reference distribution, which is theoretically uniform under the null, even in the presence of complex correlation structures.

**Implementation:**
- **Function**: `generate_permutation_reference` in `code/analyze_pvalues.py`

## Deviation Quantification: Kolmogorov-Smirnov (KS) Statistic

We quantify the deviation of the observed p-value distribution from the theoretical uniform distribution (or the permutation reference) using the KS statistic.

**Definition:**
$$ D_{n} = \sup_{x} |F_n(x) - F(x)| $$
Where:
- $F_n(x)$ is the empirical cumulative distribution function (ECDF) of the observed p-values.
- $F(x)$ is the CDF of the reference distribution (Uniform(0,1) or the permutation reference).
- $\sup$ denotes the supremum (maximum) distance.

**Interpretation:**
- A KS statistic close to 0 indicates the p-values are uniformly distributed (valid test).
- A large KS statistic indicates significant deviation, suggesting the test is anti-conservative (too many small p-values) or conservative.

**Implementation:**
- **Function**: `calculate_ks_statistic` in `code/analyze_pvalues.py`

## Visual Inspection: QQ-Plots

Quantile-Quantile (QQ) plots provide a visual tool to assess the distribution of p-values.

**Construction:**
- **X-axis**: Theoretical quantiles of the Uniform(0,1) distribution (or permutation reference).
- **Y-axis**: Ordered empirical p-values.
- **Reference Line**: The line $y=x$.

**Interpretation:**
- Points falling on the line indicate agreement with the null.
- Points deviating below the line (concave curve) indicate an excess of small p-values (anti-conservative).
- Points deviating above the line indicate a deficit of small p-values (conservative).

**Implementation:**
- **Function**: `generate_qq_plot` in `code/plot_qq.py`

## Confidence Intervals: Bootstrap Analysis

To assess the stability of the KS statistic, we calculate bootstrap confidence intervals.

**Procedure:**
1. Resample the p-values with replacement $M$ times (e.g., $M=1000$).
2. Calculate the KS statistic for each bootstrap sample.
3. Determine the percentile-based confidence interval (e.g., 2.5th and 97.5th percentiles).

**Implementation:**
- **Function**: `calculate_bootstrap_ci` in `code/bootstrap_ci.py`
- **Output**: Results stored in `data/results/bootstrap_cis.json`.

## Sensitivity Analysis

We perform a sensitivity analysis by sweeping over the correlation parameter $\rho \in \{0, 0.1, 0.3, 0.5, 0.7, 0.9\}$. This allows us to map how the validity of p-values degrades as the correlation structure becomes more complex, providing a quantitative measure of the "high-dimensional instability" effect.

**Implementation:**
- **Function**: `run_sensitivity_analysis` in `code/sensitivity_analysis.py`