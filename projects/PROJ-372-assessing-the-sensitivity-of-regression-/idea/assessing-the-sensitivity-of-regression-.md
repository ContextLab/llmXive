---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

**Field**: statistics

## Research question

How does the variability of ordinary least squares regression coefficients scale with sample size and predictor collinearity across diverse public observational datasets?

## Motivation

Publicly available datasets often represent convenience samples where the specific rows included may not fully capture population heterogeneity. If regression coefficients are highly sensitive to which specific subset of observations is analyzed, published effect sizes may be unstable. This project addresses the gap between theoretical sampling distributions and empirical stability in real-world public data, helping researchers gauge the reliability of standard regression outputs.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for terms including "regression coefficient stability," "dataset subset selection sensitivity," "OLS sampling variability," and "data subset selection statistical inference." The search returned results focused primarily on machine learning data efficiency or feature selection rather than observational data sensitivity.

### What is known

- [A Weighted K-Center Algorithm for Data Subset Selection (2023)](http://arxiv.org/abs/2312.10602v1) — Establishes methods for selecting data subsets to reduce annotation costs in deep learning, focusing on efficiency rather than statistical stability of coefficients.
- [On best subset regression (2011)](http://arxiv.org/abs/1112.0918v2) — Discusses variable selection (subset of features) via $\ell_0$-norm constraints, which is distinct from subset selection of observations (data points).
- [Structured penalized regression for drug sensitivity prediction (2019)](http://arxiv.org/abs/1902.04996v3) — Applies penalized regression to a specific oncology domain without addressing general coefficient sensitivity to data sampling.

### What is NOT known

There is no systematic empirical quantification of how ordinary least squares (OLS) coefficient variance behaves across random observation subsets in general-purpose public datasets. Specifically, no published work has mapped the relationship between dataset collinearity metrics and the empirical stability of coefficients under row-wise subsampling.

### Why this gap matters

Researchers relying on public benchmarks need to know if a reported coefficient is robust or an artifact of a specific sample configuration. Filling this gap provides a practical heuristic for assessing the reliability of regression findings in data-limited or convenience-sampled contexts.

### How this project addresses the gap

This project will execute a simulation study across multiple UCI datasets, systematically varying subset sizes and measuring coefficient variance. By correlating this variance with dataset-level metrics (e.g., condition number), we produce the first empirical map of sensitivity drivers in standard regression contexts.

## Expected results

We expect to find that coefficient variability decreases non-linearly with sample size, but remains high in datasets with high predictor collinearity regardless of subset size. Evidence will be confirmed by a significant negative correlation between sample size and coefficient standard deviation across the dataset corpus.

## Methodology sketch

- Download 10 structured numerical datasets from the UCI Machine Learning Repository using `wget` (e.g., `https://archive.ics.uci.edu/ml/datasets.php`).
- Preprocess each dataset to remove missing values and standardize predictors using `scikit-learn`.
- For each dataset, compute the condition number of the design matrix as a measure of collinearity.
- Generate 100 random subsets of observations for each target sample size (10%, 25%, 50%, 75%, 100% of original N).
- Fit an OLS regression model on each subset using `statsmodels` and record the estimated coefficients.
- Calculate the standard deviation of each coefficient across the 100 subsets to quantify sensitivity.
- Perform a linear regression analysis to test the relationship between dataset condition number and mean coefficient variability.
- Visualize results using `matplotlib` to show sensitivity curves across different datasets.
- Verify all computations complete within 6 hours on a single CPU core by limiting bootstrap iterations to 100 per dataset.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: Standard bootstrap tutorials (distinct focus on stability mapping vs. CI estimation).
- Verdict: NOT a duplicate
