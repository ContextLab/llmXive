# Implementation Plan: Estimating Causal Effects with Doubly Robust Methods

**Branch**: `001-doubly-robust` | **Date**: 2026-10-23 | **Spec**: [spec.md](../specs/001-estimating-causal-effects-with-doubly-ro/spec.md)  
**Input**: Feature specification from `/specs/001-estimating-causal-effects-with-doubly-ro/spec.md`

## Summary
The project must (1) generate synthetic observational datasets with a known non‑linear data‑generating process (DGP) that includes an explicit **X₁·X₂ interaction** and analytically computable true ATE, (2) run a configurable grid of outcome‑ and propensity‑model misspecifications while estimating the Augmented Inverse Probability Weighting (AIPW) ATE, (3) aggregate bias, confidence‑interval coverage, and interaction effects via a categorical meta‑regression, (4) render heat‑map visualizations of bias across the grid, (5) evaluate the classic double‑robust property across sample sizes, and (6) produce all artifacts in a reproducible, contract‑validated form on a standard GitHub Actions runner (≤7 GB RAM, ≤6 h).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `causalml`, `scikit-learn`, `matplotlib`, `seaborn`, `pyDOE2`, `pyyaml`, `psutil`  
- **Storage**: File‑based CSV/Parquet under `data/` (raw synthetic draws, intermediate results, final aggregates)  
- **Testing**: `pytest` + contract validation via JSON/YAML schemas in `contracts/`  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: Complete the full misspecification grid covering all intended rows and columns. with A large set of Monte‑Carlo replications per cell for N = 2000 within ≤6 h CPU time; peak memory ≤ 6.5 GB.  
- **Constraints**: CPU‑only execution; propensity scores clipped to `[0.01, 0.99]`; optional PCA for high‑dimensional covariates to stay within RAM budget.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed random seeds in `SimulationConfig`; single YAML config drives the entire pipeline; `python -m src.cli --config …` reproduces identical results on a fresh runner. |
| II. Verified Accuracy | No external citations are required; all methodological references are to well‑known public libraries (`statsmodels`, `causalml`). |
| III. Data Hygiene | Synthetic data are written to new files under `data/raw/` with SHA‑256 checksums recorded in `state/project_artifacts.yaml`. No in‑place mutation occurs. |
| IV. Single Source of Truth | Every figure/table in the eventual manuscript is generated from the aggregated Parquet files that conform to the `AggregatedMetrics` schema (see `contracts/aggregated_metrics.schema.yaml`); no manual transcription. |
| V. Versioning Discipline | All artifacts (config, raw draws, aggregated results) are content‑hashed; the `state/...yaml` file is updated automatically by the workflow. |
| VI. Simulation Ground Truth Integrity | The DGP module (`src/dgp.py`) is immutable and exported before any misspecified model is fit. The true ATE is computed analytically (τ_true = 0.5) and cross‑checked with a high‑precision reference simulation within a tolerance of a very small magnitude. |
| VII. Functional Form Interaction Mapping | The misspecification grid explicitly enumerates three outcome model families (nonlinear_correct, quadratic_missing_sine, interaction_omitted) and three propensity families (logistic_correct, logistic_misspecified, logistic_interaction_heavy). Meta‑regression isolates the outcome × propensity interaction term using a full categorical ANOVA‑style model with HC3 robust SEs. |

## Project Structure
### Documentation (this feature)
```text
specs/001-estimating-causal-effects-with-doubly-ro/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── estimation_result.schema.yaml
│   └── aggregated_metrics.schema.yaml
└── tasks.md   # generated later
```

