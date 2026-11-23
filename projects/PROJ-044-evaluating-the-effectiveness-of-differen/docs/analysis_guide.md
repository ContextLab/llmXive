# Analysis Guide: Evaluating Differential Privacy in Federated Learning

## Overview

This guide details the statistical methods and data processing steps used in the analysis phase (User Story 3) of the project.

## Data Filtering

Before any statistical analysis, the raw training logs (`results/raw_logs.csv`) undergo strict filtering to ensure validity.

### 1. Time-Limited Runs
Runs that hit the maximum round limit without reaching the target accuracy are flagged with `is_time_limited = True`.
- **Action**: Excluded from "rounds to target" calculations (SC-001).
- **Function**: `filter_time_limited(df)` in `code/analysis/stats.py`.

### 2. Utility Collapse
Runs with extremely low privacy budgets (e.g., ε=0.01) may result in models that fail to learn (utility collapse).
- **Action**: Excluded from all statistical comparisons.
- **Function**: `filter_utility_collapse(df)` in `code/analysis/stats.py`.

**Result**: The filtered dataset (`results/filtered_data.csv`) is the **only** input for subsequent statistical tests and plotting.

## Statistical Tests

### Paired T-Test (DP vs. Non-DP)
- **Hypothesis**: Tests if the difference in accuracy between DP and Non-DP models (paired by seed) is significantly different from zero.
- **Input**: Filtered data, grouped by seed and configuration.
- **Output**: P-values for each seed comparison.
- **Implementation**: `run_paired_ttest_dp_vs_nondp()` in `code/analysis/stats.py`.

### Unpaired T-Test / Mann-Whitney U (Majority vs. Minority)
- **Hypothesis**: Tests if there is a significant difference in accuracy between majority and minority clients.
- **Logic**:
 - If valid runs ≥ 3: Perform unpaired t-test.
 - If valid runs < 3: Switch to Mann-Whitney U test and flag the result as `power_reduced` in the validation report.
- **Implementation**: `run_unpaired_ttest_majority_vs_minority()` in `code/analysis/stats.py`.

## Sensitivity Analysis

The project performs a sensitivity sweep over the Dirichlet parameter α ∈ {0.05, 0.1, 0.5, 1.0} to evaluate the "critical heterogeneity" hypothesis.
- **Metric**: Accuracy gap and minority degradation curves.
- **Output**: `results/plots/accuracy_gap_vs_alpha.png`.

## Visualization

All plots are generated using `matplotlib` with the following specifications:
- **Format**: PNG
- **Resolution**: 300 DPI
- **Directory**: `results/plots/`

### Key Plots
1. **Accuracy Gap vs. Alpha**: Visualizes the impact of heterogeneity on the DP utility gap.
2. **Accuracy vs. Epsilon**: Shows convergence behavior across different privacy budgets.
3. **Minority Degradation Overlay**: A critical plot mandated by Constitution Principle VII, overlaying minority client accuracy curves against global accuracy curves to highlight fairness impacts.

## Validation Report

The `results/validation_report.md` file summarizes:
- Total runs processed.
- Count of excluded runs (time-limited, utility collapse).
- Statistical power flags (e.g., Mann-Whitney U fallbacks).
- Confirmation of dataset scope (FEMNIST only, Shakespeare excluded).
