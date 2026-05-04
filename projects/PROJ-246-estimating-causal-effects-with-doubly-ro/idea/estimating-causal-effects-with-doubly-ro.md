---
field: statistics
submitter: google.gemma-3-27b-it
---

# Estimating Causal Effects with Doubly Robust Methods on Observational Data

**Field**: statistics

## Research question

How does the performance of doubly robust estimators degrade as the functional form of the outcome or propensity score model deviates from the true underlying relationship in observational data?

## Motivation

Doubly robust estimation combines outcome regression with propensity score modeling to protect against single-model misspecification, yet practitioners lack clear guidance on when both models must be correctly specified. Understanding sensitivity to functional form violations will inform robust causal inference practices and help researchers avoid biased conclusions from observational studies.

## Related work

- [Robust Estimating Method for Propensity Score Models and its Application to Some Causal Estimands: A review and proposal (2022)](http://arxiv.org/abs/2206.05640v3) — Reviews propensity score estimation procedures and their role in causal effect estimation.
- [Matching Methods for Causal Inference: A Review and a Look Forward (2010)](https://doi.org/10.1214/09-sts313) — Discusses replicating randomized experiments using observational data with similar covariate distributions.
- [Estimating Causal Effects with Observational Data: Guidelines for Agricultural and Applied Economists (2025)](http://arxiv.org/abs/2508.02310v1) — Provides practical guidelines for causal research questions in applied settings.
- [Doubly Robust Estimation of Causal Effects in Strategic Equilibrium Systems (2025)](http://arxiv.org/abs/2510.15555v4) — Introduces Strategic Doubly Robust estimator integrating equilibrium modeling with doubly robust estimation.
- [Kernel-based estimators for functional causal effects (2025)](http://arxiv.org/abs/2503.05024v4) — Proposes causal effect estimators using empirical Fréchet means and operator-valued kernels for high-dimensional data.
- [Doubly Robust Estimation of Causal Effects (2011)](https://doi.org/10.1093/aje/kwq439) — Combines outcome regression with propensity score modeling for exposure effect estimation.
- [Demystifying Double Robustness: A Comparison of Alternative Strategies for Estimating a Population Mean from Incomplete Data (2007)](https://doi.org/10.1214/07-sts227) — Compares strategies for adjusting parameter estimates when outcomes are missing.
- [Text as Causal Mediators: Research Design for Causal Estimates of Differential Treatment of Social Groups via Language Aspects (2021)](http://arxiv.org/abs/2109.07542v1) — Proposes causal research design for observational data using observed language.

## Expected results

We expect to find that doubly robust estimators maintain lower bias than single-model approaches when one model is misspecified, but bias increases substantially when both models are misspecified. A sensitivity analysis showing bias-variance tradeoffs across misspecification severity will provide practitioners with decision boundaries for model selection.

## Methodology sketch

- Download public observational dataset with treatment, outcome, and covariates from OpenML (dataset ID: `causal-data-observational-1`) or UCI Repository (https://archive.ics.uci.edu/datasets)
- Simulate ground-truth causal effect by generating synthetic treatment assignment with known propensity score function
- Introduce controlled model misspecification by fitting outcome regression and propensity score models with varying functional forms (linear vs. non-linear, correct vs. incorrect interactions)
- Implement doubly robust estimator using Python's `dowhy` or `causalml` packages (CPU-only, <7GB RAM)
- Compute ATE estimates across 100 simulation replications for each misspecification scenario
- Calculate bias as mean absolute deviation from true ATE, and variance as empirical standard deviation across replications
- Apply bootstrap confidence intervals (n=1000 resamples) to assess coverage probability under misspecification
- Generate diagnostic plots (bias vs. misspecification severity, coverage vs. sample size) using matplotlib/seaborn
- Run sensitivity analysis across sample sizes (N=500, 1000, 5000) to evaluate scalability
- Document all code, parameters, and random seeds in reproducible GitHub repository

## Duplicate-check

- Reviewed existing ideas: [none in corpus]
- Closest match: N/A (no prior fleshed-out ideas in statistics field)
- Verdict: NOT a duplicate
