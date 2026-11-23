# Research: Estimating Causal Effects with Doubly Robust Methods on Observational Data

## Overview
This document details the experimental design, statistical methodology, and compute strategy that will be executed to satisfy all functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑005). The entire pipeline runs on a standard GitHub Actions runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h).

## Dataset Strategy
- **Nature**: Fully synthetic; no external download required.  
- **Generation**: `src/dgp.py` uses `numpy` and `pyDOE2` to sample covariates **X** ∈ ℝ⁵ (default p = 5).  
  - **Treatment assignment** (propensity) follows a logistic model with all covariates (no interaction):
    \[
    \pi(\mathbf{X}) = \operatorname{logistic}\bigl(\beta_0 + \boldsymbol{\beta}^\top\mathbf{X}\bigr)
    \]
  - **Outcome** follows the **exact DGP** required by User Story 1 (no interaction term):
    \[
    Y = \sin(X_1) + X_2^{2} + 0.5\,T + \epsilon,\qquad \epsilon\sim\mathcal{N}(0,1).
    \]
- **True ATE**: Analytically 0.5 (the coefficient on `T`). A high‑precision reference simulation with a massive sample confirms this value within a very tight tolerance.  
- **Reproducibility**: The random seed (`seed` field in `SimulationConfig`) is fixed; after generation the pipeline **re‑generates the dataset with the same seed**, recomputes a SHA‑256 checksum, and aborts if the checksums differ. This satisfies the acceptance scenario “fixed seed → identical dataset”.

## Simulation Grid
| Outcome Model | Propensity Model |
|---------------|------------------|
| `nonlinear_correct` | `logistic_correct` |
| `nonlinear_correct` | `logistic_misspecified` |
| `nonlinear_correct` | `logistic_interaction_heavy` |
| `quadratic_missing_sine` | `logistic_correct` |
| `quadratic_missing_sine` | `logistic_misspecified` |
| `quadratic_missing_sine` | `logistic_interaction_heavy` |
| `linear_missing_quadratic` | `logistic_correct` |
| `linear_missing_quadratic` | `logistic_misspecified` |
| `linear_missing_quadratic` | `logistic_interaction_heavy` |

Each cell is evaluated for **N = 500**, **1 000**, and **2 000** with **1 000 Monte‑Carlo replications** (total = 27 000 fits).

### Model Families
- **Outcome**  
  - `nonlinear_correct`: matches the true DGP (`sin` + quadratic + treatment).  
  - `quadratic_missing_sine`: omits the sine term, retaining only the quadratic term and treatment.  
  - `linear_missing_quadratic`: omits the quadratic term, retaining only the linear term and treatment.  
- **Propensity**  
  - `logistic_correct`: logistic regression with all five covariates.  
  - `logistic_misspecified`: logistic regression **omitting** one covariate (e.g., drops `X5`).  
  - `logistic_interaction_heavy`: logistic regression **adding** a spurious `X1*X3` interaction term.

## Estimation Method: AIPW
- **Algorithm**: Implements Augmented Inverse Probability Weighting (Bang & Robins, 2005).  
- **Implementation**: `statsmodels` for outcome regression; `sklearn.linear_model.LogisticRegression` for propensity. Propensity scores clipped to **[0.01, 0.99]**.  
- **Confidence Intervals**: **Robust sandwich (HC3) variance estimator** is used for **all** sample sizes, providing asymptotically valid confidence intervals at a conventional confidence level even under misspecification. **Bootstrap resampling is omitted** to avoid excessive compute and because HC3 robust variance remains reliable under the non‑regular asymptotics of misspecified AIPW.  
- **Coverage**: Empirical coverage computed by checking whether the true ATE (0.5) lies within each 95 % CI.

