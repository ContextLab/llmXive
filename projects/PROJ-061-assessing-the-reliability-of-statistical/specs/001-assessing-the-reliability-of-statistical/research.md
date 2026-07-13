# Research: Assessing the Reliability of Statistical Power Calculations in Real-World Datasets

## Overview

This research phase defines the dataset strategy, computational methodology, and validation approach for assessing the reliability of statistical power calculations. The primary goal is to quantify the discrepancy between theoretical power estimates (assuming normality/equal variance) and empirical power derived from bootstrapping, specifically under controlled assumption violations.

## Dataset Strategy

The project requires at least 10 diverse public datasets covering continuous, count, and binary outcomes, each with N ≥ 30. All datasets are sourced from the UCI Machine Learning Repository or OpenML, ensuring canonical, checksummable, and versioned sources.

**Verified Datasets**:
The following datasets have been verified for direct URL access and structure. They cover continuous, count, and binary outcomes. For multi-class datasets, a specific binary split is defined to enable the two-sample t-test.

| Dataset Name | Source URL | Outcome Type | Sample Size (N) | Outcome Variable | Grouping Variable / Strategy | Notes |
|:--- |:--- |:--- |:--- |:--- |:--- |:--- |
| Wine Quality (Red) | ` | Continuous | 1599 | `quality` | `pH` (binned: <7 vs ≥7) | Continuous outcome; grouping via median split on pH. |
| Bank Marketing | ` | Binary | 41188 | `y` (yes/no) | `y` | Binary outcome; direct t-test on continuous predictors. |
| Concrete Compressive Strength | ` | Continuous | 1030 | `Concrete compressive strength` | `Cement` (binned: <300 vs ≥300) | Continuous outcome. |
| Wine Quality (White) | ` | Continuous | 4898 | `quality` | `pH` (binned: <7 vs ≥7) | Continuous outcome. |
| Auto MPG | ` | Continuous | 398 | `mpg` | `cylinders` (binned: 4 vs 6+8) | Continuous outcome. |
| Abalone | ` | Count | 4177 | `Rings` (integer) | `Sex` (Male vs Female+Infant) | Count outcome (proxy for age). |
| Heart Disease (Cleveland) | ` | Binary | 303 | `target` | `target` | Binary outcome. |
| Breast Cancer (Wisconsin) | ` | Binary | 569 | `diagnosis` | `diagnosis` | Binary outcome. |
| Pima Indians Diabetes | ` | Binary | 768 | `outcome` | `outcome` | Binary outcome. |
| OpenML: Adult Income | ` | Binary | 32561 | `class` | `class` | Binary outcome (income >50K). |
| Iris | ` | Continuous | 150 | `sepal_length` | `species` (Setosa vs Versicolor+Virginica) | **Multi-class**: Binary split defined as Setosa vs Rest to enable t-test. |
| Wine | ` | Continuous | 178 | `alcohol` | `class` (Class 1 vs Class 2+3) | **Multi-class**: Binary split defined as Class 1 vs Rest. |

*Note on Source Verification*: All URLs point to the UCI Machine Learning Repository or OpenML API. These are canonical sources. Checksums will be computed upon download to ensure data integrity (Constitution Principle III).

*Note on Multi-Class Handling*: For datasets with >2 classes (Iris, Wine), a specific binary split is pre-defined (e.g., Class 1 vs. Class 2+3) to create a valid two-sample t-test scenario. This split is recorded in the `grouping_definition` field of the output schema to ensure the effect size is a function of this controlled split, addressing the concern that arbitrary binning introduces confounding. The analysis treats this split as a fixed experimental condition.

## Methodology

### 1. Theoretical Power Calculation (FR-002)
- **Method**: Closed-form approximation for two-sample t-test.
- **Assumptions**: Normality, equal variance, fixed effect size (Cohen's d = 0.5, 0.8).
- **Tool**: `statsmodels.stats.power.tt_solve_power`.
- **Input**: Sample size (n1, n2), alpha (0.05), effect size.
- **Baseline**: Calculated on the **original, unperturbed** data distribution parameters (pooled SD, N) to establish the "Ideal" theoretical power.

### 2. Empirical Power via Bootstrapping (FR-003)
- **Method**: Monte Carlo simulation (1,000 iterations).
- **Procedure**:
 1. **Group Definition**:
 - **Natural Binary**: For datasets with a natural binary outcome (e.g., Breast Cancer, Bank Marketing): Use the outcome variable as the grouping factor.
 - **Pre-defined Binary Split**: For multi-class datasets (e.g., Iris, Wine): Use the pre-defined binary split (e.g., Setosa vs Rest) as the grouping factor.
 - **Synthetic Shift**: For continuous/count datasets without a natural binary grouping (e.g., Wine Quality, Concrete): Randomly split the data into two equal groups. Add a fixed offset to Group B such that the mean difference equals the target Cohen's d (0.5 or 0.8) multiplied by the pooled standard deviation of the original data. This creates a known ground truth effect size.
 2. **Bootstrap Loop**:
 - Resample with replacement from Group A and Group B.
 - **Mean Shifting**: If the original data did not have a natural effect size (Synthetic Shift case), add the target mean difference to the resampled Group B to ensure the simulation tests the specific alternative hypothesis (d=0.5).
 - Perform t-test.
 - Record if p-value < 0.05.
 3. Empirical Power = (Count of significant results) / 1000.
- **Constraint**: CPU-only, no GPU.

### 3. Violation Induction (FR-004, US-2)
- **Heavy-Tailed Noise**: Inject t-distribution noise (df=3) or replace tails with t-distribution values at a contamination rate (e.g., [deferred]). Applied to all datasets.
- **Autocorrelation (AR(1))**: **Conditional Application**. Only applied to datasets with an explicit time index (e.g., if a time column exists). For cross-sectional data (e.g., Wine, Bank), this violation is **skipped** and logged as "N/A - No Time Index". This prevents creating spurious structures.
- **Effect Size Heterogeneity**: Mix sub-populations with different means (separated by 1.5 SD) to simulate heterogeneous effects. Applied to all datasets.
- **Validation (FR-009)**: Log `achieved_magnitude` (e.g., actual AR coefficient calculated from perturbed data, or actual contamination rate).

### 4. Bias Calculation (FR-005)
- **Definition**: Bias = | **Theoretical Power (on Clean Data)** - **Empirical Power (on Perturbed Data)** |.
- **Rationale**: This isolates the impact of the violation. We compare the *ideal* theoretical expectation (based on clean data parameters) against the *actual* empirical performance under the violation. This avoids the circularity of calculating theoretical power on perturbed data where assumptions are violated.
- **Relative Error**: Absolute Error / Theoretical Power (Clean).

### 5. Sensitivity Analysis (FR-006, US-3)
- **Thresholds**: 0.01, 0.05, 0.10.
- **Output**: Count/percentage of datasets classified as "high bias" for each threshold.

### 6. Validation & Reliability Checks
- **Synthetic Ground Truth (FR-008)**: Run on fully synthetic data with known parameters. Verify bootstrap recovery rate is within 5% of true power.
- **Bootstrap Stability Check (FR-010)**:
 - **Metric**: Coefficient of Variation (CV) of the **p-value distribution** across the 1000 bootstrap iterations.
 - **Logic**: Power is a proportion derived from p-values. If the p-values are highly unstable (high CV), the power estimate is unreliable.
 - **Threshold**: If CV > 0.10, flag the empirical power estimate as "unreliable" and exclude it from the final bias calculation. This directly measures the stability of the estimator, not the underlying data variance.

## Compute Feasibility Analysis

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Workload**: 10 datasets × 3 violation types (max) × 1000 iterations = 30,000 bootstrap simulations.
- **Estimation**:
 - A single t-test bootstrap on N=500 takes ~0.01s.
 - [deferred] × 0.01s = 300s (5 minutes) for core logic.
 - Overhead (I/O, data loading, logging) estimated at 2x.
 - Total runtime ≈ 10-15 minutes, well within the 6-hour limit.
- **Memory**: Datasets are small (N < 50,000). Memory usage will be < 1GB.
- **Strategy**: No GPU, no heavy libraries. Use `numpy` and `scipy` which have efficient CPU implementations.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Size < 30** | Bootstrap invalid. | Filter datasets in `loaders.py`; skip or flag as "insufficient sample size". |
| **Missing Values** | Bias in bootstrap. | Drop missing values (listwise deletion) as per Assumptions. |
| **Autocorrelation in Non-Time Data** | Violation cannot be applied. | Detect data type; skip AR(1) for non-ordered data and log warning (see Methodology Section 3). |
| **Bootstrap Variance Mismatch** | Unreliable empirical power. | Implement FR-010 (CV of p-values); exclude flagged results from bias calculation. |
| **Runtime > 6h** | Job failure. | Parallelize bootstrap iterations if possible (though single-threaded is safe); optimize loops. |
| **Arbitrary Splitting in Multi-Class Data** | Effect size depends on split choice. | **Mitigation**: Pre-define specific binary splits (e.g., Class 1 vs Rest) and record them in `grouping_definition`. Treat the split as a controlled experimental variable, not an arbitrary choice. |

## Decision Rationale

- **Synthetic Shift**: Chosen to create a known ground truth for continuous data, avoiding arbitrary splits that introduce unknown effect sizes.
- **Pre-defined Binary Splits**: For multi-class data, a specific split is chosen to enable t-test analysis. This is recorded to ensure transparency and reproducibility, addressing the concern of arbitrary binning.
- **Conditional AR(1)**: Essential to maintain methodological soundness; autocorrelation is a time-series property and cannot be meaningfully injected into cross-sectional data.
- **Bias Definition**: Comparing Clean Theoretical vs. Perturbed Empirical isolates the violation's impact, avoiding the mathematical incoherence of applying normal-theory formulas to non-normal data.
- **Bootstrap Stability (CV)**: Directly measures the stability of the power estimator (proportion of rejections), which is the correct metric for reliability.
