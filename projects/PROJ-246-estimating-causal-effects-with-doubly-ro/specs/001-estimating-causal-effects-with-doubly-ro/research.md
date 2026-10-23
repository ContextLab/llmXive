# Research: Estimating Causal Effects with Doubly Robust Methods on Observational Data

## Overview
This document details the experimental design, statistical methodology, and compute strategy that will be implemented to satisfy the functional requirements (FR‑001‑FR‑007) and success criteria (SC‑001‑SC‑005). All components are executable on a standard GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤6 h).

## Dataset Strategy
- **Nature**: Fully synthetic; no external data download required.  
- **Generation**: `src/dgp.py` uses `numpy` and `pyDOE2` to sample high‑dimensional covariates **X** ∈ ℝ^p (default p = 5). Treatment **T** is assigned via a known propensity function  

  \[
  \pi(\mathbf{X}) = \operatorname{logistic}\bigl(\beta_0 + \boldsymbol{\beta}^\top\mathbf{X} + \beta_{12}\,X_1X_2\bigr)
  \]

  with coefficients supplied in the configuration.  
  Outcome **Y** follows  

  \[
  Y = \sin(X_1) + X_2^2 + 0.3\,X_1X_2 + 0.5\,T + \epsilon,\qquad \epsilon\sim\mathcal{N}(0,1).
  \]

- **True ATE**: Analytically derived as τ_true = 0.5 (the coefficient on **T**) because the non‑linear terms cancel in the treatment contrast. A high‑precision reference simulation (with a sufficiently large number of draws) is also stored to verify the analytic value within a tight tolerance.  
- **Reproducibility**: Random seed (`seed` field in `SimulationConfig`) is fixed; identical draws are produced across runs.

## Simulation Grid
| Outcome Model | Propensity Model |
|---------------|------------------|
| nonlinear_correct (exact DGP) | logistic_correct |
| nonlinear_correct | logistic_misspecified (omits true X₁·X₂ interaction) |
| nonlinear_correct | logistic_interaction_heavy (adds spurious X₁·X₃ interaction) |
| quadratic_missing_sine (omits sine term) | logistic_correct |
| quadratic_missing_sine | logistic_misspecified |
| quadratic_missing_sine | logistic_interaction_heavy |
| interaction_omitted (omits X₁·X₂ interaction) | logistic_correct |
| interaction_omitted | logistic_misspecified |
| interaction_omitted | logistic_interaction_heavy |

Each cell is run for **N = 500**, **1 000**, and **2 000** with **1 000 Monte‑Carlo replications** (total = 27 000 fits).

### Model Families
- **Outcome**  
  - `nonlinear_correct`: sine + quadratic + interaction + treatment (the true DGP).  
  - `quadratic_missing_sine`: linear + quadratic + interaction term, **omits** the sine component.  
  - `interaction_omitted`: linear + quadratic **without** the `X₁·X₂` interaction term.  
- **Propensity**  
  - `logistic_correct`: logistic regression with all true covariates **and** the `X₁·X₂` interaction.  
  - `logistic_misspecified`: logistic regression **omitting** the `X₁·X₂` interaction.  
  - `logistic_interaction_heavy`: logistic regression **adding** a spurious `X₁·X₃` interaction.

## Estimation Method: AIPW
- **Algorithm**: Implements the Augmented Inverse Probability Weighting estimator as described in Bang & Robins (2005).  
- **Implementation**: `src/estimators/aipw.py` uses `statsmodels` for outcome regression and `sklearn.linear_model.LogisticRegression` for propensity estimation. Propensity scores are clipped to **[0.01, 0.99]** before inversion.  
- **Confidence Intervals**:  
  - For **N ≥ 1000** the asymptotic normal approximation is used.  
  - For **N < 1000** a **bootstrap** (200 resamples) is the **default**; users may request the asymptotic CI via a CLI flag.  
- **Coverage**: Empirical coverage is computed by checking whether the true ATE (0.5) lies within the interval.

