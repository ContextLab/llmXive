# Methodology Rationale: Statistical Deviation Amendment (AMEND-001-STATS)

**Date**: 2023-10-27
**Author**: Automated Research Agent
**Status**: Draft Amendment Request
**Related Task**: T000a

## 1. Executive Summary

This document formally requests an amendment to **Constitution Principle VI** of the llmXive research pipeline. The current principle mandates the use of **Pearson correlation** for continuous variables and **McNemar’s test** for paired categorical comparisons. However, the specific requirements of the research project *PROJ-038* (Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy) necessitate the use of **Point-Biserial correlation**, **Spearman’s rank correlation**, and the **Paired Permutation Test**.

This deviation is scientifically justified by the nature of the data distributions and the specific hypothesis testing framework required for bug prediction analysis. The following sections detail the conflict and the justification for the proposed methods.

## 2. Conflict Analysis

### 2.1 Current Constitution Principle VI
> "Statistical analysis must rely on Pearson correlation for linear relationships between continuous variables and McNemar’s test for paired nominal data to ensure standard parametric rigor."

### 2.2 Project Requirements (PROJ-038)
The project specification requires:
1. **Correlation Analysis**: Assessment of the relationship between continuous complexity metrics (Cyclomatic Complexity, Halstead Volume, LOC) and a binary bug label (`is_buggy` ∈ {0, 1}). Additionally, non-parametric rank correlation is required to handle potential non-linear monotonic relationships and outliers common in code complexity data.
2. **Significance Testing**: Validation of model performance differences (ROC-AUC scores) between a "Full Metric Set" and a "Single Best Metric" model using a non-parametric approach robust to the specific distribution of cross-validation folds.

## 3. Scientific Justification for Deviation

### 3.1 Point-Biserial Correlation vs. Pearson Correlation
* **The Conflict**: Pearson correlation assumes both variables are continuous and normally distributed. In our dataset, the target variable `is_buggy` is strictly **binary** (0 or 1).
* **The Justification**: The **Point-Biserial correlation** is a special case of the Pearson correlation specifically designed for one continuous variable and one dichotomous variable. While mathematically equivalent to Pearson in this specific case, explicitly naming and using Point-Biserial ensures statistical correctness in reporting and aligns with best practices for binary classification feature analysis. Using the generic "Pearson" label without qualification may lead to misinterpretation of the data types involved.
* **Decision**: We will use Point-Biserial correlation as the primary metric for binary-target relationships, acknowledging it as the correct parametric test for this data structure.

### 3.2 Spearman’s Rank Correlation vs. Pearson Correlation
* **The Conflict**: Code complexity metrics (e.g., Cyclomatic Complexity, Halstead Volume) are notorious for **heavy-tailed distributions** and significant **outliers** (e.g., "God Classes" with thousands of lines of code). Pearson correlation is highly sensitive to these outliers, potentially masking true relationships or producing misleadingly high/low values.
* **The Justification**: **Spearman’s rank correlation** assesses monotonic relationships (not just linear) and is robust to outliers because it operates on the ranks of the data rather than raw values. Given the non-normal distribution of software metrics, Spearman is the scientifically superior choice for exploratory analysis in this domain.
* **Decision**: Spearman correlation will be the primary metric reported for complexity relationships, with Pearson provided only for reference.

### 3.3 Paired Permutation Test vs. McNemar’s Test
* **The Conflict**: McNemar’s test is designed for **paired nominal data** (e.g., a 2x2 contingency table of classification outcomes: Correct/Incorrect for Model A vs. Model B on the same samples). It tests for marginal homogeneity.
* **The Justification**: Our hypothesis is not about the agreement of classifications but about the **difference in continuous performance scores** (ROC-AUC) across multiple cross-validation folds. We have two sets of continuous scores (one for the Full Set model, one for the Single Best model) derived from the same data splits.
* **Decision**: The **Paired Permutation Test** (also known as a Randomization Test) is the appropriate non-parametric test. It makes no assumptions about the distribution of the score differences (which may not be normal due to the small number of folds, e.g., 5-fold CV). It directly tests the null hypothesis that the mean difference in ROC-AUC is zero by reshuffling the labels of the model scores. This is more powerful and appropriate than McNemar's for comparing continuous metric distributions.

## 4. Proposed Amendment Text

We propose that for **Project PROJ-038**, Constitution Principle VI be temporarily amended as follows:

> "For Project PROJ-038, statistical analysis shall utilize:
> 1. **Point-Biserial Correlation** for relationships between continuous metrics and binary bug labels.
> 2. **Spearman’s Rank Correlation** for relationships between continuous metrics to account for non-normal distributions and outliers.
> 3. **Paired Permutation Test** (10,000 permutations) for validating the statistical significance of differences in ROC-AUC scores between models, replacing McNemar’s test."

## 5. Conclusion

The requested methods (Point-Biserial, Spearman, Paired Permutation) are not a deviation from scientific rigor but a **refinement** to ensure the statistical tests match the data characteristics and research questions of software engineering bug prediction. Adhering strictly to the generic "Pearson/McNemar" rule would result in methodologically inappropriate analysis.

**Recommendation**: Approve AMEND-001-STATS to unblock the statistical analysis phase of the pipeline.