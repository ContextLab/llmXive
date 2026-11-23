# Methodology Rationale: Statistical Test Selection

## Executive Summary

This document provides the scientific justification for deviating from **Constitution Principle VI** (which mandates Pearson correlation and McNemar's test) in favor of **Point-Biserial correlation**, **Spearman rank correlation**, and the **Paired Permutation Test** for the analysis of code complexity metrics versus bug prediction accuracy.

This deviation is necessary due to the specific nature of the data distributions encountered in static code analysis and bug prediction research. The selected methods are statistically more robust and appropriate for the research questions defined in the project specification.

## 1. The Conflict

### Constitution Principle VI
The project's governing constitution (Principle VI) stipulates:
> "Statistical significance must be assessed using Pearson correlation for continuous variables and McNemar's test for paired categorical outcomes."

### Project Specification Requirements
The research specification (US2, US3) requires:
1. **Point-Biserial Correlation**: To assess the relationship between binary bug labels (`is_buggy` = 0/1) and continuous complexity metrics (CC, Halstead, LOC).
2. **Spearman Rank Correlation**: To assess monotonic relationships where linearity cannot be assumed (common in complexity metrics which often exhibit heavy-tailed distributions).
3. **Paired Permutation Test**: To compare the performance distributions of two models (Full Metric Set vs. Single Best Metric) without assuming normality of the difference scores.

## 2. Scientific Justification for Deviation

### 2.1 Point-Biserial vs. Pearson Correlation
**The Issue:** Pearson correlation ($r$) measures linear relationships between two *continuous* variables. It assumes bivariate normality.

**The Data Reality:** In this study, the target variable `is_buggy` is **binary** (0 or 1), not continuous. While Pearson correlation can technically be calculated between a binary and a continuous variable, the resulting statistic is mathematically equivalent to the **Point-Biserial correlation** ($r_{pb}$).

**Justification:**
* **Theoretical Correctness:** Point-Biserial is the specific case of Pearson correlation for a dichotomous variable. Explicitly naming and using $r_{pb}$ acknowledges the data structure and ensures the interpretation aligns with binary classification contexts (e.g., "point-biserial correlation between bug status and cyclomatic complexity").
* **Assumption Handling:** Point-Biserial relaxes the normality assumption for the binary variable (which is impossible to satisfy) and focuses on the normality of the continuous variable *within* each group (buggy vs. non-buggy). This is a more accurate description of the statistical test being performed.
* **Conclusion:** Using Point-Biserial is not a deviation in *math* (it is Pearson applied to binary data) but a deviation in *nomenclature and precision* required for scientific rigor.

### 2.2 Spearman Rank vs. Pearson Correlation
**The Issue:** Pearson correlation measures *linear* relationships. It is highly sensitive to outliers and non-normal distributions.

**The Data Reality:** Code complexity metrics (Cyclomatic Complexity, Halstead Volume, LOC) are notorious for:
* **Skewness:** Most files have low complexity; a few have extremely high complexity (long-tail distribution).
* **Non-Linearity:** The relationship between complexity and bug likelihood is often monotonic but not strictly linear (e.g., risk increases exponentially after a threshold).
* **Outliers:** Extreme values in metrics can disproportionately influence Pearson $r$, leading to spurious results.

**Justification:**
* **Robustness:** Spearman correlation ($\rho$) assesses *monotonic* relationships by ranking data. It is invariant to monotonic transformations and robust to outliers.
* **Scientific Consensus:** In software engineering research (e.g., studies by Briand et al., Nagappan et al.), Spearman is the standard for analyzing complexity metrics due to their non-normal distributions.
* **Conclusion:** Requiring Pearson would risk invalid results due to violation of linearity and normality assumptions. Spearman is the scientifically superior choice for this specific domain.

### 2.3 Paired Permutation Test vs. McNemar's Test
**The Issue:** McNemar's test is designed for **paired nominal data** (e.g., 2x2 contingency tables of Correct/Incorrect classifications). It tests if the marginal probabilities are equal.

**The Data Reality:** We are comparing **continuous performance metrics** (ROC-AUC, F1-Score) derived from Repeated 5-Fold Cross-Validation.
* We have a distribution of 50 ROC-AUC scores for Model A and 50 for Model B.
* We want to know if the *mean difference* in performance is statistically significant.
* The differences in ROC-AUC scores are continuous, not binary.

**Justification:**
* **Inapplicability of McNemar:** McNemar's test cannot be applied to continuous score distributions. It would require discretizing the continuous ROC-AUC scores into binary "win/loss" outcomes, which discards valuable information and reduces statistical power.
* **Advantages of Permutation Test:**
 * **Non-Parametric:** Makes no assumption about the distribution of the difference scores (normality).
 * **Exactness:** With sufficient permutations, it provides an exact p-value for the null hypothesis that the two models come from the same distribution.
 * **Paired Design:** It naturally handles the paired nature of the data (same folds, same data splits) by permuting the labels *within* each pair.
* **Conclusion:** McNemar's test is the wrong tool for comparing continuous model performance metrics. The Paired Permutation Test is the standard, rigorous method for this specific comparison in machine learning evaluation.

## 3. Compliance with the "Pending Amendment Request"

The project plan explicitly identifies this conflict as a "Pending Amendment Request." The scientific community in software engineering and machine learning evaluation has moved beyond strict adherence to parametric tests (Pearson/McNemar) when data assumptions are violated.

By adopting Point-Biserial, Spearman, and Permutation Tests, we are:
1. **Increasing Validity:** Ensuring statistical tests match the data distribution.
2. **Increasing Power:** Avoiding the loss of information inherent in forcing binary tests on continuous data.
3. **Aligning with Best Practices:** Following the standards set by top-tier software engineering venues (ICSE, FSE, ASE).

## 4. Conclusion

The deviation from Constitution Principle VI is scientifically mandated by the nature of the data (binary targets, skewed metrics, continuous performance scores). The selected methods (Point-Biserial, Spearman, Paired Permutation) are the correct statistical tools for the research questions at hand.

**Recommendation:** The constitution should be amended to allow for non-parametric and rank-based methods when data distribution assumptions (normality, linearity) are violated, specifically in the context of software metric analysis and model performance comparison.

---
*Generated for: PROJ-038-exploring-the-relationship-between-code-*
*Task: T000a - Methodology Rationale*