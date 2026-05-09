---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Data Scaling on Statistical Test Sensitivity

**Field**: statistics

## Research question

Does the choice of data scaling method (standardization, normalization, robust scaling) significantly alter p-values and effect sizes produced by common statistical tests (t-test, ANOVA, chi-squared), and does this effect depend on underlying data distribution characteristics?

## Motivation

Statistical inference pipelines routinely apply data scaling before hypothesis testing, yet there is little systematic evidence on whether different scaling methods produce substantively different inferential conclusions. This gap matters because practitioners may inadvertently bias their results by choosing a scaling method without understanding its impact on test statistics, particularly when data violate normality assumptions or contain outliers.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: (1) "data scaling statistical test sensitivity" and (2) "standardization normalization hypothesis testing p-value impact." Retrieved 7 papers from the literature block, but none directly address how preprocessing scaling choices affect frequentist test outcomes.

### What is known

- [Statistical Inference: The Big Picture (2011)](http://arxiv.org/abs/1106.2895v2) — Establishes that statistical practice has moved beyond frequentist-Bayesian controversies, emphasizing interpretation of results but not addressing preprocessing sensitivity.
- [A flexible, interpretable framework for assessing sensitivity to unmeasured confounding (2016)](https://doi.org/10.1002/sim.6973) — Addresses sensitivity to confounding in causal inference, demonstrating the importance of sensitivity analysis but not for preprocessing scaling choices.

### What is NOT known

No published work has systematically quantified how scaling methods (standardization vs. normalization vs. robust scaling) alter p-values and effect sizes across common statistical tests. There is also no published guidance on which data distribution characteristics (skewness, kurtosis, outlier frequency) predict when scaling choice will meaningfully change inferential conclusions.

### Why this gap matters

Practitioners in applied statistics, data science, and empirical research need evidence-based guidance on scaling choices to avoid inadvertently biasing hypothesis test results. Filling this gap would enable more reproducible statistical practice and clarify when scaling preprocessing is consequential versus innocuous.

### How this project addresses the gap

This project will download multiple UCI datasets with varying distribution characteristics, apply different scaling methods, conduct standard statistical tests, and quantify differences in p-values and effect sizes. The methodology directly produces the previously unavailable evidence on scaling-induced inferential variation.

## Expected results

We expect to observe that scaling method choice produces negligible differences for normally distributed data but meaningful p-value shifts (Δp > 0.05) for skewed or outlier-contaminated distributions. This would be confirmed by measuring effect size differences and conducting equivalence tests; the null finding (scaling has no effect) would also be informative by validating current common practice.

## Methodology sketch

- Download 10-15 publicly available datasets from UCI Machine Learning Repository with documented distribution characteristics (e.g., https://archive.ics.uci.edu/datasets)
- For each dataset, extract continuous variables suitable for t-test/ANOVA/chi-squared analysis
- Apply three scaling methods: standardization (z-score), min-max normalization, and robust scaling (median/IQR-based)
- Conduct paired t-tests on two-group variables and one-way ANOVA on multi-group variables for each scaled version
- Record p-values, effect sizes (Cohen's d, eta-squared), and 95% confidence intervals for all test-scaling combinations
- Compute distribution metrics (skewness, kurtosis, outlier ratio) to characterize each dataset
- Perform correlation analysis between distribution metrics and p-value differences across scaling methods
- Use bootstrap resampling (n=1000 iterations) to assess stability of scaling-induced p-value differences
- Generate summary tables and visualizations showing when scaling choice meaningfully impacts inferential conclusions
- Document all code and data URLs in a reproducible workflow compatible with GitHub Actions free-tier (2 CPU, 7GB RAM, 6h max)

## Duplicate-check

- Reviewed existing ideas: [None in current corpus for this field]
- Closest match: No prior fleshed-out ideas found in statistics field
- Verdict: NOT a duplicate
