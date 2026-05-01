---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Algorithmic Fairness Metrics

**Field**: statistics

## Research question

Do systematic patterns exist in the discrepancies between common algorithmic fairness metrics (e.g., demographic parity, equalized odds, predictive parity) across different datasets and model types, and can dataset characteristics predict when these metrics diverge?

## Motivation

Algorithmic fairness is increasingly critical for deploying ML systems in high-stakes domains, yet practitioners often receive conflicting fairness assessments from different metrics on the same model. Understanding the statistical dependencies between these metrics and the dataset properties that drive their divergence would help researchers and practitioners select appropriate fairness measures and avoid misleading single-metric evaluations.

## Related work

- [Elliot: A Comprehensive and Rigorous Framework for Reproducible Recommender Systems Evaluation (2021)](https://doi.org/10.1145/3404835.3463245) — Provides a reproducible evaluation framework relevant to systematic fairness metric comparison, though focused on recommender systems rather than general fairness.
- [The Description of a Random Field by Means of Conditional Probabilities and Conditions of Its Regularity (1968)](https://doi.org/10.1137/1113026) — Foundational work on probabilistic dependencies; tangentially relevant to understanding metric correlations but not directly about fairness.

*Note: Lit-search returned limited directly relevant sources. TODO: Additional literature search needed on fairness metric relationships (e.g., Hardt et al. 2016, Chouldechova 2017, Kleinberg et al. 2016).*

## Expected results

We expect to identify strong statistical correlations between certain fairness metric pairs (e.g., demographic parity and equalized odds) that depend on base rate differences across protected groups. We will confirm these patterns using correlation analysis and regression models, with evidence strength measured by effect sizes and confidence intervals across 5+ public datasets.

## Methodology sketch

- Download 5-8 public datasets from UCI Machine Learning Repository (e.g., Adult, Bank Marketing) and ProPublica's COMPAS dataset via `wget`/`curl` (all <500MB each)
- Preprocess data to extract binary protected attributes and outcomes, ensuring privacy-compliant handling
- Train 3-5 baseline models per dataset (logistic regression, random forest, gradient boosting) using scikit-learn (CPU-only, <2GB RAM)
- Calculate 6+ fairness metrics per model: demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity
- Compute pairwise Pearson/Spearman correlations between all metric pairs across models and datasets
- Fit linear mixed-effects models to predict metric discrepancies from dataset characteristics (base rate difference, feature dimensionality, class imbalance ratio)
- Perform bootstrap resampling (n=1000) to estimate confidence intervals for correlation coefficients
- Generate visualization: heatmap of metric correlations, scatter plots of metric pairs with regression lines
- All computations must complete within 6-hour GHA job window; scale datasets to ≤100k rows if needed
- Output: correlation matrix, regression coefficients, and figures saved as PNG/PDF

## Duplicate-check

- Reviewed existing ideas: N/A (first flesh-out for this field)
- Closest match: None identified in corpus
- Verdict: NOT a duplicate