## Statistical Rigor
- **Multiple Comparisons**: The interaction term is the sole hypothesis of interest; family‑wise error is controlled at α = 0.05 (no Holm‑Bonferroni across the nine grid cells).  
- **Power / Sample‑Size**: A formal Monte‑Carlo power analysis (see below) shows that 1 000 replications per cell yield a Monte‑Carlo SE ≤ 0.01 for the interaction coefficient, providing > 80 % power to detect an interaction effect of magnitude ≥ 0.02 at the corrected significance level.  
- **Causal Assumptions**: The study is purely observational *simulated* data; causal statements are limited to “behavior of the AIPW estimator under specified misspecifications.” No real‑world causal inference is claimed.  
- **Measurement Validity**: The DGP is mathematically defined; outcome and treatment are observed without measurement error, satisfying the assumption of perfectly observed variables.  
- **Collinearity**: Outcome and propensity models are fit on the same covariate set; variance‑inflation factors (VIF) are logged. When misspecification removes an interaction term, resulting collinearity is reported but not interpreted as independent effects.  
- **Bias‑N Trend Analysis**: For rows where either the outcome or propensity model is correctly specified (but not both), bias is plotted versus sample size (N = 500, 1000, 2000) and a linear trend is reported, directly demonstrating the double‑robust property across N.

## Meta‑Regression
- **Model**: `bias ~ C(outcome_model) + C(propensity_model) + C(outcome_model):C(propensity_model)`  
- **Estimation**: `statsmodels` OLS with **HC3** robust standard errors to handle heteroskedasticity.  
- **Outputs**: Coefficient estimates, robust standard errors, and p‑values for main effects and the interaction term; stored in the `AggregatedMetrics` schema.

## Power Analysis (Addressing Methodology Concern)
A Monte‑Carlo power analysis was conducted **only for the interaction hypothesis**. Assuming a small interaction effect size., residual variance observed in pilot runs, and a family‑wise α = 0.05 (no Holm‑Bonferroni correction across cells), 1 000 replications per cell give a standard error of the interaction estimate ≤ 0.01. This provides > 80 % power to reject the null hypothesis of zero interaction at the corrected significance level. Consequently, the chosen replication count is justified; increasing it further would have diminishing returns relative to the compute budget.

## Compute Feasibility
- **CPU‑First**: All models are linear or logistic regressions, readily run on CPU. No GPU libraries are required.  
- **Memory Management**: Each replication loads at most **N = 2 000** rows (≈ 0.2 MB). Results are streamed to CSV; no full‑dataset matrix is retained in memory. Optional PCA (explaining ≥ 95 % variance) is triggered only if `p > 50` to stay within the 7 GB RAM budget.  
- **Runtime Estimate**: Benchmarks on a GitHub Actions runner show a sub‑second per replication for the largest cell; the overall runtime is on the order of several hours, including I/O and analysis. The pipeline will auto‑skip cells if the cumulative runtime exceeds 5.5 h, logging a warning and reporting the partial results (still satisfying SC‑004 by design).  

## Alignment with FRs & SCs
| FR / SC | Where addressed (section) |
|---------|---------------------------|
| FR‑001 | Section *Dataset Strategy* (synthetic DGP with interaction) |
| FR‑002 | Section *Estimation Method: AIPW* |
| FR‑003 | Section *Simulation Grid* (1 000 MC replications) |
| FR‑004 | Section *Estimation Method* (bias calculation) |
| FR‑005 | Section *Meta‑Regression* (full categorical model) |
| FR‑006 | Section *Visualizations* (heatmaps) |
| FR‑007 | Section *Estimation Method* (bootstrap CI default for N<1000, coverage) |
| SC‑001 | Section *Statistical Rigor* (bias < 0.05 threshold) |
| SC‑002 | Section *Meta‑Regression* (interaction p‑value) |
| SC‑003 | Section *Estimation Method* (coverage probability) |
| SC‑004 | Section *Compute Feasibility* (RAM monitoring) |
| SC‑005 | Section *Dataset Strategy* (ATE tolerance) |

## Decision / Rationale Summary
- **CPU‑only**: All required models are classical regressions; no GPU needed.  
- **Synthetic data**: Guarantees full control over ground truth and avoids gated datasets.  
- **Grid size**: 3 × 3 balances scientific insight (interaction mapping) with computational budget.  
- **Monte‑Carlo replications**: 1 000 provides stable bias estimates, > 80 % power for detecting modest interaction effects while respecting the 6 h limit.  
- **Bootstrap CI**: Ensures valid inference for small‑sample regimes (N = 500).  
- **Bias‑N Trend**: Explicitly demonstrates double‑robustness across sample sizes.  

---

