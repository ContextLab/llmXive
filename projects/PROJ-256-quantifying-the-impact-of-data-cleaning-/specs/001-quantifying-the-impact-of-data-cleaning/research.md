# Research: Quantifying the Impact of Data Cleaning on Statistical Inference

## Research Question

How do different data cleaning strategies (outlier removal, missing value imputation, data type correction) quantitatively affect p-values, confidence intervals, and effect sizes in common statistical tests?

## Dataset Strategy

**Constraint**: Per project rules, only datasets from the `# Verified datasets` block may be cited or used.

| Dataset Name | Verified URL | Suitability | Notes |
|:--- |:--- |:--- |:--- |
| **UCI HAR** | ` | **High** | Numeric sensor data; suitable for t-tests/regression. |
| **UCI Shopper** | ` | **High** | Numeric purchase data; suitable for regression. |
| **UCI DROP** | ` | **Low** | Text-based (Reading Comprehension); unsuitable for numeric cleaning study. |
| **Other Verified** | (F1-score, URL, IQR, MUST) | **Low** | Primarily text/audio benchmarks; lack numeric outcomes for statistical inference. |

**Decision**: We will use **UCI HAR** and **UCI Shopper** as the primary sources. The spec requirement for "OpenML Small Datasets" has **NO verified source** in the allowed block. We adapt FR-001 to use the verified UCI links to ensure feasibility, noting this deviation in the plan.

**Dataset-Variable Fit Check**:
- **Required**: Numeric outcome variable, numeric predictors, missing values, outliers.
- **UCI HAR**: Contains numeric sensor features. Outcome is activity class (can be treated as group for t-tests).
- **UCI Shopper**: Contains numeric features (e.g., amount spent). Outcome can be derived or existing numeric column used.
- **Gap**: Spec text contains conflicting research questions (e.g., "Can transfer learning...", "Can LLMs generate reports...", "Glioblastoma biomarkers..."). These are identified as **spec corruption** and are **excluded** from this plan. The plan follows the Title and FR-002/FR-011 (Statistical Cleaning).

**Feasibility Gap**: SC-006 requires ≥10 datasets but only a limited number of verified datasets are available. This creates a blocking gap. Median/IQR aggregation across 2 datasets is not statistically meaningful. The study will proceed with per-dataset analysis and descriptive summaries, noting this limitation.

## Statistical Rigor

1. **Multiple-Comparison Correction**: Per FR-007/SC-004, Benjamini-Hochberg (BH) will be applied when >1 hypothesis test is run across datasets to control **False Discovery Rate (FDR)** at q≤0.05. **Note**: BH controls FDR, not family-wise error rate (FWER). FWER control would require Bonferroni or Holm methods.
2. **Sample Size/Power**: Power analysis is documented below. For small-sample datasets (n<50), minimum detectable effect size (MDES) is calculated. Bootstrap may be unstable for n<50; jackknife variance estimation or analytical standard errors are used as alternatives.
 - **MDES Calculation**: For two-sample t-test with α=0.05, power=0.80, n=50 per group: MDES ≈ 0.57 (Cohen's d). For n=20 per group: MDES ≈ 0.90.
 - **Small-N Alternative**: For n<50, use jackknife resampling (n iterations) or analytical standard error formulas instead of bootstrap.
 - **Bootstrap Iterations**: 1000 for n≥50; reduced to 500 for n<50 to ensure CPU tractability.
3. **Causal Inference**: Claims are framed as **associational**. This is an observational study of cleaning effects, not a randomized trial of cleaning strategies.
4. **Measurement Validity**: Uses standard statistical instruments (t-tests, OLS) with established validation. No new questionnaires used.
5. **Collinearity**: VIF diagnostics will be run on regression models. If predictors are definitionally related, independent effects are NOT claimed.
6. **Permutation Null**: Per FR-011, outcome variables will be shuffled for **1000 permutations per dataset** to estimate false-positive rates for outlier thresholds. This ensures stable FPR estimates with acceptable variance.

## Computational Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, 7 GB RAM).
- **Methods**:
 - **Bootstrap**: 1000 iterations per dataset (FR-009) for n≥50; jackknife for n<50. CPU-tractable for N<200. If N is larger, sample to N=200 for bootstrap to ensure ≤6h runtime.
 - **Imputation**: `sklearn.impute.KNN` (k=5) is CPU-tractable for small N.
 - **Outliers**: IQR calculation is O(N).
 - **Permutation**: 1000 permutations per dataset for FPR estimation (FR-011).
- **Data Volume**: Datasets sampled to fit ≤7 GB RAM. If raw download exceeds limits, chunking or row sampling is applied.

## Risk Mitigation

| Risk | Mitigation |
|:--- |:--- |
| **Spec Text Corruption** | Ignore inserted text about LLM/Transfer Learning/Glioblastoma; focus on Title/FRs. Document gap in `research.md`. Flagged for kickback. |
| **Dataset Incompatibility** | Use only verified UCI HAR/Shopper. If they lack numeric outcomes, skip dataset and log exclusion (Edge Case: Missing outcome >80%). |
| **Runtime Exceeds 6h** | Reduce bootstrap iterations to 500; sample datasets to N≤200 for intensive steps. |
| **Memory Overflow** | Process datasets sequentially; clear memory between runs; avoid loading all datasets at once. |
| **Statistical Aggregation** | Only 2 datasets available; median/IQR across datasets not statistically meaningful. Use per-dataset analysis with descriptive summaries. Flagged for kickback. |
| **Power Limitations** | Small-N datasets (n<50) have limited power. Use jackknife/analytical SE alternatives. Document MDES for each dataset. |
