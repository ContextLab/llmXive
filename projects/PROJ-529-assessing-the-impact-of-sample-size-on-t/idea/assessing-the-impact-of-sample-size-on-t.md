---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Impact of Sample Size on the Reliability of Meta-Analytic Effect Sizes

**Field**: statistics

## Research question

How does the number of studies included in a meta-analysis affect the stability of the pooled effect size estimate and its confidence interval coverage?

## Motivation

Meta-analyses are foundational for evidence synthesis across health, social, and environmental sciences, yet the reliability of pooled effect estimates is often assumed rather than empirically validated. Understanding the minimum number of studies needed for stable meta-analytic conclusions would provide practical guidance for researchers designing and interpreting meta-analyses, particularly in fields where small numbers of studies are common.

## Related work

- [Exploring Consequences of Simulation Design for Apparent Performance of Statistical Methods. 2: Results from simulations with normally and uniformly distributed sample sizes](http://arxiv.org/abs/2007.05354v1) — Establishes how simulation design choices affect conclusions about statistical method performance in meta-analysis of log-odds-ratios.
- [Exploring Consequences of Simulation Design for Apparent Performance of Statistical Methods. 1: Results from simulations with constant sample sizes](http://arxiv.org/abs/2006.16638v2) — Documents simulation-based evaluation of meta-analysis methods with fixed sample sizes, providing methodological precedent for simulation studies.
- [Power failure: why small sample size undermines the reliability of neuroscience](https://doi.org/10.1038/nrn3475) — Demonstrates empirically that small sample sizes reduce statistical power and reliability, establishing the general principle that sample size affects result stability.
- [The phylogenetic effective sample size and jumps](http://arxiv.org/abs/1809.06672v1) — Introduces the concept of effective sample size in correlated data, providing a theoretical framework for understanding sample size beyond simple counts.

## Expected results

We expect to observe a non-linear relationship where effect size estimates become more stable as study count increases, with diminishing returns beyond a threshold (likely 10-20 studies). Confidence interval coverage should approach nominal levels (95%) as study count increases, and we will quantify the study count at which coverage stabilizes within 2% of the target.

## Methodology sketch

- Download publicly available meta-analysis datasets from Cochrane Library (https://www.cochranelibrary.com/) and Campbell Collaboration (https://campbellcollaboration.org/) repositories using `wget`/`curl` (target: 50+ meta-analyses with ≥10 component studies each)
- Parse effect sizes and standard errors from each component study using Python `pandas` and `numpy` (memory-efficient streaming to stay under 7GB RAM)
- Implement subsampling procedure: for each meta-analysis, create 100 bootstrap samples at study counts ranging from k=3 to k=N (where N is total studies)
- Compute pooled effect size (fixed and random effects models using `statsmodels` or `metafor`-equivalent Python implementation) for each subsample
- Calculate stability metrics: standard deviation of pooled effect across subsamples, bias relative to full-sample estimate, and confidence interval coverage rate
- Perform statistical analysis: fit generalized additive model (GAM) to model stability metrics as function of study count, identify inflection points using changepoint detection
- Generate diagnostic plots: stability curves with confidence bands, coverage plots by study count, funnel plots for selected examples
- Run all computations within 6-hour GHA job limit by parallelizing bootstrap iterations across CPU cores and using chunked processing for large meta-analyses

## Duplicate-check

- Reviewed existing ideas: None provided in input corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate
