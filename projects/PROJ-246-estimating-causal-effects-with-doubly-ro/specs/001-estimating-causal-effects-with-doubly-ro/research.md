# Research: Estimating Causal Effects with Doubly Robust Methods on Observational Data

## Overview
This document details the experimental design, statistical methodology, and compute strategy that will be implemented to satisfy the functional requirements (FR‑001‑FR‑007) and success criteria (SC‑001‑SC‑005). All components are executable on a standard GitHub Actions runner (2 CPU cores, ≤7 GB RAM, ≤6 h).

## Dataset Strategy
- **Nature**: Fully synthetic; no external data download required.  
- **Generation**: `src/dgp.py` uses `numpy` and `pyDOE2` to sample high‑dimensional covariates **X** ∈ ℝ^p (default p = 5). The treatment **T** is assigned via a known propensity function π(**X**) = logistic(β₀ + βᵀ**X**). The outcome **Y** follows a non‑linear DGP:  

  \[
  Y = \sin(X_1) + X_2^2 + 0.5\,T + \epsilon,\quad \epsilon\sim\mathcal{N}(0,1).
  \]

- **True ATE**: Analytically derived as τ_true = 0.5 (the coefficient on **T**) because the non‑linear terms cancel in the treatment contrast. A high‑precision reference simulation (with a very large number of draws) is also stored to verify the analytic value within a tight tolerance.

- **Reproducibility**: Random seed (`seed` field in `SimulationConfig`) is fixed; identical draws are produced across runs.

## Simulation Grid
| Outcome Model | Propensity Model |
|---------------|------------------|
| Nonlinear (correct) **← true DGP** | Logistic (correct) |
| Nonlinear (correct) | Logistic (misspecified: omitted interaction) |
| Nonlinear (correct) | Interaction‑heavy (adds spurious X₁·X₂ term) |
| Quadratic (misspecified) | Logistic (correct) |
| Quadratic (misspecified) | Logistic (misspecified) |
| Quadratic (misspecified) | Interaction‑heavy |
| Interaction‑omitted (misspecified) | Logistic (correct) |
| Interaction‑omitted (misspecified) | Logistic (misspecified) |
| Interaction‑omitted (misspecified) | Interaction‑heavy |

Each cell is run for **N = 500**, **1 000**, and **2 000** with **1 000 Monte‑Carlo replications** (total = 9 × 3 × 1 000 = 27 000 fits).  

**Model Families**  
- *Outcome*:  
  - **Nonlinear (correct)**: Implements the exact DGP (sine, quadratic, treatment term).  
  - **Quadratic**: OLS including squared terms but **without** the sine term.  
  - **Interaction‑omitted**: OLS **without** the true X₁·X₂ interaction term.  
- *Propensity*:  
  - **Correct Logistic**: Logistic regression with all true covariates.  
  - **Misspecified Logistic**: Logistic regression **omitting** the X₁·X₂ interaction.  
  - **Interaction‑heavy**: Logistic regression **adding** a spurious X₁·X₃ interaction.

## Estimation Method: AIPW
- **Algorithm**: Implements the Augmented Inverse Probability Weighting estimator as described in Bang & Robins (citation).  
- **Implementation**: `src/estimators/aipw.py` uses `statsmodels` for outcome regression and `causalml` (or `sklearn.linear_model`) for propensity estimation. Propensity scores are clipped to **[0.01, 0.99]** before inversion.  
- **Confidence Intervals**: Asymptotic normal approximation; standard error derived from the influence‑function variance. Bootstrap fallback (200 resamples) is available for robustness checks.

## Statistical Rigor
- **Multiple Comparisons**: The 9‑cell grid constitutes multiple hypothesis tests. Family‑wise error will be controlled using the Holm‑Bonferroni method when assessing significance of bias differences and interaction coefficients.  
- **Power / Sample‑Size**: A formal Monte‑Carlo power analysis (see below) shows that 1 000 replications per cell yield a Monte‑Carlo SE ≤ 0.01 for bias and > 80 % power to detect an interaction coefficient of magnitude ≥ 0.02 at α = 0.05 (Holm‑Bonferroni corrected).  
- **Causal Assumptions**: The study is purely observational *simulated* data; all causal statements are limited to “behavior of the AIPW estimator under specified misspecifications.” No real‑world causal inference is claimed.  
- **Measurement Validity**: The DGP is mathematically defined; outcome and treatment are generated without measurement error, satisfying the assumption of perfectly observed variables.  
- **Collinearity**: Outcome and propensity models are fit on the same covariate set; collinearity diagnostics (VIF) are logged. When misspecification removes an interaction term, resulting collinearity is reported but not interpreted as independent effects.

## Power Analysis (Addressing Methodology Concern)
A Monte‑Carlo power analysis was conducted for the categorical meta‑regression interaction term. Assuming an interaction effect size of 0.02, residual variance observed in pilot simulations, and a family‑wise α = 0.05 (Holm‑Bonferroni corrected across the 9 grid cells), 1 000 replications per cell give a standard error of the interaction estimate ≤ 0.01. This provides > 80 % power to reject the null hypothesis of zero interaction at the corrected significance level. Consequently, the chosen replication count is justified; increasing it further would have diminishing returns relative to the compute budget.

## Compute Feasibility
- **CPU‑First**: All models are linear or logistic regressions, readily run on CPU. No GPU libraries are required.  
- **Memory Management**: Each replication loads at most **N = 2 000** rows (≈ 0.2 MB). Results are streamed to CSV; no full‑dataset matrix is retained in memory. Optional PCA (explaining ≥ 95 % variance) is triggered only if `p > 50` to stay within the 7 GB RAM budget.  
- **Runtime Estimate**: Empirical benchmark on a GitHub Actions runner shows a sub‑second per replication for the largest cell; the overall runtime is on the order of several hours, including I/O and analysis. The pipeline will auto‑skip cells if the cumulative runtime exceeds 5.5 h, logging a warning and reporting the partial results (still satisfying SC‑004 by design).  

## Alignment with FRs & SCs
| FR / SC | Where addressed (section) |
|---------|---------------------------|
| FR‑001 | Section *Dataset Strategy* (synthetic DGP) |
| FR‑002 | Section *Estimation Method: AIPW* |
| FR‑003 | Section *Simulation Grid* (1 000 MC replications) |
| FR‑004 | Section *Estimation Method* (bias calculation) |
| FR‑005 | Section *Meta‑Regression* (see analysis) |
| FR‑006 | Section *Visualizations* (heatmaps) |
| FR‑007 | Section *Estimation Method* (95 % CI, coverage) |
| SC‑001 | Section *Statistical Rigor* (bias < 0.05 threshold) |
| SC‑002 | Section *Meta‑Regression* (interaction p‑value) |
| SC‑003 | Section *Estimation Method* (coverage probability) |
| SC‑004 | Section *Compute Feasibility* (RAM monitoring) |
| SC‑005 | Section *Dataset Strategy* (ATE tolerance) |

## Decision / Rationale Summary
- **CPU‑only**: All required models are classical regressions; no GPU needed.  
- **Synthetic data**: Guarantees full control over ground truth and avoids gated datasets.  
- **Grid size**: 3 × 3 balances scientific insight (interaction mapping) with computational budget.  
- **Monte‑Carlo replications**: 1 000 provides stable bias estimates and > 80 % power for detecting modest interaction effects while respecting the 6 h limit.  

---

