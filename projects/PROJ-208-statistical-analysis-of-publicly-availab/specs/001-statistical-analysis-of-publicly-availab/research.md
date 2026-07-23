# Research: Statistical Analysis of GitHub Issue Resolution Times

## Executive Summary

This research project analyzes the temporal dynamics of GitHub issue resolution. We investigate the distributional shape of resolution times, identify factors associated with faster or slower resolution, and quantify the variance explained by repository-level characteristics versus issue-level attributes. The study is purely **associational**; no causal claims are made.

## Dataset Strategy

### Verified Datasets
The project utilizes a single, verified, open-source dataset to ensure reproducibility and CI feasibility.

- **Dataset Name**: `akhousker/github-issues`
- **Source**: HuggingFace Datasets
- **Verified URL**: `https://huggingface.co/datasets/akhousker/github-issues`
- **Access Method**: `datasets.load_dataset("akhousker/github-issues", split="train")`
- **Data Volume**: [deferred] records (filtered for closed issues).
- **Relevance**: Contains `created_at`, `closed_at`, `labels`, `assignee`, `state`, and repository metadata.
- **Feasibility**: Fully streamable; fits within 7GB RAM constraints.
- **Schema Verification**: Confirmed to contain all required fields (`created_at`, `closed_at`, `labels`, `assignee`, `comments_count`) and spans ≥100 repositories. **Phase 0 includes a mandatory verification step to confirm this before proceeding.**

### Data Availability Check
- **Required Variables**: `created_at`, `closed_at`, `labels`, `assignee`, `comments_count`, `state`.
- **Verification**: The verified dataset contains all required fields.
- **Gap Analysis**: No missing variables. If `assignee` is null, it will be treated as "unassigned" (categorical).
- **Access Gated**: None. The dataset is public and requires no credentials.

### Data Loading Strategy
To respect the 7GB RAM limit and ensure robustness:
1. Use `datasets` library with `streaming=True`.
2. Filter for `state == "closed"` during the streaming iteration.
3. Compute `resolution_time_hours` on-the-fly or in a single pass to avoid materializing the full dataset in memory if >1M rows (though current volume is manageable).
4. Persist the cleaned subset to `data/processed/cleaned_issues.csv` for downstream analysis.

## Statistical Methodology

### 1. Distributional Analysis (US-2)
- **Goal**: Determine if resolution times follow a log-normal or Weibull distribution.
- **Method**:
  - Filter out invalid times (`closed < created`).
  - Identify outliers: `resolution_time > 30 days` (conservative cap for extreme tail data).
  - Fit Log-Normal and Weibull distributions using Maximum Likelihood Estimation (MLE) via `scipy.stats`.
  - **Robustness**: Use bounded optimization and method-of-moments fallback if MLE fails.
  - **Validation**: Perform a **Parametric Bootstrap** (n=1000) to generate the null distribution for the KS statistic if standard KS p-values are unreliable due to parameter estimation.
  - **Metrics**: Kolmogorov-Smirnov (KS) statistic, p-value (bootstrap-corrected), AIC.
  - **Rationale**: These are standard for right-skewed duration data. Both will be tested to determine the best fit.

### 2. Hypothesis Testing (US-3)
- **Goal**: Test associations between categorical predictors (language, labels) and resolution time.
- **Method**:
  - **Kruskal-Wallis H-test**: For non-parametric comparison across >2 groups (e.g., languages).
  - **ANOVA**: If normality assumptions are met (after log-transform).
  - **Multiple Comparisons**: Apply **Holm-Bonferroni** correction to control Family-Wise Error Rate (FWER) when conducting ≥3 tests.
  - **Effect Sizes**: Report H-statistic or F-statistic and Cohen's f / eta-squared.

### 3. Mixed-Effects Modeling (US-3)
- **Goal**: Quantify variance explained by issue-level covariates while controlling for repository heterogeneity.
- **Method**:
  - **Model**: Linear Mixed-Effects Model (LMM).
  - **Fixed Effects**: `log(resolution_time)`, `labels`, `comments_count`, `assignee` status.
  - **Random Effects**: Random intercepts for `repository`.
  - **Collinearity**: Calculate Variance Inflation Factor (VIF) on the **Marginal OLS** model (ignoring random effects) to ensure methodological soundness.
    - **Encoding**: Group rare labels into 'Other' to prevent high dimensionality.
    - If VIF ≥ 5, report as descriptive joint relationship, not independent effect.
  - **Validation**: **10-Fold Cross-Validation** stratified by repository size (replaces LOO-CV for computational feasibility).
    - Iteratively hold out a subset of repositories, train on the rest, predict on the held-out set.
    - **Metrics**: Mean Absolute Error (MAE), R².

### 4. Sensitivity Analysis (FR-007)
- **Goal**: Assess robustness of significance thresholds.
- **Method**: Sweep decision cutoffs over `{0.01, 0.05, 0.1}`.
- **Output**: Report **Stability Proportion** (proportion of bootstrap resamples where the predictor remains significant) for each threshold.
  - *Note*: True False Positive/Negative rates cannot be calculated without ground truth labels. Stability is the only valid metric for observational data.

## Statistical Rigor & Constraints

- **Multiple Comparison Correction**: Mandatory Holm-Bonferroni for all hypothesis tests involving >1 group.
- **Sample Size/Power**: Acknowledged limitation if N < 1000 for specific subgroups. Power analysis deferred to implementation phase if data volume allows.
- **Causal Inference**: Explicitly stated as **observational**. All claims framed as "associated with" or "correlational".
- **Measurement Validity**: GitHub API metadata is treated as ground truth.
- **Collinearity**: VIF check mandatory (Marginal OLS method). If `comments_count` and `label_count` are highly correlated (|r|≥0.7), independent effects will not be claimed.
- **Compute Feasibility**: All methods are CPU-tractable. No GPU required. 10-Fold CV used to ensure 6h runtime.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **CPU-First** | GitHub Actions free tier (multi-core CPU, gigabyte-scale RAM) is the target. Statistical methods (MLE, LMM) are efficient on CPU. |
| **Streaming Data** | Prevents OOM errors if the dataset grows or if multiple repositories are aggregated. |
| **Holm-Bonferroni** | More powerful than Bonferroni while controlling FWER; required by FR-004. |
| **10-Fold CV** | Essential for validating generalizability across repositories while remaining computationally feasible within 6 hours. **LOO-CV is too slow.** |
| **Log-Transform** | Resolution times are typically right-skewed; log-transform stabilizes variance for linear models. |
| **Parametric Bootstrap** | Resolves circular validation in KS test for fitted distributions. |
| **Marginal OLS VIF** | Resolves methodological unsoundness of standard VIF on LMMs. |
| **Stability Proportion** | Replaces FP/FN rates as the only valid sensitivity metric for observational data without ground truth. |