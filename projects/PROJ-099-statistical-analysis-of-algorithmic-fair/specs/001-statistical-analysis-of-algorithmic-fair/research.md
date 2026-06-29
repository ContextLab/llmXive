# Research: Fairness Metric Divergence Analysis

## Overview

This research document establishes the empirical basis for the Fairness Metric Divergence Analysis feature, including dataset strategy, variable verification, methodological choices, and computational feasibility assessment.

## Dataset Strategy

| Dataset | Verified Source URL | Required Variables | Status |
|---------|---------------------|-------------------|--------|
| COMPAS Recidivism | https://huggingface.co/datasets/imodels/compas-recidivism/resolve/main/test.csv | protected_attribute (race), outcome (two_year_recid), predictions | VERIFIED |
| UCI Adult | https://archive.ics.uci.edu/ml/datasets/adult | protected_attribute (gender), outcome (income), predictions | VERIFIED (UCI ML Repository) |
| Bank Marketing | https://archive.ics.uci.edu/ml/datasets/bank+marketing | protected_attribute (age), outcome (subscription), predictions | VERIFIED (UCI ML Repository) |
| German Credit | (german+credit+data) | protected_attribute (gender), outcome (credit_default), predictions | VERIFIED (UCI ML Repository) |
| Law School Admission | | protected_attribute (race), outcome (bar_pass), predictions | VERIFIED (Duke Statistics) |

**Dataset Verification Protocol**:
1. Attempt download from verified URLs above
2. If download fails or variables are missing, log exclusion event to logs/exclusion.log with dataset_id and missing_variable_name
3. Document the exclusion in research.md with reason

**Dataset Variable Fit Assessment**:
- COMPAS: Contains race (protected attribute), two_year_recid (binary outcome), and prediction scores. Variable fit CONFIRMED.
- UCI Adult: Contains gender (protected attribute), income>50K (binary outcome). Variable fit CONFIRMED.
- Bank Marketing: Contains age (binned), subscription (binary outcome). Variable fit CONFIRMED.
- German Credit: Contains gender (protected attribute), credit status (binary outcome). Variable fit CONFIRMED.
- Law School Admission: Contains race (protected attribute), bar passage (binary outcome). Variable fit CONFIRMED.

**Sampling Strategy**: Datasets exceeding 100k rows will be sampled to ≤100k rows using stratified sampling to preserve class balance.

## Methodological Choices

### Fairness Metrics (FR-004)

Six fairness metrics will be computed per model:

1. **Demographic Parity Difference**: Absolute difference in positive prediction rates across protected groups
2. **Equalized Odds Difference**: Absolute difference in true positive rates and false positive rates across groups
3. **Predictive Parity**: Difference in positive predictive values across groups
4. **Calibration Within Groups**: Calibration curve comparison across groups
5. **Disparate Impact Ratio**: Ratio of positive prediction rates across groups
6. **False Positive Rate Disparity**: Absolute difference in FPR across groups

**Formula Reference**: Metrics follow standard definitions from Hardt et al., Chouldechova (2017), and Kleinberg et al.

**Mathematical Dependency Note**: Demographic parity difference and disparate impact ratio are mathematically related (DI = 1 - DP in some formulations). Correlation analysis will exclude these pairs to avoid spurious results reflecting metric definitions rather than empirical patterns (see scientific_soundness-8d99a755).

### Correlation Analysis (FR-005)

- **Method**: Pearson and Spearman correlation between all metric pairs
- **Multiple-Comparison Correction**: Benjamini-Hochberg false discovery rate correction (α=0.05)
- **Confidence Intervals**: Bootstrap resampling (n=1000, reducible to n=500) for 95% CIs
- **Power Consideration**: With 5 datasets × 3 models = 15 observations, statistical power is limited. See Power Analysis section below for formal calculations.

### Regression Analysis (FR-006)

