---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Statistical Significance of A/B Test Results with Non-Independent Observations

**Field**: statistics

## Research question

To what extent does intra-cluster correlation in user clickstream data inflate Type I error rates in standard A/B tests, and can cluster-robust standard errors or permutation tests restore nominal error rates?

## Motivation

Standard A/B testing assumes independent observations, but user sessions and device usage create correlated data structures. Ignoring this dependence leads to false positives and misguided product decisions; quantifying this risk is critical for reliable experimentation in digital platforms.

## Related work

- [Statistical Inference: The Big Picture (2011)](http://arxiv.org/abs/1106.2895v2) — Discusses the philosophy of statistical practice and interpretation, providing context for evaluating inference validity under assumption violations.
- [pROC: an open-source package for R and S+ to analyze and compare ROC curves (2011)](https://doi.org/10.1186/1471-2105-12-77) — Presents tools for comparing classifier performance, relevant to methodological comparison of statistical test accuracy.

## Expected results

Standard t-tests will exhibit Type I error rates significantly exceeding 5% under moderate correlation, while cluster-robust methods will maintain error rates near the nominal level. Evidence will be quantified via simulation-based power analysis.

## Methodology sketch

- Download public clickstream data (e.g., UCI Online Retail dataset: https://archive.ics.uci.edu/ml/datasets/Online+Retail) to establish baseline session structures.
- Generate synthetic treatment/control labels with varying intra-cluster correlation coefficients (ICC) using Python `numpy`.
- Implement standard two-sample t-test and chi-squared test for independence as baselines.
- Implement cluster-robust variance estimation and block permutation tests as alternatives.
- Run 1,000 Monte Carlo simulations per correlation level to estimate empirical Type I error rates.
- Compare observed error rates against nominal alpha (0.05) using confidence intervals.
- Ensure all computations are parallelized within the 7GB RAM limit using `joblib` or sequential batches.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: N/A (Fresh topic).
- Verdict: NOT a duplicate
