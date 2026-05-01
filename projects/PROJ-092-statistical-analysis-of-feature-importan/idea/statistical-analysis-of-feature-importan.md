---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Feature Importance Drift in Pre-trained Models

**Field**: statistics

## Research question

How do feature importance rankings in pre-trained tree-based models drift when applied to sequentially sampled time-series data, and can this drift be statistically distinguished from random variation using rank correlation tests?

## Motivation

Model reliability degrades as data distributions shift (concept drift), but feature-level instability is less quantified than prediction accuracy loss. This gap hinders robust model maintenance strategies, as practitioners often retrain without understanding if specific features have fundamentally lost predictive power. Quantifying this drift allows for targeted recalibration rather than full model replacement.

## Related work

- [Semantic Importance-Aware Communications Using Pre-trained Language Models (2023)](http://arxiv.org/abs/2302.07142v2) — Discusses importance mechanisms in pre-trained models, providing context for defining feature relevance in modern architectures.
- [Statistical Modeling of Spatial Extremes (2012)](http://arxiv.org/abs/1208.3378v1) — Offers statistical frameworks for modeling distributional changes, applicable to drift analysis over time or space.
- [Statistical Inference: The Big Picture (2011)](http://arxiv.org/abs/1106.2895v2) — Establishes principles for interpreting statistical results and significance in modern practice, guiding the drift significance tests.

## Expected results

We expect to observe a statistically significant decline in rank correlation (Spearman's rho) of feature importances across sequential time windows compared to a static baseline. The measurement will be confirmed by p-values < 0.05 on Kendall's tau tests between adjacent windows, indicating non-random drift. Evidence will be considered strong if drift magnitude correlates with known distribution shift events in the dataset metadata.

## Methodology sketch

- Download the UCI Electricity Load Diagrams 2011-2014 dataset from `https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014` to a local `data/` directory using `wget`.
- Preprocess data by normalizing features and splitting into 30-day sequential time windows.
- Train a baseline Random Forest classifier/regressor (using `scikit-learn`) on the initial training window.
- Compute permutation importance scores for all features within each subsequent time window.
- Calculate Spearman rank correlation coefficients between feature importance rankings of consecutive windows.
- Apply a Mann-Kendall trend test to the sequence of correlation coefficients to detect monotonic drift.
- Visualize drift trajectories using `matplotlib` to identify specific features with high variance.
- Ensure all computations run within a single Python script under 2 CPU cores and 4GB RAM to fit GHA free-tier limits.

## Duplicate-check

- Reviewed existing ideas: None available in context.
- Closest match: None (simulated check against local corpus).
- Verdict: NOT a duplicate