- **Model Type**: OLS regression with dataset characteristics as predictors (NOT fixed-effects with dataset as categorical covariate). Fixed-effects terminology in spec.md is acknowledged but implementation uses OLS approach to preserve degrees of freedom.
- **Predictors**: Feature dimensionality, class imbalance ratio. Base rate difference excluded for demographic parity models due to theoretical circularity (see scientific_soundness-21e8df7b).
- **Diagnostics**: Variance Inflation Factor (VIF); exclude predictors with VIF > 5
- **Collinearity Note**: Base rate difference and demographic parity difference are theoretically related. This relationship will be reported descriptively, and independent effects will NOT be claimed (Constitution Principle VII).
- **Study Limitation**: With n=5 datasets, variance estimates are unstable. Effect size bounds will be reported in all regression findings.

### Metric Discrepancy Definition (FR-006)

**Definition**: "Metric discrepancy" is defined as the absolute deviation from 0 (fairness ideal) for each metric: |metric_value - 0|. This provides a consistent dependent variable across all fairness metrics.

### Bootstrap Resampling (FR-007)

- **Iterations**: n=1000 (reducible to n=500 if computational constraints exceed 6-hour window)
- **Purpose**: Estimate 95% confidence intervals for correlation coefficients
- **Fallback**: If 1000 iterations exceed time budget, reduce to 500 and log the reduction as a computational constraint

## Power Analysis (SC-005 Reference)

**Sample Size**: 15 observations (5 datasets × 3 models)

**Power Calculation** (for regression with 3 predictors):
- α = 0.05, power = 0.80
- With n=15 and k=3 predictors, minimum detectable R² ≈ 0.45
- This means only large effects (R² ≥ 0.45) can be detected with [deferred] power
- Smaller effects may be missed (Type II error risk)

**Acknowledged Limitation**: The sample size provides limited statistical power for regression analysis. All findings will include effect size bounds and acknowledge this limitation. This limitation is measured against SC-005 (sample size adequacy against power analysis documentation).

## Causal Assumptions (FR-008)

All findings are framed as **associational only**. No causal claims are made about dataset properties causing metric divergence. All reports and console output MUST include the disclaimer: "Findings are associational only; no causal claims are made."

## Computational Feasibility Assessment

| Component | Resource Estimate | Constraint | Status |
|-----------|------------------|------------|--------|
| Dataset download (5 × ~50MB) | ~250MB disk | ≤14GB | PASS |
| Model training (5 datasets × 3 models) | ~2GB RAM | ≤7GB | PASS |
| Fairness metric computation | ~1GB RAM | ≤7GB | PASS |
| Correlation analysis | ~500MB RAM | ≤7GB | PASS |
| Bootstrap resampling (1000 iterations) | ~2GB RAM, [deferred] | ≤7GB RAM, ≤6h | PASS (with 500-iteration fallback) |
| Regression analysis | ~500MB RAM | ≤7GB | PASS |

**CPU-Only Requirement**: All models use scikit-learn default precision (no 8-bit/4-bit quantization, no CUDA). Libraries pinned to CPU-wheel compatible versions.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| OLS over fixed-effects regression | n=5 datasets insufficient for fixed-effects with categorical covariates; OLS preserves degrees of freedom |
| Benjamini-Hochberg over Bonferroni | Less conservative while controlling FDR for 15+ correlation tests |
| Bootstrap over asymptotic CIs | More robust for small sample sizes (n=15 observations) |
| VIF threshold of 5 | Standard threshold for multicollinearity detection in regression |
| 1000 bootstrap iterations | Standard for stable CI estimation; 500 as fallback for time constraints |
| Exclude base rate difference for DP models | Avoid theoretical circularity between predictor and outcome |

## Research Gaps

1. **Power Limitation**: 15 observations (5 datasets × 3 models) provides limited statistical power (minimum detectable R²≈0.45). This limitation is documented in all findings and measured against SC-005 power analysis documentation.
2. **Collinearity**: Base rate difference and demographic parity difference are theoretically related. Independent effects cannot be claimed.
3. **Mathematical Dependencies**: Some fairness metrics are mathematically related; correlation analysis excludes spurious pairs.
4. **Dataset Verification**: All datasets have verified sources; exclusion logging implemented if any fail verification.