# Research: Evaluating the Robustness of Statistical Methods to Common Data Errors

## Objective

To quantify the degradation of statistical inference (Type I error inflation, CI coverage loss, effect size bias) when standard tests are applied to datasets with controlled errors.

## Dataset Strategy

The project utilizes datasets from the `# Verified datasets` block. Since the spec requires diverse data (numerical/categorical) and the verified list contains a mix of formats, the strategy is:

| Dataset Source | URL | Type | Usage |
|----------------|-----|------|-------|
| UCI HAR (CSV) | ` | Numerical (Activity Recognition) | T-test, ANOVA on sensor features. |
| UCI Shopper (Parquet) | ` | Mixed (Categorical/Numerical) | Chi-squared (categorical), Regression (numerical). |
| UCI DROP (Parquet) | ` | Mixed (Reading Comprehension) | Regression, ANOVA on derived scores. |
| Malawi Socio-Economic Survey (Parquet) | ` | Numerical/Socio-economic | Baseline for *injecting* MCAR errors (Standard survey data). |
| UCI Wine Quality (Red) (CSV) | `https://huggingface.co/datasets/UCI/wine-quality/resolve/main/winequality-red.csv` | Numerical (Quality Ratings) | ANOVA (comparing pH/alcohol across quality levels). |

**Note on Variable Fit**: The spec requires testing specific statistical assumptions (e.g., normality for t-test). The implementation will include a pre-processing step to verify variable types and sample sizes (N ≥ 30) before applying tests. If a dataset lacks a required variable type (e.g., no categorical column for Chi-squared), that specific test-dataset combination is skipped, and the reason is logged.

## Methodology

### 1. Ground Truth Generation (FR-006, FR-007)

To ensure valid measurement of Type I error and Bias, we distinguish between two data generation modes:

- **Null Generation (for Type I Error)**: Generate synthetic datasets where the Null Hypothesis is **TRUE** (e.g., $\mu_1 = \mu_2$ for t-test, all group means equal for ANOVA). Error injection is applied to these datasets to measure the rate of false rejections.
- **Effect Generation (for Power/Bias)**: Generate synthetic datasets where the Alternative Hypothesis is **TRUE** (e.g., $\mu_1 \neq \mu_2$ with a known effect size $\delta$). Error injection is applied to measure the bias in the estimated effect size and the loss of power.

**Real-World Data Handling**: For real-world datasets, the "Ground Truth" is approximated by the **Clean Sample Estimate**. Bias and Coverage for real-world data are calculated relative to the statistics derived from the clean version of the *same* dataset (treating the clean sample as the best available proxy), while synthetic data uses the known population parameters. This distinction is critical: Real-World results measure *relative degradation* (Clean vs. Corrupted), while Synthetic results measure *absolute accuracy* against truth.

### 2. Error Injection (FR-002)

- **Rates**: [deferred], [deferred], [deferred], [deferred].
- **Mechanisms**:
 - *Random Value Replacement*: Replace $X_{ij}$ with $U(\min(X), \max(X))$. This introduces a uniform component, potentially violating normality assumptions. The study explicitly tests robustness to this specific distributional shift.
 - *Category Misclassification*: Swap category labels with probability $p$.
 - *MCAR Missingness*: Set $X_{ij} = \text{NaN}$ with probability $p$.

### 3. Statistical Analysis (FR-003)

- **Tests**: `scipy.stats.ttest_ind`, `scipy.stats.f_oneway`, `scipy.stats.chi2_contingency`, `statsmodels.OLS`.
- **Handling**: Listwise deletion for missing data (MCAR).

### 4. Metric Calculation (FR-004, SC-001, SC-002, SC-003)

- **Type I Error**: Proportion of rejections ($p < 0.05$) under true null (Synthetic Null Data).
- **CI Coverage**: Proportion of 95% CIs containing the **Original Clean Truth** (Synthetic Population Parameter or Clean Sample Estimate).
- **Bias**: $| \hat{\theta}_{corrupted} - \theta_{clean\_truth} |$. *Note: Bias is always measured against the original clean truth, never the corrupted parameter.*
- **Power**: Proportion of rejections under true alternative.
- **Effective Sample Size**: Mean N remaining after listwise deletion.

## Statistical Rigor & Assumptions

- **Power & Sample Size**:
 - **Minimum N**: Iterations where listwise deletion results in $N < 30$ are **skipped** and logged. This ensures Type I error is only measured where the test assumptions (approximate normality via CLT) are likely to hold.
 - **Power Loss**: We explicitly report "Effective N" and "Power Estimate" alongside Type I error. For MCAR, listwise deletion reduces power (fewer rejections) but should not inflate Type I error. Distinguishing these prevents the conflation of power loss with error inflation.
- **Multiple Comparisons**: Not applicable for the primary metric aggregation (we are measuring the *rate* of error, not testing a hypothesis about the rate itself). However, if comparing degradation curves, Bonferroni correction will be applied.
- **Causal Claims**: None. This is a simulation of data corruption. The "degradation" is a measured phenomenon, not a causal claim about real-world data collection.
- **Distributional Assumptions**: The "Random Value Replacement" mechanism introduces non-normality. The study explicitly acknowledges that observed degradation may be due to the violation of the normality assumption caused by the error injection itself. Results are interpreted as "Robustness to Non-Normality induced by Data Error".
- **Measurement Validity**: Standard parametric tests are used; their validity relies on assumptions (normality, homoscedasticity) which are checked on the *clean* synthetic data.

## Compute Feasibility

- **Hardware**: 2 CPU, 7GB RAM.
- **Strategy**:
 - Datasets are small (typically < 100MB).
 - Simulations are parallelized across CPU cores using `multiprocessing` (limit to 2 workers).
 - Iterations capped to ensure < 6h runtime.
 - No GPU libraries (e.g., PyTorch) used; `scipy` and `statsmodels` are CPU-native.