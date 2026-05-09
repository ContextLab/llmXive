---
field: statistics
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

**Field**: statistics

## Research question

What is the relationship between model sparsity and the probability of correctly identifying true predictors in linear regression across varying signal-to-noise ratios?

## Motivation

Practitioners routinely apply variable selection to improve parsimony, yet the cost of this reduction on statistical power remains empirically under-quantified. Without evidence on how selection procedures degrade detection rates, researchers risk high false-negative rates when interpreting non-significant results. This project addresses the gap between theoretical power analysis and the empirical reality of model selection.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and OpenAlex using terms including "variable selection statistical power", "LASSO regression type II error", and "stepwise selection power analysis". The search returned limited direct empirical comparisons of selection-induced power loss on real-world covariance structures.

### What is known

- [Statistical power analyses using G*Power 3.1: Tests for correlation and regression analyses (2009)](https://doi.org/10.3758/brm.41.4.1149) — Provides standard tools for *a priori* power calculation but assumes fixed model specifications without accounting for selection steps.

### What is NOT known

No published work has empirically quantified the reduction in power specifically caused by the variable selection process itself when applied to datasets with realistic, non-orthogonal predictor covariance structures. Current literature focuses on theoretical properties or fixed-model power, leaving the practical trade-off between parsimony and detection unknown.

### Why this gap matters

Filling this gap prevents researchers from falsely concluding "no effect" due to selection-induced power loss rather than true null effects. This impacts fields relying on regression for causal inference or feature importance, such as epidemiology and social science.

### How this project addresses the gap

The methodology uses real-world covariance structures from public datasets to simulate ground-truth scenarios, allowing direct measurement of selection-induced power loss. This bridges the theoretical tools (G*Power) with the empirical reality of model building.

## Expected results

We expect variable selection procedures to exhibit lower empirical power than full models when true signal strength is low, as true predictors may be erroneously dropped. Conversely, in high-noise regimes, selection may maintain or improve power by excluding irrelevant noise variables. The magnitude of this trade-off will be quantified across sparsity levels.

## Methodology sketch

- Download 10 regression datasets from OpenML (e.g., via `curl` to `https://www.openml.org/api/v1/data`) to estimate predictor covariance and noise structures.
- Simulate 1,000 synthetic outcome vectors ($Y$) for each dataset using known true coefficients (varying sparsity and signal-to-noise ratios).
- Apply three selection methods: Forward Stepwise, Backward Elimination, and LASSO (via `glmnet` or `statsmodels`), recording selected variables.
- Calculate empirical power as the proportion of true non-zero coefficients correctly retained across the 1,000 simulations per condition.
- Compare power rates across methods and sparsity levels using Kruskal-Wallis tests followed by Dunn's post-hoc analysis.
- Visualize power curves (Power vs. Signal-to-Noise Ratio) for each selection method to identify crossover points.

## Duplicate-check

- Reviewed existing ideas: None provided in this context.
- Closest match: N/A.
- Verdict: NOT a duplicate.
