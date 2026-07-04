# Statistical Methods Documentation

## Overview

This document details the statistical methods used to analyze the benchmark results, ensuring scientific rigor and reproducibility.

## 1. Block Averaging

To reduce the impact of outliers and system noise, latency measurements are aggregated into blocks.

- **Block Size**: Determined based on statistical power requirements (default: 100 measurements per block).
- **Process**:
 1. Collect 1000 raw latency measurements.
 2. Divide into blocks (e.g., 10 blocks of 100).
 3. Calculate the mean latency for each block.
 4. Use these block averages for subsequent statistical tests.

## 2. Welch's Independent Samples t-test

**Rationale**: The configurations being compared (e.g., `-O2` vs `-O3`) are independent binaries. They do not share the same random seed or execution context in a paired manner. Therefore, Welch's t-test is the appropriate method, overriding ambiguous specifications that might suggest a paired t-test.

**Hypotheses**:
- **Null Hypothesis ($H_0$)**: There is no significant difference in mean latency between the two configurations.
- **Alternative Hypothesis ($H_1$)**: There is a significant difference (two-tailed).

**Threshold**: p-value < 0.05 indicates statistical significance.

**Implementation**:
- Located in `code/analysis/stats.py`.
- Function: `welch_ttest(latency_set_a, latency_set_b)`.
- Returns: t-statistic and p-value.

## 3. Stability Metrics

### L2 Relative Error

$$ \text{L2 Error} = \frac{\| \text{Output}_{\text{optimized}} - \text{Output}_{\text{reference}} \|_2}{\| \text{Output}_{\text{reference}} \|_2} $$

- **Threshold**: 1e-5. Configurations exceeding this are marked as unstable.

### Maximum Absolute Difference

$$ \text{Max Diff} = \max | \text{Output}_{\text{optimized}} - \text{Output}_{\text{reference}} | $$

- Used as a secondary metric to detect localized numerical errors.

## 4. Pareto Frontier Analysis

The Pareto frontier identifies configurations that offer the best trade-off between latency (minimize) and accuracy (minimize error).

- **Exploration Plot**: Includes all numerically stable configurations, with a visual distinction for downsampled runs.
- **Final Plot**: Strictly includes only configurations with error <= 1e-5.

## 5. Handling Outliers and Instability

- **NaN Detection**: Any run producing NaN values is immediately flagged and excluded from statistical analysis.
- **Unstable Runs**: Runs with L2 error > 1e-5 are excluded from the final Pareto frontier but retained in raw logs for audit purposes.
- **Memory Pressure**: Downsampled runs are included in the exploration plot but clearly marked to distinguish them from standard runs.
