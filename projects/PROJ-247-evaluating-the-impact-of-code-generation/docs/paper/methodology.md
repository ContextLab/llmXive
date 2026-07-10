# Methodology: Statistical Analysis of Code Maintainability

## Overview

This document details the statistical methodology employed to evaluate the impact of LLM-generated code versus human-written code on long-term maintainability. The analysis relies on data processed through the pipeline stages: dataset curation (US1), longitudinal metric extraction (US2), and statistical testing (US3).

## 1. Data Structure and Matching

### 1.1 Propensity Score Matching
To mitigate confounding variables, we employ **1:1 Nearest Neighbor Propensity Score Matching**.
- **Treatment Group**: Code blocks tagged as "LLM-generated" (confidence ≥ 0.8).
- **Control Group**: Code blocks tagged as "Human-written" (confidence ≥ 0.8).
- **Covariates**:
 - **Block-level**: Cyclomatic complexity, nesting depth, Lines of Code (LOC) (extracted via `radon`).
 - **Repository-level**: Star count, repository age (days since creation).
- **Matching Logic**: Matches are performed within the same repository to control for project-specific context. The `code/utils/matching.py` module implements this using Euclidean distance on standardized propensity scores.

### 1.2 Data Filtering
- **Refactoring Exclusion**: Blocks identified as moved via `git mv` are excluded to prevent churn artifacts unrelated to code quality.
- **Inclusion Criteria**: Repositories with fewer than 5 LLM and 5 Human blocks are excluded to ensure statistical power.

## 2. Statistical Testing: Wilcoxon Signed-Rank Test

### 2.1 Rationale for Test Selection
As documented in `docs/paper/constitution_amendment.md` (amendment to Constitution Principle VI), we utilize the **Wilcoxon Signed-Rank Test** rather than the Mann-Whitney U test.
- **Paired Nature**: The data consists of matched pairs (LLM block vs. Human block within the same repository). The Wilcoxon test is specifically designed for dependent (paired) samples.
- **Non-Normality**: Maintainability metrics (churn, latency) typically exhibit skewed distributions with outliers. The Wilcoxon test is a non-parametric test that does not assume normality, making it robust against these deviations.

### 2.2 Implementation
The test is implemented in `code/03_analysis.py` using `scipy.stats.wilcoxon`.
- **Null Hypothesis ($H_0$)**: The median difference between the paired observations (LLM - Human) is zero.
- **Alternative Hypothesis ($H_1$)**: The median difference is not zero.
- **Metrics Tested**:
 1. Code Churn (lines added/deleted per month).
 2. Bug Fix Latency (days from commit to fix).

## 3. Multiple Comparisons Correction: Benjamini-Hochberg (BH)

### 3.1 The Problem of Multiple Testing
We perform hypothesis tests across multiple metrics (e.g., churn, latency) and potentially across different time windows. Conducting multiple tests increases the Family-Wise Error Rate (FWER), leading to a higher probability of false positives (Type I errors).

### 3.2 Benjamini-Hochberg Procedure
To control the **False Discovery Rate (FDR)** rather than the stricter FWER, we apply the Benjamini-Hochberg correction to the raw p-values obtained from the Wilcoxon tests.

**Algorithm**:
1. Let $m$ be the total number of hypotheses (tests) performed.
2. Order the raw p-values from smallest to largest: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
3. For each $p_{(i)}$, calculate the adjusted p-value (or critical value):
 $$ p'_{(i)} = \frac{p_{(i)} \times m}{i} $$
 Where $i$ is the rank of the p-value.
4. Ensure monotonicity: $p'_{(i)} = \min(p'_{(i)}, p'_{(i+1)})$ working backwards from $m$ to 1.
5. Reject $H_0$ for all hypotheses where $p'_{(i)} < \alpha$ (where $\alpha = 0.05$).

### 3.3 Assumptions and Verification
The Benjamini-Hochberg procedure relies on specific assumptions regarding the dependency structure of the test statistics:

**Assumption 1: Independence or Positive Regression Dependency**
- **Requirement**: The test statistics should be independent, or satisfy the condition of Positive Regression Dependency on each of the subsets (PRDS).
- **Verification in this Study**:
 - The metrics tested (Churn vs. Latency) are distinct dimensions of maintainability. While they may be correlated within a single code block, the correlation is generally positive (high churn often correlates with high latency in complex bugs).
 - PRDS holds for positively correlated test statistics. Since code complexity tends to drive both metrics in the same direction, the dependency structure satisfies the PRDS condition, making BH valid and more powerful than Bonferroni.
- **Code Traceability**: The implementation of this correction is found in `code/03_analysis.py` within the `apply_benjamini_hochberg_correction` function.

**Assumption 2: Validity of Individual P-values**
- **Requirement**: The input p-values must be valid (uniformly distributed under the null).
- **Verification**: The Wilcoxon Signed-Rank test is an exact non-parametric test (or asymptotic approximation for large $n$), ensuring the validity of the input p-values provided the matching was performed correctly.

**Assumption 3: Fixed Number of Hypotheses**
- **Requirement**: The number of tests ($m$) must be determined prior to looking at the data.
- **Verification**: The analysis plan pre-specifies the metrics to be tested (Churn, Latency). No data-driven selection of metrics occurred after observing the results.

### 3.4 Implementation Details
The correction logic in `code/03_analysis.py` follows these steps:
1. Collect all raw p-values from `run_wilcoxon_tests`.
2. Sort p-values and retain original indices.
3. Compute rank-based thresholds.
4. Adjust p-values to ensure monotonicity.
5. Output the FDR-adjusted p-values to `data/processed/statistical_results.json`.

## 4. Sensitivity Analysis

To account for potential misclassification in the "LLM" vs. "Human" labels, we perform a sensitivity analysis using the precision and recall metrics derived from the ground truth subset (`data/ground_truth/manual_labels.csv`).
- **Source**: `code/05_classifier_evaluation.py` calculates these metrics.
- **Threshold**: We verify against the SC-006 threshold of 0.85 precision/recall.
- **Adjustment**: If misclassification rates are significant, effect sizes are adjusted using the inverse of the classification accuracy to estimate the "true" effect size.

## 5. Power Analysis

A post-hoc power analysis is conducted using `scipy.stats.power_analysis` to ensure the study was sufficiently powered (target $\ge 0.80$) given the final matched pair count and observed effect sizes (Cohen's d). This is detailed in `code/03_analysis.py` (Task T031).

## 6. Data Traceability

All results in this methodology trace back to the following artifacts:
- **Input Data**: `data/processed/matched_pairs.csv`, `data/processed/metrics_longitudinal.csv`.
- **Code Logic**: `code/03_analysis.py` (specifically `run_wilcoxon_tests` and `apply_benjamini_hochberg_correction`).
- **Output**: `data/processed/statistical_results.json`, `docs/paper/results_summary.md`.

## References
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. *Journal of the Royal Statistical Society: Series B*.
- Wilcoxon, F. (1945). Individual Comparisons by Ranking Methods. *Biometrics Bulletin*.