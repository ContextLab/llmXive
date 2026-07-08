# Methodology Rationale: Statistical Method Selection

## 1. Context and Conflict

This document addresses the apparent conflict between **Constitution Principle VI** (which prescribes Pearson correlation and McNemar's test) and the **Project Specification** (which requires Point-Biserial correlation, Spearman rank correlation, and the Paired Permutation Test) for the analysis of code complexity metrics and bug prediction accuracy.

The Constitution Principle VI was drafted with the assumption of continuous, normally distributed variables and paired categorical outcomes in a general context. However, the specific nature of the data generated in this project (Project PROJ-038) necessitates a deviation to ensure statistical validity and scientific rigor.

## 2. Scientific Justification for Deviation

### 2.1. Deviation from Pearson to Point-Biserial Correlation

**The Conflict:**
Constitution Principle VI suggests Pearson's correlation coefficient ($r$). Pearson's $r$ measures the linear relationship between two *continuous* variables that are normally distributed.

**The Reality of the Data:**
In this study, the target variable `is_buggy` is **binary** (0 for clean, 1 for buggy). While the independent variables (Complexity Metrics: Cyclomatic Complexity, Halstead Volume, LOC) are continuous, the dependent variable is strictly dichotomous.

**The Solution (Point-Biserial):**
The Point-Biserial correlation coefficient ($r_{pb}$) is mathematically equivalent to Pearson's $r$ when one variable is continuous and the other is naturally binary. It is the statistically correct parameter to estimate the strength of association between a complexity metric and the probability of a file containing a bug. Using standard Pearson without acknowledging the binary nature of the target can lead to misinterpretation of the effect size in the context of classification performance.

**Conclusion:**
We adopt Point-Biserial correlation not as a rejection of Pearson, but as the specific, rigorous application of Pearson's logic to a binary-dependent variable scenario, ensuring the correlation coefficient accurately reflects the relationship between metric magnitude and bug presence.

### 2.2. Deviation from Pearson to Spearman Rank Correlation

**The Conflict:**
Constitution Principle VI assumes linearity and normality.

**The Reality of the Data:**
Code complexity metrics (especially Cyclomatic Complexity and Halstead Volume) are known to be **highly skewed** and non-normally distributed in real-world software repositories (long-tail distributions). A few extremely complex files can disproportionately influence Pearson's $r$, violating the assumption of normality and linearity.

**The Solution (Spearman):**
Spearman's rank correlation ($\rho$) is a non-parametric measure that assesses how well the relationship between two variables can be described using a monotonic function. It operates on the *ranks* of the data rather than raw values, making it robust to outliers and non-normal distributions.

**Conclusion:**
We include Spearman correlation to provide a robust measure of association that is not distorted by the heavy-tailed nature of complexity metrics, offering a more reliable indicator of whether "higher complexity generally correlates with higher bug likelihood" without assuming a specific linear scale.

### 2.3. Deviation from McNemar to Paired Permutation Test

**The Conflict:**
Constitution Principle VI suggests McNemar's test. McNemar's test is designed for **paired nominal data** (e.g., a 2x2 contingency table of Yes/No outcomes from two methods on the same subjects) to determine if the row and column marginal frequencies are equal. It tests for *marginal homogeneity* in classification counts.

**The Reality of the Data:**
The research goal is to compare the **performance distributions** (specifically ROC-AUC and F1-scores) of two models (Single Best Metric vs. Full Metric Set) across multiple cross-validation folds. We are comparing continuous performance scores derived from the same data splits (paired folds), not just the final confusion matrix counts. McNemar's test would discard the variance information inherent in the repeated cross-validation process and only compare the final aggregated classification counts, which is less sensitive to differences in model ranking and probability calibration.

**The Solution (Paired Permutation Test):**
A Paired Permutation Test (or Randomization Test) is the gold standard for comparing two dependent samples when the distribution of the difference is unknown or non-normal.
1. We have paired observations (Model A score vs. Model B score for each of the 50 folds). [UNRESOLVED-CLAIM: c_b1505358 — status=not_enough_info]
2. We calculate the observed mean difference in performance.
3. We generate a null distribution by randomly flipping the sign of the difference for each pair (simulating the null hypothesis that the models are equivalent) and recalculating the mean difference.
4. The p-value is the proportion of permuted differences that are as extreme as the observed difference.

**Conclusion:**
The Paired Permutation Test is superior to McNemar's for this specific task because it:
* Utilizes the full distribution of performance scores across folds.
* Makes no parametric assumptions about the distribution of ROC-AUC/F1 scores.
* Directly tests the hypothesis that the *magnitude* of performance improvement is statistically significant, rather than just the marginal counts of a single aggregated confusion matrix.

## 3. Compliance Statement

This deviation is explicitly requested in the project plan under the **'Pending Amendment Request'** clause. The chosen methods (Point-Biserial, Spearman, Paired Permutation) are scientifically justified by the specific statistical properties of the data (binary target, skewed metrics, paired continuous performance scores) and provide a more rigorous analysis than the generic methods suggested in the original Constitution Principle VI.

By adopting these methods, the project ensures that the conclusions drawn regarding the relationship between code complexity and bug prediction are statistically sound and reproducible.

## 4. References

1. *Ruscio, J. (2008). A probability-based measure of effect size: Robustness to base rates and other factors. Psychological Methods.* (Regarding Point-Biserial interpretation).
2. *Spearman, C. (1904). The proof and measurement of association between two things. American Journal of Psychology.*
3. *Edgington, E. S., & Onghena, P. (2007). Randomization tests. CRC Press.* (Regarding Paired Permutation Tests for model comparison).
4. *Demšar, J. (2006). Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research.* (Standard reference for non-parametric comparison of classifiers).