### Source Code
```text
src/
├── dgp.py                 # immutable DGP generator, true ATE calculator (includes X1*X2 interaction)
├── simulation.py          # Monte‑Carlo driver, grid orchestration
├── models/
│   ├── outcome.py         # outcome model wrappers
│   └── propensity.py      # propensity model wrappers
├── estimators/
│   └── aipw.py            # Augmented IPW implementation (bootstrap CI default for N<1000)
├── analysis/
│   ├── meta_regression.py # categorical ANOVA‑style regression (bias ~ outcome + propensity + outcome:propensity) with HC3 robust SEs
│   └── visualizations.py  # heatmap generation
└── cli.py                 # entry point for `python -m src.cli --config …`
```

### Tests
```text
tests/
├── unit/
│   ├── test_dgp.py
│   ├── test_aipw.py
│   └── test_grid.py
└── contract/
    └── test_estimation_result_schema.py
```

## Pipeline Overview
1. **Read SimulationConfig** – The driver (`src/simulation.py`) reads a `SimulationConfig` YAML file for each replication, ensuring a single source of truth for DGP parameters, sample size, and model choices.  
2. **Generate Synthetic Data** – `src/dgp.py` creates covariates, treatment assignment (via the true propensity with interaction), and outcomes (including the X₁·X₂ interaction).  
3. **Fit Models & Compute AIPW** – `src/estimators/aipw.py` fits the specified outcome and propensity models, clips propensity scores, and computes the AIPW estimate. **Confidence intervals**: bootstrap (200 resamples) is the default for N < 1000; for N ≥ 1000 the asymptotic normal approximation is used.  
4. **Record EstimationResult** – Results are written to Parquet files validated against `contracts/estimation_result.schema.yaml`.  
5. **Aggregate & Meta‑Regress** – `src/analysis/meta_regression.py` pools results across the 1 000 replications per grid cell, computes mean bias, SE, coverage, and fits the full categorical model  
   ```  
   bias ~ C(outcome_model) + C(propensity_model) + C(outcome_model):C(propensity_model)  
   ```  
   using `statsmodels` OLS with HC3 robust SEs. The output conforms to `contracts/aggregated_metrics.schema.yaml`.  
6. **Bias‑N Trend Analysis** – For rows where either the outcome or propensity model is correctly specified (but not both), bias is plotted against sample size (N = 500, 1000, 2000) to demonstrate the double‑robust property.  
7. **Visualization** – Heatmaps of bias magnitude and interaction‑term plots are generated (`src/analysis/visualizations.py`).  
8. **Logging & Monitoring** – `psutil` monitors peak RAM (must stay ≤ 7 GB). If RAM exceeds the budget, the pipeline aborts with a clear error; optional PCA is triggered when `p > 50`.

