---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Field**: statistics

## Research question

How do different missing data mechanisms (MCAR, MAR, MNAR) in randomized controlled trials affect the validity of p-values from complete-case analysis compared to methods designed to handle missingness (multiple imputation, inverse probability weighting)?

## Motivation

Missing data is pervasive in clinical RCTs, yet many published analyses rely on complete-case methods that assume data are missing completely at random (MCAR). When this assumption fails, p-values may be biased or inflated, leading to incorrect conclusions about treatment effects. Understanding when complete-case analysis remains reliable versus when it requires correction has direct implications for clinical trial reporting standards and evidence synthesis.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms: "missing data RCT p-value validity", "complete-case analysis bias clinical trial", "missing not at random statistical significance", and "multiple imputation vs complete-case RCT". Results were sparse: one tangentially related paper on causal inference platforms, no direct empirical comparisons of p-value validity across missingness mechanisms in RCT settings.

### What is known

- [The MR-Base platform supports systematic causal inference across the human phenome (2018)](https://doi.org/10.7554/elife.34408) — Establishes frameworks for causal inference using observational data, but does not address missing data mechanisms or p-value validity in RCTs specifically.

### What is NOT known

No published work has systematically quantified how p-values from complete-case analysis deviate from truth under controlled MCAR/MAR/MNAR conditions using real RCT data. There is no empirical benchmark identifying the missingness threshold at which complete-case analysis becomes unreliable for treatment effect inference.

### Why this gap matters

Clinicians and trialists routinely choose between complete-case and imputation methods without clear guidance on when the simpler approach is safe. Filling this gap would enable evidence-based recommendations for missing data handling in trial protocols, reducing the risk of spurious statistical significance in published research.

### How this project addresses the gap

This project will simulate realistic missingness patterns on public RCT datasets, compute p-values under complete-case and corrected methods, and quantify the divergence between them. The methodology directly measures the unknown: how missing data mechanisms distort statistical significance in practice.

## Expected results

We expect complete-case analysis to maintain nominal Type I error rates under MCAR but show inflated false positive rates under MAR and MNAR conditions. The magnitude of p-value distortion will serve as the primary evidence, with a threshold identified where complete-case analysis becomes unreliable (e.g., >10% deviation from expected significance levels).

## Methodology sketch

- Download 3-5 publicly available RCT datasets from clinicaltrials.gov or OpenML (e.g., datasets with binary/continuous outcomes and covariates)
- Extract treatment assignment, outcome, and covariate columns; document original sample size and missingness patterns
- Simulate missingness under three mechanisms: MCAR (random removal), MAR (missingness predicted by observed covariates), MNAR (missingness predicted by unobserved outcome values)
- For each mechanism, create missingness at 10%, 20%, 30%, 40% rates across 100 bootstrap iterations
- Compute treatment effect p-values using: (1) complete-case t-test/Wilcoxon, (2) multiple imputation (m=5) with chained equations, (3) inverse probability weighting
- Calculate Type I error rates under null hypothesis and power under alternative using known ground-truth effects from original data
- Compare p-value distributions across methods using Kolmogorov-Smirnov test and quantify bias in standard error estimates
- Generate visualizations: p-value histograms, Type I error vs. missingness rate curves, bias decomposition plots

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: None (no prior fleshed-out ideas on missing data validity in RCTs).
- Verdict: NOT a duplicate
