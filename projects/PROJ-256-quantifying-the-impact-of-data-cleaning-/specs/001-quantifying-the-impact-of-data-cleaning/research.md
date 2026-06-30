# Research: Quantifying the Impact of Data Cleaning on Statistical Inference

## Research Question
How do different data cleaning strategies (outlier removal, missing value imputation, data type correction) quantitatively **change** p-values, confidence intervals, and effect sizes in common statistical tests?

> **Note**: The study measures **change** (delta) rather than **accuracy** (bias against ground truth). The research question is reframed as "How do strategies change inference" rather than "Do they improve it" due to lack of ground truth.

## Dataset Strategy

The specification (FR-001) requests datasets from the OpenML Small Datasets collection and UCI. However, the **Verified datasets** block provided for this project contains only two verified sources. We must strictly adhere to these verified sources to satisfy Constitution Principle II (Verified Accuracy) and avoid hallucinated URLs.

**Spec Deviation**: FR-001 requires OpenML. No verified OpenML URLs are available. This project uses UCI HAR and UCI Shopper as a fallback. This deviation is logged and requires a spec kickback.

| Dataset Name | Source URL | Format | Suitability |
|:--- |:--- |:--- |:--- |
| **UCI HAR** | ` | CSV | **Suitable**. Contains numeric sensor data. Can be used for t-tests (e.g., activity classification vs. sensor magnitude) and regression. |
| **UCI Shopper** | ` | Parquet | **Suitable**. Contains customer behavior data. Good for regression analysis (e.g., purchase amount vs. visit duration). |

**Data Feasibility Limitation**:
The spec requires ≥10 datasets (SC-006) to compute meaningful medians and IQRs. With only **2** verified datasets, statistical aggregation (median/IQR) is mathematically possible but statistically unstable. The plan will compute these metrics but will explicitly flag them as "Limited Sample (n=2)" in all reports. No other datasets are available in the verified block; we cannot fabricate URLs for OpenML or other UCI datasets.

## Methodology

### 1. Baseline Analysis (Raw Data)
- Load datasets.
- Identify numeric outcome variables and predictors.
- Perform **t-tests** (independent samples) and **linear regressions**.
- Record: p-value, 95% CI, effect size (Cohen's d, R²).

### 2. Cleaning Strategies
- **Outlier Removal**: IQR method with k=1.5. Sensitivity analysis with k=1.0, 2.0.
- **Missing Value Imputation**: Mean, Median, KNN (k=5).
- **Categorical Recoding**: Label encoding for factors.

### 3. Statistical Rigor & Corrections
- **Multiple Comparisons**: Apply Benjamini-Hochberg (BH) procedure to control False Discovery Rate (FDR) at α ≤ 0.05. *Note: Spec FR-007 mentions "family-wise error rate" (FWER), but BH controls FDR. We will implement BH as it is standard for >1 test, but explicitly note this distinction in reports. This is a deviation from the strict text of FR-007.*
- **Bootstrap Variance**: 1000 resamples per metric shift to estimate CI of the shift (Constitution Principle VI). *Fallback: Reduce to 500 if runtime > 5 hours.*
- **Sensitivity Analysis**: Stratify by dataset size (n<50, 50-200, >200) and missingness rate. *Note: With n=2, bins may be empty; logic handles this gracefully by logging a warning and skipping the bin.*
- **False Positive Rate (FPR)**: Generate permutation null datasets (shuffle outcome) to estimate FPR for outlier thresholds. *Note: This estimates Type I error rate under the null, not cleaning-induced bias on real data. With n=2, FPR estimates will have high variance and be flagged as such.*
- **Inconsistency Rate**: Calculate the proportion of datasets where significance status (p ≤ 0.05 vs p > 0.05) changes between baseline and cleaned analysis.

### 4. Computational Constraints
- **Hardware**: CPU-only (2 cores, 7 GB RAM).
- **Strategy**: Use `scipy` and `statsmodels` (closed-form solutions). No deep learning.
- **Optimization**: If bootstrap runtime > 5 hours, reduce iterations to 500 (documented fallback).

## Decision Rationale
- **Why these datasets?** They are the *only* verified sources. Using unverified URLs would violate Constitution Principle II.
- **Why BH over Bonferroni?** BH is more powerful for exploratory research with multiple tests, though the spec mentions FWER. We prioritize statistical power while maintaining error control. This is a deviation from the strict text of FR-007.
- **Why 1000 bootstraps?** Required by Constitution Principle VI. We implement a runtime guard to reduce to 500 if necessary, ensuring the job completes within 6 hours.
- **Why per-dataset reporting?** With n=2, aggregate statistics (median/IQR) are invalid. Per-dataset deltas are the only statistically sound metric.