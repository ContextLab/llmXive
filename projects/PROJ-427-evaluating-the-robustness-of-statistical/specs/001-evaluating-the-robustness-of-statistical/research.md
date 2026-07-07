# Research: Evaluating the Robustness of Statistical Methods to Common Data Errors

## Overview

This research phase defines the methodology, dataset strategy, and statistical framework for evaluating the robustness of standard statistical tests to common data errors. The goal is to generate empirical evidence on how Type I error rates, confidence interval coverage, and effect size bias degrade as data quality decreases.

## Dataset Strategy

The project will utilize a mix of verified public datasets from the `# Verified datasets` block and synthetic data to ensure ground-truth parameters are known.

| Dataset Name | Source URL | Type | Variables Used | Rationale |
|--------------|------------|------|----------------|-----------|
| UCI HAR (Test) | `https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv` | Numerical | Accelerometer/gyroscope features, Activity Label | High-dimensional numerical data. **Grouping**: Activity label (6 classes) for ANOVA. **Note**: For Type I error, labels will be permuted to establish a true null. For Power analysis, original labels are used. |
| UCI Shopper | `https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet` | Mixed | Time Spent, Purchase Amount (validated), Categorical flags | Contains numerical and categorical variables. **Validation**: Script checks for 'Purchase Amount' or 'Time Spent' numeric columns. If missing, fallback to synthetic data for regression. |
| MCAR (Malawi) | `https://huggingface.co/datasets/mcarthuradal/malawi/resolve/main/booklets/bk0-00000-of-00001.parquet` | Numerical | Household income, asset counts | Real-world survey data for MCAR missingness simulation. |
| Synthetic Null | N/A (Generated) | Numerical | N/A | Generated via `code/generate_synthetic.py` to establish true null hypothesis (no effect) for valid Type I error measurement. |
| Synthetic Effect | N/A (Generated) | Numerical | N/A | Generated with known effect size to validate bias measurements and CI coverage (ground truth known). |

**Note**: 'UCI DROP' has been removed from the primary list as it is a text-based NLP dataset not suitable for direct numerical statistical testing without complex feature extraction. The plan relies on synthetic data for pure numerical regression validation if UCI Shopper lacks the required variables.

**Note**: Only verified datasets from the provided block are used. If a dataset lacks specific variable types, synthetic data is generated (FR-006) rather than fabricating data or using unverified sources.

## Statistical Methodology

### Error Injection Protocol
Per Constitution Principle VI, errors will be injected at varying rates:
1.  **Random Value Replacement**: Numerical values replaced with uniform random draws from the observed min/max range.
2.  **Category Misclassification**: Categorical values swapped with other valid categories at random.
3.  **MCAR Missingness**: Values replaced with `NaN` randomly across the dataset.

### Statistical Tests
The following tests will be executed on both clean and corrupted data:
-   **t-test**: For comparing means of two groups (using synthetic or binning-derived groups if necessary).
-   **ANOVA**: For comparing means of >2 groups (using HAR activity labels).
-   **Chi-squared**: For independence of categorical variables.
-   **Linear Regression**: For continuous outcome prediction.

### Metrics Calculation
-   **Type I Error Rate**: Proportion of simulations where $p < 0.05$ under a **True Null**.
    -   *Synthetic Data*: Null is known by construction (mean=0).
    -   *Real Data*: Null is established **only** via label permutation (shuffling outcome vs. predictors) to break existing associations.
-   **CI Coverage**: Proportion of 95% confidence intervals that contain the **true population parameter**.
    -   *Synthetic Data*: True parameter is known (FR-006).
    -   *Real Data*: **Not calculated** against sample mean (circular validation). Instead, we measure **Estimate Stability** (variance of coefficients across error rates) and **Bias relative to a robust bootstrap baseline** (high-iteration bootstrap on clean data).
-   **Effect Size Bias**: Absolute difference between estimated effect size and true effect size (synthetic only) or bootstrap baseline (real data).

### Power and Sample Size
Given the 6-hour runtime limit on free-tier CI, the simulation targets **1,000 iterations** per configuration to achieve a standard error of a minimal magnitude for Type I error (sufficient to distinguish 0.05 from 0.07). If runtime exceeds a predefined threshold, the iteration count will be reduced. as a fallback, with a note in the results acknowledging the wider confidence intervals. This is a necessary trade-off between statistical precision and computational feasibility.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use Synthetic Data for Null Hypothesis | Real datasets rarely have a known "true null" without permutation. Generating synthetic data with known parameters (FR-006, FR-007) ensures valid Type I error measurement. |
| MCAR via Listwise Deletion | Consistent with standard practice for MCAR mechanisms and avoids bias from imputation in this robustness study. |
| Uniform Distribution for Replacement | Prevents introducing impossible values (e.g., negative age) while maximizing noise impact. |
| [deferred] Iterations (Target) | Balances statistical stability (SE ~0.007) with the 6-hour runtime constraint. Fallback to 500 if needed. |
| HAR Analysis Strategy | HAR will be used for ANOVA (Power degradation) and Type I error (via label permutation). Original labels are not used for Type I error as the null is false. |

## Limitations

-   **Runtime Constraints**: The simulation is limited to a sufficient number of iterations per configuration. If this exceeds 6 hours, the iteration count is reduced to 500, increasing the uncertainty of the degradation metrics.
-   **Dataset Availability**: Only verified datasets from the provided block are used. If a dataset lacks specific variable types, synthetic data is used.
-   **Computational Power**: No GPU acceleration is available; all operations must be CPU-tractable.
-   **Real-Data CI Coverage**: True CI coverage cannot be measured for real-world datasets as the population parameter is unknown. We substitute this with Estimate Stability and Bootstrap Bias metrics.

## References

-   UCI HAR Dataset: `https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv`
-   UCI Shopper Dataset: `https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet`
-   MCAR Malawi Dataset: `https://huggingface.co/datasets/mcarthuradal/malawi/resolve/main/booklets/bk0-00000-of-00001.parquet`