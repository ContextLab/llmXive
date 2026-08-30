# Design Document: Evaluating Robustness of Statistical Tests

## 1. Introduction
This document outlines the design of the PROJ-483 pipeline, which evaluates how violations of the independence assumption affect the Type I error rate and power of common statistical tests.

## 2. Problem Statement
Standard statistical tests (t-test, ANOVA, Chi-squared) assume independent observations. In real-world data (time series, clustered data, spatial data), this assumption is often violated. This project quantifies the severity of the resulting errors.

## 3. Methodology

### 3.1. Generate-then-Inject Paradigm
To ensure a true null hypothesis ($H_0$), we do not use real data with unknown dependencies as the base. Instead:
1. **Generate**: Create synthetic data where $H_0$ is known to be true (e.g., samples from $N(0,1)$).
2. **Inject**: Apply a specific dependency structure (AR(1), Block Bootstrap, Spatial) with a known strength parameter ($r$).
3. **Test**: Apply the statistical test.
4. **Repeat**: Perform this process $N$ times (e.g., 10,000) to estimate the empirical Type I error rate.

### 3.2. Dependency Models
- **AR(1)**: $X_t = r X_{t-1} + \epsilon_t$. Models temporal autocorrelation.
- **Block Bootstrap**: Resamples blocks of data to simulate hierarchical clustering.
- **Spatial Kernel**: Uses a Gaussian kernel to smooth data based on feature-space distance (proxy for spatial coordinates).

### 3.3. Metrics
- **Type I Error Rate**: Proportion of rejections when $H_0$ is true.
- **Power**: Proportion of rejections when $H_0$ is false (effect injected).
- **Clopper-Pearson CI**: Exact confidence interval for binomial proportions (error rates).
- **Monotonicity Test**: Spearman correlation to verify error rates increase with dependency strength.

## 4. Data Management
- **Source**: Public datasets from UCI and OpenML.
- **Validation**: Datasets must have $N \ge 50$ and appropriate variable types.
- **Storage**: Raw data in `data/raw/`, metadata in `data/manifests/`.

## 5. Implementation Details

### 5.1. Modularity
- **Config**: Centralized parameter management.
- **Injector**: Pluggable dependency injection strategies.
- **Runner**: High-performance simulation loop (vectorized where possible).
- **Metrics**: Aggregation and statistical analysis.

### 5.2. Reproducibility
- All random seeds are controlled via `config.yaml`.
- Checksums are stored for all downloaded data.
- Full logging of simulation parameters and results.

## 6. Edge Cases
- **Small Sample Size**: Datasets with $N < 50$ are skipped and logged.
- **Null Construction Failure**: If a dataset cannot be used to construct a valid null (e.g., highly correlated variables), it is logged in `edge_case_report.json`.
- **Normality Violation**: If injected dependency creates non-normal data that violates test assumptions, the pipeline logs the event but continues (robustness check).

## 7. Future Work
- Extend to non-parametric tests.
- Incorporate more complex dependency structures (e.g., long-memory processes).
- Real-time visualization of simulation progress.
