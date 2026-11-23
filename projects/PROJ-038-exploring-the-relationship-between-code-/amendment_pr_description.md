# Constitution Amendment Proposal: Statistical Methods Update

**Date**: 2023-10-27
**Author**: llmXive Research Pipeline
**Target Document**: `constitutions/FR-030.md`
**Section**: Principle VI (Statistical Rigor)

## Summary

This proposal seeks to amend **Principle VI** of the llmXive Constitution to replace the prescribed statistical methods for correlation and hypothesis testing. Specifically, we propose replacing **Pearson correlation** and **McNemar's test** with **Point-Biserial correlation** and **Paired Permutation Tests**, respectively.

This change is necessitated by the nature of the target variable in our bug prediction research (binary: `is_buggy`), for which Pearson correlation is statistically inappropriate, and the need for non-parametric robustness in small-sample or non-normally distributed model performance comparisons.

## Proposed Text Change

### Current Text (Principle VI)
> "Correlation analysis shall use Pearson correlation coefficients for continuous variables. Model comparison significance shall be established via McNemar's test for paired nominal data."

### Proposed New Text (Principle VI)
> "Correlation analysis between continuous complexity metrics and the binary bug label shall use the **Point-Biserial correlation coefficient**. Model comparison significance for paired ROC-AUC distributions shall be established via **Paired Permutation Tests** to ensure robustness without assuming normality."

## Scientific Justification

1. **Binary Target Variable**: The primary dependent variable in this study is `is_buggy` (0 or 1). The Pearson correlation coefficient assumes both variables are continuous and normally distributed. Using it with a binary variable yields a mathematically equivalent but conceptually distinct result (the Point-Biserial coefficient) and often violates assumptions of homoscedasticity. The Point-Biserial coefficient is the correct parametric measure for the relationship between a continuous variable and a true dichotomy.

2. **Non-Parametric Robustness**: Bug prediction datasets often exhibit class imbalance and non-normal distributions of metrics. McNemar's test is designed for 2x2 contingency tables (categorical vs categorical). When comparing continuous performance metrics (like ROC-AUC scores) across folds, the assumption of independence or the specific distributional requirements of parametric tests may not hold. A **Paired Permutation Test** provides a distribution-free method to assess the significance of the difference in mean performance between two models (e.g., Full Metric Set vs. Single Best Metric) by shuffling the labels of the differences and recalculating the test statistic.

## Impact Analysis

- **Affected Modules**: `code/src/analysis.py`, `code/src/modeling.py`
- **Data Requirements**: No change in data ingestion; analysis logic must be updated to compute Point-Biserial instead of Pearson.
- **Reproducibility**: This change improves the scientific validity of the results, ensuring that reported correlations and p-values are methodologically sound for the data types involved.

## Implementation Plan

1. Update `constitutions/FR-030.md` with the new text.
2. Update `code/src/analysis.py` to use `scipy.stats.pointbiserialr` and implement a custom permutation test function.
3. Update `code/src/modeling.py` to output data structures compatible with the new test.
4. Re-run the correlation and significance analysis tasks (T021, T031).

---
*This amendment is required to proceed with the statistical analysis phase of the research pipeline.*
