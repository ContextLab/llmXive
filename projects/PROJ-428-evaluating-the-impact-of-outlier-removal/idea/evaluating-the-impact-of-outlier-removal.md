---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Outlier Removal Methods on Variance Estimation

**Field**: statistics

## Research question

How does outlier contamination affect variance estimation accuracy across different distribution types, and which removal strategies minimize estimation bias and mean squared error under varying contamination levels?

## Motivation

Real-world datasets frequently contain outliers that inflate variance estimates, compromising downstream statistical inference and hypothesis testing. While robust statistical methods exist, there is no systematic empirical guidance on which outlier removal strategy performs best under specific contamination scenarios. This project addresses that gap by quantifying the trade-offs between bias and variance in estimation after applying different removal techniques.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: "outlier removal variance estimation," "robust variance estimation methods," "trimmed mean variance bias," and "winsorization statistical inference." The literature block returned only one directly relevant result focused on V-statistics asymptotics rather than practical outlier removal evaluation.

### What is known

- [$V$-statistics and Variance Estimation (2019)](http://arxiv.org/abs/1912.01089v2) — Establishes a theoretical framework for analyzing asymptotics of V-statistics, but does not address practical outlier removal strategies or their empirical impact on variance estimation accuracy.

### What is NOT known

No published work has systematically compared common outlier removal methods (IQR filtering, winsorization, trimmed means) across multiple distribution types and contamination levels to quantify their bias and mean squared error in variance estimation. Theoretical results exist for specific robust estimators, but practitioners lack empirical guidance on method selection for real datasets.

### Why this gap matters

Practitioners in fields from quality control to econometrics need evidence-based guidance on outlier handling to ensure valid statistical inference. Without systematic comparison, method selection remains ad hoc, potentially introducing unquantified bias into downstream analyses and compromising reproducibility.

### How this project addresses the gap

This project empirically evaluates multiple outlier removal strategies using simulated contamination on public datasets, directly measuring bias and MSE of resulting variance estimates. The methodology produces previously unavailable evidence on which methods minimize estimation error under specific contamination scenarios.

## Expected results

We expect to find that no single method dominates across all distributions and contamination levels, with IQR filtering performing better for heavy-tailed distributions and winsorization excelling under moderate contamination. The level of evidence needed is consistent bias/MSE measurements across at least 5 distribution types and 4 contamination levels (0%, 5%, 10%, 20%).

## Methodology sketch

- Download 5+ public datasets from UCI Machine Learning Repository (e.g., Adult, Wine Quality, Boston Housing) using `wget`/`curl` commands
- For each dataset, identify univariate continuous variables and compute baseline variance estimates
- Simulate outlier contamination by injecting extreme values at 0%, 5%, 10%, and 20% rates
- Apply three removal methods: (1) IQR filtering (1.5× rule), (2) winsorization (5th/95th percentiles), (3) trimmed mean (10% trimming)
- Compute variance estimates after each removal method and compare to known true variance (from uncontaminated data) or robust benchmark (median absolute deviation-based)
- Calculate bias (mean difference from true variance) and mean squared error across 100 Monte Carlo replicates per condition
- Apply two-sample t-tests or ANOVA to compare MSE between methods, with Bonferroni correction for multiple comparisons
- Visualize results with interaction plots showing method performance across contamination levels and distribution types
- All computation fits within 7GB RAM and 6-hour GitHub Actions runner limits using Python with numpy/pandas/scipy

## Duplicate-check

- Reviewed existing ideas: [variance estimation robustness, outlier detection benchmarks, distributional shift analysis]
- Closest match: variance estimation robustness (similarity sketch: both address variance estimation but this project focuses specifically on outlier removal methods rather than robust estimators)
- Verdict: NOT a duplicate
