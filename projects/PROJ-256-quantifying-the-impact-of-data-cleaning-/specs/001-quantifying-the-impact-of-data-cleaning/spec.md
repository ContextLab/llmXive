# Specification: Quantifying the Impact of Data Cleaning on Statistical Inference

## 1. Introduction

### 1.1 Problem Statement
Data cleaning is a standard step in empirical research, yet its impact on statistical inference (p-values, confidence intervals, effect sizes) is rarely quantified systematically. This study aims to measure how common cleaning strategies (outlier removal, imputation, recoding) alter the results of standard statistical tests (t-tests, linear regression).

### 1.2 Research Question
How do standard data cleaning strategies affect the statistical significance and effect size estimates of common statistical tests on real-world datasets?

### 1.3 Hypothesis
- **H1**: Outlier removal is expected to reduce p-values when outliers are present (increasing significance).
- **H2**: Imputation and recoding are expected to stabilize effect sizes and reduce variance in estimates.

## 2. Methodology

### 2.1 Data Sources
The study will use verified public datasets from the UCI Machine Learning Repository and OpenML.
- **Inclusion Criteria**: Binary outcome variable, numeric predictors, public accessibility.
- **Exclusion Criteria**: Datasets with >80% missing outcome, synthetic data, or proprietary restrictions.
- **Current Dataset List**: UCI HAR, UCI Shopper. (See `data/raw/README.md` for provenance).

### 2.2 Cleaning Strategies
Three strategies will be applied systematically:
1. **Outlier Removal**: IQR method with k=1.5.
2. **Imputation**: Mean, Median, and KNN (k=5) imputation for missing values.
3. **Recoding**: Categorical factor encoding.

### 2.3 Statistical Analysis
- **Tests**: Independent t-tests and Linear Regression (OLS).
- **Metrics**: P-values, 95% Confidence Intervals, Cohen's d / R².
- **Comparison**: Absolute and relative differences between baseline (raw) and cleaned results.

### 2.4 Sample Size Limitation (Amended)
**Note**: Due to the scarcity of suitable public datasets meeting inclusion criteria, this study may proceed with as few as 2 datasets (n=2).
- **Aggregates**: If n < 5, aggregate statistics (median, IQR) of effect shifts are considered unstable and will be omitted.
- **Reporting**: Results will be reported on a per-dataset basis with qualitative directionality assessments.
- **Documentation**: The `data/processed/data_quality_report.md` will explicitly state the final sample size and this limitation.

## 3. Functional Requirements

### FR-001: Dataset Acquisition
The system must download real datasets from verified sources (UCI, OpenML). If a dataset is unavailable, the system must fail loudly (no synthetic fallback).

### FR-002: Cleaning Logic
The system must implement IQR outlier removal, mean/median/KNN imputation, and categorical recoding.

### FR-003: Statistical Analysis
The system must compute t-tests and linear regressions using `scipy.stats` and `statsmodels`.

### FR-004: Reporting
The system must generate:
- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/comparison_report.json`
- `data/processed/data_quality_report.md`
- Visualizations (Forest plot, Heatmap) in `output/figures/`.

## 4. Success Criteria

### SC-001: Real Results
All output JSON files must contain real statistical values (p-values in (0,1), finite CIs). Empty or null results are considered a failure.

### SC-002: Per-Dataset Reporting
For n < 5, the system must produce per-delta reports with qualitative directionality instead of unstable aggregates.

### SC-003: Reproducibility
The pipeline must be reproducible via `python code/main.py` with a fixed random seed.

## 5. Limitations

- **Sample Size**: The study is limited to the number of available public datasets meeting strict criteria (currently n=2).
- **Generalizability**: Findings are specific to the characteristics of the selected datasets (HAR, Shopper).
- **Statistical Power**: With n=2, hypothesis testing on the *shifts* themselves is not possible; only descriptive reporting of shifts is performed.

## 6. Appendix

### 6.1 Data Provenance
- UCI HAR: https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones
- UCI Shopper: https://archive.ics.uci.edu/dataset/459/online+shopper+purchasing+intention

### 6.2 Changelog
- **2026-07-14**: Amended FR-001 and SC-001 to allow n=2 and mandate per-dataset reporting due to data scarcity. Removed corrupted text blocks.