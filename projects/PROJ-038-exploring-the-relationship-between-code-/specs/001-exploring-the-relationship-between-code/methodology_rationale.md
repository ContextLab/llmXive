# Methodology Rationale: Statistical Test Selection

## Document Status
**Status**: DRAFT
**Date**: 2023-10-27
**Action Required**: External Governance Ratification
**Note**: Execution of statistical analysis tasks is BLOCKED until this amendment is ratified and the artifact `amendment_ratified.md` is created.

## 1. Context and Conflict Identification

### 1.1 Constitution Principle VI
The project's governing Constitution (Principle VI) mandates the use of **Pearson Correlation** for continuous-variable relationships and **McNemar's Test** for paired binary classification differences. These methods are traditionally standard for:
- **Pearson**: Assessing linear relationships between normally distributed continuous variables.
- **McNemar**: Comparing paired proportions (e.g., accuracy of two classifiers on the same binary labels).

### 1.2 Spec-Required Methods
The Research Specification (`spec.md`) explicitly requires the following methods for this study:
- **Point-Biserial Correlation**: To assess the relationship between continuous complexity metrics (e.g., Cyclomatic Complexity, Halstead Volume) and a binary bug label (`is_buggy`).
- **Spearman Rank Correlation**: To assess monotonic relationships, robust to non-normal distributions and outliers common in code complexity data.
- **Paired Permutation Test**: To validate the difference in performance (ROC-AUC) between the "Full Metric Set" model and the "Single Best Metric" model without relying on parametric assumptions.

### 1.3 The Conflict
There is a direct methodological conflict:
- **Constitution VI** prescribes Pearson/McNemar.
- **Specification** prescribes Point-Biserial/Spearman/Paired Permutation.

If strictly adhering to Constitution VI, the analysis would be statistically invalid for the data characteristics described in the Spec (non-normal complexity distributions, binary targets, and non-parametric model comparison needs).

## 2. Scientific Justification for Deviation

The deviation from Constitution VI to the Spec's required methods is scientifically justified by the following empirical and theoretical factors:

### 2.1 Nature of the Target Variable (Point-Biserial vs. Pearson)
The target variable `is_buggy` is **binary** (0 or 1).
- **Point-Biserial Correlation** is mathematically equivalent to the Pearson correlation coefficient when one variable is continuous and the other is naturally dichotomous.
- Using Point-Biserial is not a "new" method but the **correct application** of Pearson for binary targets. However, explicitly naming it "Point-Biserial" in the methodology clarifies the statistical intent and ensures the correct interpretation of the effect size (correlation between a metric and bug presence).
- **Decision**: We adopt Point-Biserial to explicitly acknowledge the binary nature of the bug label, which aligns with the spirit of Pearson while ensuring methodological precision.

### 2.2 Distribution of Code Complexity Metrics (Spearman vs. Pearson)
Code complexity metrics (Cyclomatic Complexity, Halstead Volume, LOC) are **highly skewed** and **non-normally distributed** (heavy-tailed).
- **Pearson Correlation** assumes linearity and normality. It is sensitive to outliers, which are prevalent in software projects (e.g., a few massive "god classes").
- **Spearman Rank Correlation** assesses monotonic relationships based on ranks. It is robust to outliers and does not assume normality.
- **Decision**: Spearman is the statistically superior choice for this dataset. Using Pearson would risk spurious correlations driven by a small number of extreme outliers, violating the "Real Data Integrity" principle.

### 2.3 Model Comparison (Paired Permutation vs. McNemar)
The study compares the performance (ROC-AUC) of two models on the **same** test folds.
- **McNemar's Test** is designed for comparing **binary classification accuracy** (counts of correct/incorrect predictions) in a 2x2 contingency table. It is not appropriate for comparing continuous performance metrics like ROC-AUC or F1-scores.
- **Paired Permutation Test** is the non-parametric gold standard for comparing two dependent distributions (e.g., ROC-AUC scores from the same folds). It makes no assumptions about the distribution of the differences.
- **Decision**: McNemar is mathematically inapplicable to the metric (ROC-AUC) being compared. The Paired Permutation Test is the only valid approach to test the null hypothesis that the two models have equal performance distributions.

## 3. Conclusion and Recommendation

The methods prescribed in the Specification (Point-Biserial, Spearman, Paired Permutation) are not a rejection of statistical rigor but an **adaptation** of it to the specific characteristics of software engineering data (binary targets, skewed distributions, continuous performance metrics).

Strict adherence to the generic "Pearson/McNemar" rule of Constitution VI would result in **statistically invalid conclusions**. Therefore, the Constitution is amended *de facto* for this project to allow the use of the Spec's methods.

## 4. Required Action

**Governance Body Action**:
1. Review this rationale.
2. If approved, create the file `specs/001-code-complexity-bug-prediction/amendment_ratified.md` containing a signature or timestamp of ratification.
3. Upon creation of `amendment_ratified.md`, the pipeline (Task T000b) will proceed to execution.

**Failure Condition**:
If `amendment_ratified.md` is not present, the pipeline will halt with a `ConstitutionalBlockError` to prevent invalid statistical analysis.

---
*This document serves as the formal justification for the statistical methodology employed in PROJ-038.*