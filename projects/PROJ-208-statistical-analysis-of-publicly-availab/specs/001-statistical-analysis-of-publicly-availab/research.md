# Research: Statistical Analysis of GitHub Issue Resolution Times

## 1. Problem Statement
The objective is to statistically analyze publicly available GitHub issue resolution times to understand the distribution of these times and identify factors (labels, language, assignee count) that are associatively linked to resolution duration. The study must be reproducible, computationally feasible on a free-tier CI runner, and strictly observational (no causal claims).

## 2. Dataset Strategy

### 2.1 Primary Data Source
The plan utilizes the **verified** HuggingFace dataset `akhousker/github-issues`.
- **Source**: `akhousker/github-issues`
- **Access Method**: `datasets.load_dataset("akhousker/github-issues", split="train")`
- **Verified Record Count**: [deferred] records (sufficient for statistical power in distribution fitting and mixed-effects modeling).
- **Verified Fields**: `issue_id`, `repository`, `created_at`, `closed_at`, `resolution_time_hours`, `labels`, `assignee`, `state`, `comments_count`.
- **Schema Fit**: The dataset contains `created_at` and `closed_at` (required for FR-002). It contains `labels` and `assignee`. The `language` field is **not** explicitly present in the raw schema. **Mitigation**: The plan will implement a **Repository Metadata Enrichment** step using the **GitHub REST API** to fetch the `language` field for each unique repository in the dataset. This ensures the LME model is not under-specified.

### 2.2 Data Availability & Feasibility
- **Download Mechanism**: Programmatic via `huggingface_hub`/`datasets`. No API keys required for public datasets.
- **Size**: ~1-5 MB (text/parquet). Well within 14 GB disk and 7 GB RAM limits.
- **Streaming**: Not required; dataset fits in memory.
- **Access Gated**: No. Publicly available.
- **Fallback**: If HF dataset is unavailable or schema fails, `loader_api.py` will collect data from GitHub REST API (Phase 0.5).

### 2.3 Data Hygiene Plan
- **Checksum**: MD5 hash of the downloaded parquet file stored in `state/`.
- **Raw Preservation**: Downloaded file saved as `data/raw/github_issues_raw.parquet` (read-only).
- **Derived Data**: `data/processed/cleaned_issues.csv` (CSV) containing computed `resolution_time_hours` and `is_outlier` (MAD-based).

## 3. Statistical Methodology

### 3.1 Distribution Analysis (US-2)
- **Goal**: Determine if resolution times follow a Log-normal or Weibull distribution.
- **Method**:
  1. Log-transform `resolution_time_hours` (base e).
  2. Fit Log-normal and Weibull distributions using `scipy.stats`.
  3. Evaluate fit using Kolmogorov-Smirnov (KS) statistic and p-value.
  4. **Outlier Detection**: Use **Median Absolute Deviation (MAD)** on the **log-transformed scale** (MAD * 3.0) to flag extreme outliers. This is more robust for right-skewed time-to-event data than IQR on the original scale.
- **Handling Convergence**: If MLE fails for a distribution, report "Convergence Failed" and use the best-fit truncated distribution or fallback to non-parametric description.

### 3.2 Hypothesis Testing (US-3)
- **Goal**: Test if categorical predictors (e.g., Label presence, Language) affect resolution time.
- **Method**:
  1. **Label Aggregation**: Group labels with <5% frequency into 'Other' to ensure sufficient sample size per group for Kruskal-Wallis. If cardinality remains high, fallback to binary 'Label Presence' analysis.
  2. **Kruskal-Wallis H-test**: Non-parametric test for >2 groups.
  3. **Multiple Comparison Correction**: 
     - For **independent** tests (e.g., Language groups): Apply **Holm-Bonferroni** correction (FR-004).
     - For **dependent** tests (e.g., non-mutually exclusive labels): Apply **Westfall-Young Permutation** test to correctly control Family-Wise Error Rate (FWER) under dependency.
  4. **Effect Size**: Calculate epsilon-squared ($\epsilon^2$) or rank-biserial correlation.
  5. **Confidence Intervals**: Bootstrap 95% CIs for effect sizes.
- **Constraint**: If <20 repositories exist in a group, note low power.

### 3.3 Mixed-Effects Modeling (US-3)
- **Goal**: Quantify variance explained by covariates while controlling for repository-level clustering.
- **Model**: $Y_{ij} = \beta_0 + \beta_1 X_{ij} + u_j + \epsilon_{ij}$
  - $Y$: Log-resolution time.
  - $X$: Issue-level covariates (comments, label count, language, etc.).
  - $u_j$: Random intercept for repository $j$.
- **Software**: `statsmodels` `MixedLM`.
- **Collinearity (FR-006)**:
  - Calculate VIF for all fixed effects from the **LME fixed effects design matrix** (not Marginal OLS) to correctly account for random effects structure.
  - If VIF exceeds a predefined threshold, flag the predictor.
  - **Action**: Do not claim independent effects. Report joint relationship and descriptive stats.
  - **Dimensionality Reduction**: Group rare labels (<5%) before encoding to prevent singular matrices.
- **Cross-Validation**: **5-fold Stratified by Repository Size** (small, medium, large based on issue count). Report MAE and R².

### 3.4 Sensitivity Analysis (FR-007)
- **Goal**: Assess stability of results across significance thresholds.
- **Method**: **Parametric Bootstrap** (1000 iterations) tailored to the LME structure (simulating new residuals based on fitted variance components) and **Stratified Bootstrap** (stratifying by repository) to preserve hierarchical structure.
- **Thresholds**: Sweep $\alpha$ across a range of small positive values.
- **Metric**: **Bootstrap Stability Index** (proportion of resamples where the effect size remains within 10% of the original estimate). This is more robust than 'stability proportion' of significance.

## 4. Compute Feasibility Decision

| Method | CPU Feasible? | GPU Required? | Decision |
| :--- | :--- | :--- | :--- |
| Data Loading | Yes | No | CPU (Native) |
| Distribution Fitting | Yes | No | CPU (Scipy) |
| Kruskal-Wallis | Yes | No | CPU (Scipy) |
| Mixed-Effects (LME) | Yes | No | CPU (Statsmodels) |
| Bootstrap (1000 iters) | Yes | No | CPU (Parallelized) |
| **Total** | **Yes** | **No** | **CPU-First Strategy** |

**Rationale**: The dataset is small. All statistical methods are classical and computationally light. No deep learning or large matrix inversions requiring GPU acceleration are needed. The plan strictly adheres to CPU-tractable methods (FR-010).

## 5. Risks & Mitigations

- **Risk**: Missing `language` field in dataset.
  - **Mitigation**: Implement **Repository Metadata Enrichment** via GitHub REST API to fetch `language` for each unique repository in the dataset.
- **Risk**: Extreme outliers skewing LME.
  - **Mitigation**: Log-transform the outcome variable and use **MAD on log-scale** for outlier detection.
- **Risk**: Low sample size for specific label groups.
  - **Mitigation**: Group rare labels into "Other" category (<5% frequency) before testing.
- **Risk**: Label dependency violating Holm-Bonferroni assumptions.
  - **Mitigation**: Use **Westfall-Young Permutation** test for dependent label groups.
- **Risk**: VIF on OLS not valid for LME.
  - **Mitigation**: Calculate VIF on the **LME fixed effects design matrix**.