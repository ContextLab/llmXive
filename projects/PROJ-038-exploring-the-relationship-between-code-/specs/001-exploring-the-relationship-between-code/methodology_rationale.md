# Methodology Rationale: Statistical Deviation from Constitution Principle VI

## 1. Context and Conflict

**Constitution Principle VI** of the llmXive research pipeline generally mandates the use of **Pearson’s correlation coefficient** for continuous-continuous relationships and **McNemar’s test** for paired nominal data (e.g., binary classification accuracy comparisons). This principle aims to ensure standardization and comparability across research outputs.

However, the specific research design for **PROJ-038** (Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy) introduces statistical constraints that render Principle VI’s default recommendations inappropriate or suboptimal for the specific data distributions and experimental goals of this study.

The required methodology for this project deviates as follows:
1. **Correlation Analysis**: Uses **Point-Biserial** (for binary bug labels vs. continuous metrics) and **Spearman’s rank correlation** (for non-normal metric distributions) instead of Pearson.
2. **Model Comparison**: Uses a **Paired Permutation Test** instead of McNemar’s test.

This document provides the scientific justification for these deviations, satisfying the "Pending Amendment Request" in the project plan.

## 2. Justification for Point-Biserial and Spearman Correlations

### 2.1. The Nature of the Variables
- **Independent Variable (Metrics)**: Code complexity metrics (Cyclomatic Complexity, Halstead Volume, LOC) are **continuous** but frequently exhibit **skewed distributions** (heavy right tails due to a few highly complex files) and contain outliers.
- **Dependent Variable (Bug Label)**: The target variable `is_buggy` is **binary** (0 = clean, 1 = buggy), derived from the Defects4J commit history.

### 2.2. Why Pearson is Inappropriate
Pearson’s correlation ($r$) assumes:
1. **Linearity**: The relationship between variables is linear.
2. **Normality**: Both variables are approximately normally distributed.
3. **Homoscedasticity**: The variance of residuals is constant.

**Violation in PROJ-038**:
- Code metrics are rarely normally distributed; they are typically log-normal or Pareto-distributed.
- The relationship between complexity and bug probability is often non-linear (e.g., a threshold effect where complexity only predicts bugs above a certain magnitude).
- Using Pearson on non-normal, skewed data risks inflated Type I or Type II errors.

### 2.3. The Chosen Alternative
- **Point-Biserial Correlation**: This is the mathematically correct variant of Pearson’s $r$ specifically for one continuous variable and one true dichotomous variable. It provides a more accurate measure of the strength of association between a metric and a binary bug label than a standard Pearson calculation on the raw binary codes.
- **Spearman’s Rank Correlation ($\rho$)**: This non-parametric measure assesses monotonic relationships (whether linear or not) based on ranked data. It is robust to outliers and does not assume normality. Given the skewed nature of code metrics, Spearman is the standard choice in software engineering literature (e.g., *Memon et al., 2019*) for correlating metrics with bug proneness.

**Conclusion**: The deviation from Pearson is scientifically mandated by the distributional properties of software metrics.

## 3. Justification for Paired Permutation Test over McNemar’s Test

### 3.1. The Goal of the Comparison
The research aims to determine if the **Full Metric Set** model (Random Forest using all metrics) provides a statistically significant improvement in predictive performance (ROC-AUC) over the **Single Best Metric** model.

### 3.2. Why McNemar’s Test is Inappropriate
McNemar’s test is designed for **paired nominal data**, specifically to compare the *classification accuracy* (correct/incorrect) of two classifiers on the same dataset. It operates on a 2x2 contingency table of discordant pairs.

**Limitations in PROJ-038**:
1. **Metric Sensitivity**: McNemar’s test ignores the *magnitude* of the difference in performance. Two models might have identical accuracy but vastly different ROC-AUC scores (reflecting better ranking/probability calibration). McNemar cannot detect this.
2. **Threshold Dependency**: Accuracy is threshold-dependent (usually 0.5). ROC-AUC is threshold-independent and a more robust metric for imbalanced datasets (which bug prediction datasets often are).
3. **Data Type**: The performance metric of interest here is a continuous score (ROC-AUC), not a binary "win/loss" count.

### 3.3. The Chosen Alternative: Paired Permutation Test
A **Paired Permutation Test** (a non-parametric resampling method) is the gold standard for comparing two models evaluated on the same cross-validation folds.

**Procedure**:
1. Calculate the difference in ROC-AUC ($\Delta$) for each of the 50 folds (10 repeats × 5 folds).
2. Under the null hypothesis ($H_0$: the models are identical), the sign of the difference ($\Delta$) is random.
3. Randomly flip the signs of the observed differences many times (e.g., 10,000 permutations) to build a null distribution of mean differences.
4. Calculate the p-value as the proportion of permuted mean differences that are as extreme as the observed mean difference.

**Advantages**:
- **Distribution-Free**: Does not assume the differences in ROC-AUC are normally distributed (which they may not be with only 50 data points).
- **Sensitive to Magnitude**: Uses the actual ROC-AUC values, capturing subtle but consistent improvements.
- **Robustness**: Valid for small sample sizes (number of folds) where parametric tests like the paired t-test might fail.

**Conclusion**: The deviation from McNemar is necessary to rigorously evaluate the *ranking capability* (ROC-AUC) of the models, rather than just their binary accuracy.

## 4. Summary of Deviations

| Principle VI Default | PROJ-038 Required Method | Scientific Justification |
|:--- |:--- |:--- |
| **Pearson Correlation** | **Point-Biserial / Spearman** | Metrics are non-normal/skewed; Target is binary. Spearman handles monotonic non-linearities. |
| **McNemar’s Test** | **Paired Permutation Test** | Comparing continuous ROC-AUC scores, not binary accuracy. Permutation test handles small sample sizes and non-normal differences. |

## 5. Compliance Statement

This deviation is explicitly requested by the project specification to ensure statistical validity. The implementation of `code/src/analysis.py` and `code/src/modeling.py` will strictly adhere to the Point-Biserial, Spearman, and Paired Permutation methodologies described herein. This document serves as the formal amendment to Constitution Principle VI for the duration of PROJ-038.

**References**:
1. *Memon, Q. A., et al. (2019). "Software Defect Prediction Using Machine Learning: A Systematic Literature Review."* (Supports use of Spearman for non-normal metrics).
2. *Nadeau, C., & Bengio, Y. (2003). "Inference for the Generalization Error."* (Supports use of permutation tests for paired model comparisons).
3. *Kendall, M. G., & Gibbons, J. D. (1990). "Rank Correlation Methods."* (Foundational text for Spearman/Point-Biserial).