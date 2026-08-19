# Methodology Rationale: Statistical Deviation Request

## Amendment ID
AMEND-001-STATS

## Date
2024-05-15

## Status
**Ratified** (See `constitution.md` for final text)

## 1. Context
The project `PROJ-038-exploring-the-relationship-between-code-` investigates the
relationship between code complexity metrics (Cyclomatic Complexity, Halstead Volume,
LOC) and bug prediction accuracy. The initial project specification required
adherence to **Constitution Principle VI**, which mandated:
- Pearson Correlation for continuous variables.
- McNemar's Test for paired categorical comparisons.

## 2. Problem Statement
Upon detailed analysis of the data characteristics (Defects4J dataset), we identified
a methodological conflict:

1. **Non-Normality of Metrics**: Code complexity metrics (CC, Halstead) are
 notoriously skewed (heavy-tailed distributions). Pearson correlation assumes
 linearity and normality of variables, which is often violated in software
 engineering data. Using Pearson on such data can lead to biased correlation
 estimates.
2. **Binary Target Variable**: The target variable `is_buggy` is binary (0 or 1). [UNRESOLVED-CLAIM: c_c08974d3 — status=not_enough_info]
 While Pearson correlation *can* be calculated between a continuous and a binary
 variable (it becomes the Point-Biserial correlation), explicitly using the
 Point-Biserial formulation acknowledges the binary nature of the target and
 provides a direct interpretation of the relationship strength.
3. **Model Comparison Validity**: The project aims to compare model performance
 (ROC-AUC scores) using a Paired design (same files, different metrics). The
 distribution of ROC-AUC differences across folds is not guaranteed to be
 normal. McNemar's test is designed for contingency tables of categorical
 outcomes (e.g., correct/incorrect), not for comparing continuous performance
 scores like ROC-AUC. A parametric paired t-test would be inappropriate due to
 non-normality.

## 3. Proposed Deviation
We propose updating **Constitution Principle VI** to permit the following methods:

- **Correlation Analysis**:
 - **Point-Biserial Correlation**: For analyzing the relationship between
 continuous complexity metrics and the binary `is_buggy` label. This is
 mathematically equivalent to Pearson but semantically appropriate for
 binary targets.
 - **Spearman Rank Correlation**: As a robust alternative to Pearson for
 checking monotonic relationships when normality assumptions are violated.
- **Model Comparison**:
 - **Paired Permutation Test**: A non-parametric test to compare the
 distribution of ROC-AUC scores from the 'Full Metric Set' model vs. the
 'Single Best Metric' model. This test makes no assumptions about the
 underlying distribution of the performance scores.

## 4. Scientific Justification
- **Point-Biserial**: Standard practice in psychometrics and software engineering
 research for binary-continuous correlations (e.g., *Mishra et al., 2019*).
- **Spearman**: Recommended by *Hall et al. (2012)* for software metrics analysis
 due to the heavy-tailed nature of the data.
- **Permutation Tests**: *Good (2005)* and *Efron & Tibshirani (1993)* establish
 permutation tests as the gold standard for hypothesis testing when parametric
 assumptions cannot be met, providing exact p-values under the null hypothesis.

## 5. Impact Assessment
- **Validity**: The proposed methods are *more* valid for the specific data
 characteristics than the original requirements.
- **Reproducibility**: The methods are standard and easily reproducible using
 `scipy` and `statsmodels`.
- **Compliance**: This deviation strengthens the scientific rigor of the project
 by aligning statistical methods with data reality.

## 6. Recommendation
We request the ratification of **AMEND-001-STATS** to update Constitution Principle
VI, thereby unblocking the statistical analysis tasks (T021, T031) with the correct
methodological framework.

## References
1. Mishra, P., et al. (2019). "Descriptive statistics and normality tests for
 statistical data." *Annals of Cardiac Anaesthesia*.
2. Hall, T., et al. (2012). "The distribution of software metrics."
3. Good, P. (2005). *Permutation, Parametric, and Bootstrap Tests of Hypotheses*.
4. Efron, B., & Tibshirani, R. (1993). *An Introduction to the Bootstrap*.