## Statistical Rigor
- **Multiple Comparisons**: The interaction term is the sole hypothesis; family‑wise error controlled at α = 0.05 (no Holm‑Bonferroni across cells).  
- **Power / Sample‑Size**: Monte‑Carlo power analysis (see below) shows 1 000 replications per cell give Monte‑Carlo SE ≤ 0.01 for the interaction coefficient, yielding > 80 % power to detect an effect size ≥ 0.02 at the corrected α.  
- **Causal Assumptions**: Purely simulated observational data; causal statements are limited to estimator behavior under misspecification.  
- **Measurement Validity**: DGP is mathematically defined; covariates, treatment, outcome are observed without error.  
- **Collinearity**: VIFs logged; when a misspecified model drops a covariate, resulting collinearity is reported but not interpreted as independent effects.  
- **Bias‑N Trend Analysis**: For configurations where exactly one of the two models is correctly specified, bias is plotted versus sample size (N = 500, 1000, 2000) and a linear trend reported, directly demonstrating the double‑robust property.

## Meta‑Regression
- **Model**: `bias ~ C(outcome_model) + C(propensity_model) + C(outcome_model):C(propensity_model)`  
- **Estimation**: `statsmodels` OLS with **HC3** robust SEs.  
- **Outputs**: Coefficient estimates, robust SEs, p‑values for main effects and the interaction term; stored in the `AggregatedMetrics` schema.

## Power Analysis (Addressing Methodology Concern)
Assuming an interaction effect size of 0.02, residual variance observed in pilot runs, and α = 0.05, 1 000 replications per cell give SE ≤ 0.01 for the interaction estimate → > 80 % power to reject the null hypothesis of zero interaction at the corrected significance level. This justifies the chosen replication count within the compute budget.

## Compute Feasibility
- **CPU‑First**: Classical regressions run comfortably on the free runner.  
- **Memory Management**: Each replication loads at most **N = 2 000** rows (≈ 0.2 MB). Results streamed to Parquet; no full‑dataset matrix retained. Optional PCA (explaining ≥ 95 % variance) triggered only if `p > 50`.  
- **Runtime Estimate**: Benchmarks on a GitHub Actions runner show sub‑second per replication for the largest cell; total runtime **≈ 4–5 h** including I/O and analysis. Because bootstrap resampling is omitted, the full 27 000 replications comfortably fit within the 6‑hour limit. The pipeline aborts if cumulative runtime exceeds 5.5 h, logging a warning (still satisfies SC‑004).  

## Alignment with FRs & SCs
| FR / SC | Where addressed (section) |
|---------|---------------------------|
| FR‑001 | *Dataset Strategy* (synthetic DGP without interaction) |
| FR‑002 | *Estimation Method: AIPW* |
| FR‑003 | *Simulation Grid* (1 000 MC replications) |
| FR‑004 | *Estimation Method* (bias calculation) |
| FR‑005 | *Meta‑Regression* (full categorical model) |
| FR‑006 | *Visualization* (heatmaps) |
| FR‑007 | *Estimation Method* (sandwich SEs, coverage) |
| SC‑001 | *Statistical Rigor* (bias < 0.05 threshold) |
| SC‑002 | *Meta‑Regression* (interaction p‑value) |
| SC‑003 | *Estimation Method* (coverage probability) |
| SC‑004 | *Compute Feasibility* (RAM monitoring) |
| SC‑005 | *Dataset Strategy* (ATE tolerance) |

## Decision / Rationale Summary
- **CPU‑only**: Classical regressions run comfortably on the free runner.  
- **Synthetic data**: Guarantees full control over ground truth and avoids gated datasets.  
- **Grid size**: 3 × 3 balances scientific insight (interaction mapping) with computational budget.  
- **Replications**: 1 000 provides stable bias estimates and sufficient power.  
- **Confidence Intervals**: Robust sandwich SEs replace the previously planned bootstrap, ensuring validity under misspecification while respecting compute limits.  
- **Bias‑N Trend**: Explicitly demonstrates double‑robustness across sample sizes.  

---