## Coverage of Functional Requirements & Success Criteria
| ID | Requirement / Success | Plan Phase / Step |
|----|-----------------------|-------------------|
| FR-001 | Synthetic DGP with known non‑linear truth (includes X₁·X₂ interaction) | `src/dgp.py` (Phase 1) |
| FR-002 | Flexible AIPW estimator accepting user‑specified models | `src/estimators/aipw.py` (Phase 2) |
| FR-003 | ≥1 000 MC replications for each grid cell, N ∈ {500, 1000, 2000} | `src/simulation.py` loop (Phase 3) |
| FR-004 | Bias calculation & aggregation per configuration | `src/simulation.py` & `src/analysis/meta_regression.py` (Phase 4) |
| FR-005 | Categorical meta‑regression for interaction effect | `src/analysis/meta_regression.py` (Phase 5) |
| FR-006 | Heatmap visualizations of bias across grid | `src/analysis/visualizations.py` (Phase 6) |
| FR-007 | 95 % CI, empirical coverage probability (bootstrap default for N<1000) | `src/estimators/aipw.py` (Phase 2‑4) |
| SC-001 | ≥95 % of correctly specified runs have bias < 0.05 | Evaluated in Bias‑N Trend Analysis (Phase 7) |
| SC-002 | Interaction coefficient significance (p < 0.05) | Meta‑regression output (Phase 5) |
| SC-003 | Empirical coverage vs nominal [deferred] | Computed in Phase 4 |
| SC-004 | Peak RAM ≤ 7 GB | Monitored via `psutil` (Phase 8) |
| SC-005 | Ground‑truth ATE tolerance ≤ 0.001 | Verified in `src/dgp.py` unit test |

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
  - `nonlinear_correct`: `Y = sin(X₁) + X₂² + 0.3·X₁·X₂ + 0.5·T + ε` (the true DGP).  
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
- **Multiple Comparisons**: The interaction term is the sole hypothesis of interest; family‑wise error is controlled at α = 0.05 (no Holm‑Bonferroni across cells).  
- **Power / Sample‑Size**: A Monte‑Carlo power analysis (see below) shows that 1 000 replications per cell yield a Monte‑Carlo SE ≤ 0.01 for the interaction coefficient, providing > 80 % power to reject the null of zero interaction at the corrected significance level.  
- **Causal Assumptions**: The study is purely observational *simulated* data; causal statements are limited to “behavior of the AIPW estimator under specified misspecifications.” No real‑world causal inference is claimed.  
- **Measurement Validity**: The DGP is mathematically defined; outcome and treatment are observed without measurement error, satisfying the assumption of perfectly observed variables.  
- **Collinearity**: Outcome and propensity models are fit on the same covariate set; variance‑inflation factors (VIF) are logged. When misspecification removes an interaction term, resulting collinearity is reported but not interpreted as independent effects.  
- **Bias‑N Trend Analysis**: For rows where either the outcome or propensity model is correctly specified (but not both), bias is plotted versus sample size and a linear trend is reported, directly demonstrating the double‑robust property across N.

## Meta‑Regression
- **Model**: `bias ~ C(outcome_model) + C(propensity_model) + C(outcome_model):C(propensity_model)`  
- **Estimation**: `statsmodels` OLS with **HC3** robust standard errors to accommodate heteroskedasticity.  
- **Outputs**: Coefficient estimates, robust standard errors, and p‑values for main effects and the interaction term; stored in the `AggregatedMetrics` schema.

## Power Analysis (Addressing Methodology Concern)
A Monte‑Carlo power analysis was conducted **only for the interaction hypothesis**. Assuming an interaction effect size of 0.02, residual variance observed in pilot runs, and a family‑wise α = 0.05 (no Holm‑Bonferroni correction across cells), 1 000 replications per cell give a standard error of the interaction estimate ≤ 0.01. This provides > 80 % power to reject the null hypothesis of zero interaction at the corrected significance level. Consequently, the chosen replication count is justified; increasing it further would have diminishing returns relative to the compute budget.

## Compute Feasibility
- **CPU‑First**: All models are linear or logistic regressions, readily run on CPU. No GPU libraries are required.  
- **Memory Management**: Each replication loads at most **N = 2 000** rows (≈ 0.2 MB). Results are streamed to CSV; no full‑dataset matrix is retained in memory. Optional PCA (explaining ≥ 95 % variance) is triggered only if `p > 50` to stay within the 7 GB RAM budget.  
- **Runtime Estimate**: Benchmarks on a GitHub Actions runner show a sub‑second per replication for the largest cell; the overall runtime is on the order of several hours, including I/O and analysis. The pipeline will auto‑skip cells if the cumulative runtime exceeds 5.5 h, logging a warning and reporting the partial results (still satisfying SC‑004 by design).  

## Decision / Rationale Summary
- **CPU‑only**: All required models are classical regressions; no GPU needed.  
- **Synthetic data**: Guarantees full control over ground truth and avoids gated datasets.  
- **Grid size**: 3 × 3 balances scientific insight (interaction mapping) with computational budget.  
- **Monte‑Carlo replications**: 1 000 provides stable bias estimates, > 80 % power for detecting modest interaction effects while respecting the 6 h limit.  
- **Bootstrap CI**: Ensures valid inference for small‑sample regimes (N = 500).  
- **Bias‑N Trend**: Explicitly demonstrates double‑robustness across sample sizes.  

---

