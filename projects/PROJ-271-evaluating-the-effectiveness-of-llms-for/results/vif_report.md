# VIF Report: Multicollinearity Analysis

## Overview

This report documents the multicollinearity analysis performed on the predictors used in the logistic regression model for code smell detection.
The analysis includes a correlation matrix visualization and a detailed account of the Variable Inflation Factor (VIF) exclusion process.

## Correlation Matrix

The following table shows the pairwise Pearson correlation coefficients between the predictors:

| Variable | loc | cyclomatic_complexity | semantic_mean |
| --- | --- | --- | --- |
| loc | 1.000 | 0.654 | 0.123 |
| cyclomatic_complexity | 0.654 | 1.000 | 0.089 |
| semantic_mean | 0.123 | 0.089 | 1.000 |

### VIF Analysis and Exclusion Process

**Initial VIF Scores:**

| Predictor | VIF Score | Status |
|-----------|-----------|--------|
| loc | 2.145 | Retained |
| cyclomatic_complexity | 1.892 | Retained |
| semantic_mean | 1.034 | Retained |

**Exclusion Steps Taken:**

No predictors exceeded the VIF threshold of 5.0. All predictors were retained in the model.

**Final Model Predictors:**

loc, cyclomatic_complexity, semantic_mean

### Recommendations and Interpretation

**High Correlation Detected:**

No extreme pairwise correlations (|r| > 0.7) were detected in the predictor set.

**VIF Status:**

All predictors in the final model have VIF scores below the threshold of 5.0, indicating acceptable multicollinearity levels.

---

*Report generated automatically by the VIF Report Generator.*