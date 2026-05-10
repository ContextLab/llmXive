---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

**Field**: statistics

## Research question

How does data scaling influence Type I error rates and statistical power of common parametric tests under varying distributional assumptions?

## Motivation

Scaling methods are routinely applied before statistical testing, yet their systematic effects on inference validity remain poorly characterized. This gap matters because inappropriate scaling can inflate false positive rates or obscure true effects, leading to unreliable conclusions in applied research.

## Literature gap analysis

### What we searched

Searches were conducted on Semantic Scholar and arXiv using queries including "data scaling statistical test robustness," "standardization Type I error," and "preprocessing inference validity." The literature block returned six papers spanning stochastic processes, density estimation, statistical philosophy, and domain-specific applications (RNA-Seq, fMRI).

### What is known

- [Statistical Inference: The Big Picture (2011)](http://arxiv.org/abs/1106.2895v2) — Establishes that modern statistical practice transcends frequentist-Bayesian dichotomies and emphasizes interpretation validity, but does not address preprocessing effects on test properties.

### What is NOT known

No published work has systematically quantified how standardization, min-max, and robust scaling alter Type I error control and power across t-tests, ANOVA, and chi-squared tests under controlled distributional violations (e.g., non-normality, heteroscedasticity). Existing scaling discussions focus on machine learning performance rather than inferential validity.

### Why this gap matters

Applied researchers across biology, psychology, and social sciences routinely preprocess data without knowing whether their scaling choices compromise statistical inference. Filling this gap would enable evidence-based preprocessing guidelines that protect against false discoveries.

### How this project addresses the gap

The simulation-based methodology directly measures Type I error rates and power under known ground truth conditions with and without scaling, producing the first systematic evidence on how scaling choices interact with distributional assumptions to affect inferential validity.

## Expected results

We expect scaling to have negligible effects on Type I error for normally distributed data but to either inflate false positives or reduce power under non-normal or heteroscedastic conditions. The measurement will compare empirical rejection rates at nominal α levels across scaling methods, with evidence requiring 10,000+ simulation iterations to achieve tight confidence intervals around error rates.

## Methodology sketch

- Download 10-15 public datasets from UCI Machine Learning Repository and OpenML with continuous variables and known group labels (e.g., `wget` from https://archive.ics.uci.edu and https://www.openml.org)
- Generate synthetic data with controlled violations (non-normality via skewness, heteroscedasticity via group-specific variance) where ground truth Type I error is known (null hypothesis true) and power is known (alternative true)
- Apply three scaling methods: standardization (z-score), min-max scaling, and robust scaling (median/IQR) to all continuous predictors
- For each dataset/scaling combination, compute t-tests, one-way ANOVA, and chi-squared tests on group differences
- Record empirical Type I error rates (proportion of rejections at α=0.05 under null) and power (proportion of rejections under alternative) across 10,000+ simulation iterations
- Fit mixed-effects models to test whether scaling method significantly predicts deviation from nominal error rates, controlling for distributional assumption violations
- Produce figures comparing error rates across scaling methods with 95% confidence intervals using `matplotlib` or `seaborn`
- Validate all computations complete within 6-hour GHA job using parallelized simulation loops (≤7GB RAM, 2 CPU cores)

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: N/A (no existing corpus to compare against).
- Verdict: NOT a duplicate
