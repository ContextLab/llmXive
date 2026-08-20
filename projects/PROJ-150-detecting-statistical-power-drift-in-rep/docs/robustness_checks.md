# Robustness and Sensitivity Analysis

## Overview

To ensure the reliability of the Linear Mixed-Effects Model (LMM) results regarding statistical power drift, this project implements a comprehensive suite of robustness checks. These checks validate the parametric assumptions of the LMM and test the stability of the findings against methodological variations.

## 1. Non-Parametric Permutation Test

**Objective**: To verify that the observed drift slope is not a result of random chance or model misspecification by generating an empirical null distribution.

**Methodology**:
1. **Shuffling**: The `year` labels in the dataset are randomly shuffled while keeping `effect_size`, `sample_size`, and grouping variables constant.
2. **Re-fitting**: The Full LMM is re-fitted on the permuted data to extract a null slope coefficient.
3. **Iteration**: This process is repeated for a large number of iterations (default: 10,000, with fallback to 1,000 under resource constraints).
4. **Empirical P-Value**: Calculated as the proportion of permuted slopes that are as extreme or more extreme than the observed slope.

**Resource Handling**:
* Memory and time monitoring (`psutil`, `time`) ensures the test does not exceed 6 hours or 6GB RAM.
* If limits are exceeded, the test terminates early and flags the result as "approximate".

**Output**: `results/permutation_pvalue.json`

## 2. Sensitivity Analysis (Alpha Sweep)

**Objective**: To determine if the conclusion of "significant drift" is dependent on a specific choice of significance threshold ($\alpha$).

**Methodology**:
1. **Sweep**: The significance threshold is swept across a range of values (e.g., 0.01, 0.05, 0.10, 0.20).
2. **Evaluation**: For each $\alpha$, the LRT p-value is compared to determine if the drift is significant.
3. **Reporting**: A report is generated indicating the stability of the result across the tested range.

**Conclusion**: If the drift is significant across a wide range of $\alpha$ values, the finding is considered robust. If it only holds at specific thresholds, the report highlights this dependency.

**Output**: `results/sensitivity_report.json`

## 3. Cross-Field Aggregation (Meta-Analysis)

**Objective**: To validate that the drift is a general phenomenon across scientific fields and not driven by a single discipline.

**Methodology**:
1. **Stratification**: Data is split by `field`.
2. **Field-Specific Models**: An LMM is fitted for each field to extract the field-specific `year` slope and standard error.
3. **DerSimonian-Laird Weighting**: An inverse-variance weighted meta-analysis is performed to combine these slopes, accounting for heterogeneity ($\tau^2$).
4. **Comparison**: The aggregated drift estimate is compared against the primary LMM slope.

**Output**: `results/aggregated_drift.json` and `results/comparison_aggregated_vs_lmm.json`

## 4. Input Permutation Framework

**Objective**: To test the stability of the drift estimate when the underlying determinants of power (`effect_size`, `sample_size`) are randomized, while holding `year` constant.

**Methodology**:
1. **Shuffling**: `effect_size` and `sample_size` columns are shuffled independently.
2. **Re-fitting**: The LMM is re-fitted on this permuted data.
3. **Null Distribution**: Generates a distribution of slopes expected if the relationship between power inputs and year is random.

**Output**: `results/null_distribution_implied_power.csv`

## Integration

These robustness checks are orchestrated by `code/main.py` and their results are consolidated into the final report. The consistency between the parametric LMM results and these non-parametric/sensitivity checks is a key validation criterion for the project.