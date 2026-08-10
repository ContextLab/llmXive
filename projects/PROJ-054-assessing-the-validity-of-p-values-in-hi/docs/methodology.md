# Methodology for Assessing P-Value Validity in High-Dimensional Data

## Overview

This document describes the methodology used to assess the validity of p-values
in high-dimensional data settings where the number of features (p) exceeds or
approaches the number of samples (n).

## Data Generation

### Correlation Structure

Synthetic datasets are generated with controlled correlation structures using
the `generate_correlated_data` function in `code/generate_data.py`. The
correlation matrix is constructed with a specified correlation coefficient ρ
spanning from 0 (no correlation) to 0.9 (strong positive correlation).

### Distributional Violations

To test the robustness of standard hypothesis tests, we introduce distributional
violations including:
- Heavy-tailed distributions (Student's t with low degrees of freedom)
- Skewed normal distributions

These violations are generated using the `generate_distribution_violations`
function.

## Hypothesis Testing

Standard t-tests and F-tests are applied to the generated data using scipy.stats.
The null hypothesis is true by construction (no mean differences between groups).

## Analysis Methods

### Kolmogorov-Smirnov Statistic

We use the KS statistic to measure the maximum deviation between the empirical
distribution of p-values and the theoretical uniform distribution.

### Permutation-Based Gold Standard

A permutation test is used to establish a gold standard reference that respects
the correlation structure of the data.

### Bootstrap Confidence Intervals

Bootstrap resampling is used to calculate confidence intervals for KS statistics,
providing uncertainty estimates for our measurements.

## Worst-Case Scenario

The sensitivity analysis (T031) identifies the worst-case scenario where p-value
validity is most compromised. As shown in the results, at ρ=0.9 with n=100 and
p=1000, the KS deviation reaches 0.389, indicating significant anti-conservative
bias in standard hypothesis tests under high correlation and high dimensionality.

## Reproducibility

All random seeds are recorded in `data/sweep/seed_map.json` to ensure complete
reproducibility of results. Data is regenerated on-the-fly during analysis to
avoid storage of large intermediate files.
