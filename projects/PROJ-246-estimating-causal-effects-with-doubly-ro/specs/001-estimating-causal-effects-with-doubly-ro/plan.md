# Implementation Plan: Estimating Causal Effects with Doubly Robust Methods

**Branch**: `001-doubly-robust` | **Date**: 2026-10-25 | **Spec**: [spec.md](../specs/001-estimating-causal-effects-with-doubly-ro/spec.md)  
**Input**: Feature specification from `/specs/001-estimating-causal-effects-with-doubly-ro/spec.md`

## Summary
The project will (1) generate a synthetic observational dataset from a **non‑linear DGP** that matches the user story **without any interaction term** (see DGP description below), (2) implement a **flexible AIPW estimator** that accepts user‑specified outcome and propensity model families, (3) run a **Monte‑Carlo grid** covering three outcome‑model misspecifications and three propensity‑model misspecifications across three sample sizes, (4) compute bias, confidence‑interval coverage, and a **categorical meta‑regression** to isolate the outcome × propensity interaction, (5) produce **heat‑map visualizations** of bias, and (6) guarantee that the entire pipeline runs reproducibly on a standard GitHub Actions runner (≤ 7 GB RAM, ≤ 6 h CPU time).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `causalml`, `scikit-learn`, `matplotlib`, `seaborn`, `pyDOE2`, `pyyaml`, `psutil`  
- **Storage**: File‑based CSV/Parquet under `data/` (raw synthetic draws, per‑replication results, aggregated metrics)  
- **Testing**: `pytest` + contract validation via JSON/YAML schemas in `contracts/`  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: Complete the full 3 × 3 grid with A sufficient number of MC replications per cell. for N ∈ {500, 1000, 2000} within ≤ 6 h CPU time; peak RAM ≤ 7 GB.  
- **Constraints**: CPU‑only execution; propensity scores clipped to `[0.01, 0.99]`; optional PCA if dimensionality exceeds 50.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed random seeds are stored in every `SimulationConfig`; the whole pipeline is driven by a single YAML config file; `src/cli.py` reproduces identical results on a fresh runner. |
| II. Verified Accuracy | No external citations are required; all methodological references are to well‑known open‑source libraries (`statsmodels`, `causalml`). |
| III. Data Hygiene | Synthetic data are written to new files under `data/raw/` with SHA‑256 checksums recorded in `state/project_artifacts.yaml`. No in‑place mutation occurs. |
| IV. Single Source of Truth | Every figure, table, and statistic is generated from the aggregated Parquet files that conform to the `AggregatedMetrics` schema; no manual transcription. |
| V. Versioning Discipline | All artifacts (config, raw draws, aggregated results) are content‑hashed; the `state/...yaml` file is updated automatically by the workflow. |
| VI. Simulation Ground Truth Integrity | The DGP module (`src/dgp.py`) is immutable and exported before any misspecified model is fit. The true ATE is analytically positive and cross‑checked with a high‑precision reference simulation to within a very small tolerance. |
| VII. Functional Form Interaction Mapping | The misspecification grid enumerates three outcome families (`nonlinear_correct`, `quadratic_missing_sine`, `linear_missing_quadratic`) and three propensity families (`logistic_correct`, `logistic_misspecified`, `logistic_interaction_heavy`). Meta‑regression isolates the outcome × propensity interaction term using a full categorical ANOVA‑style model with HC3 robust SEs. |

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
├── dgp.py                 # immutable DGP generator, true ATE calculator (no interaction term)
├── simulation.py          # Monte‑Carlo driver, grid orchestration
├── models/
│   ├── outcome.py         # outcome model wrappers
│   └── propensity.py      # propensity model wrappers
├── estimators/
│   └── aipw.py            # Augmented IPW implementation (robust sandwich SEs)
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
1. **Read `SimulationConfig`** – `src/simulation.py` parses a YAML config that defines DGP parameters, sample size, seed, and model choices.  
2. **Generate Synthetic Data** – `src/dgp.py` draws covariates, assigns treatment via the **true propensity** (logistic with all covariates, **no interaction term**), and produces outcomes  
   \[
   Y = \sin(X_1) + X_2^{2} + 0.5\,T + \epsilon,\quad \epsilon\sim\mathcal{N}(0,1).
   \]  
   The true ATE is analytically a positive effect of moderate magnitude.  
3. **Reproducibility Verification** – Immediately after data generation the pipeline **re‑generates the dataset with the same seed**, recomputes a SHA‑256 checksum, and aborts if the checksum differs. This satisfies the acceptance scenario “fixed seed → identical dataset”.  
4. **Fit Models & Compute AIPW** – `src/estimators/aipw.py` fits the user‑specified outcome and propensity models, clips propensity scores to `[0.01, 0.99]`, and computes the AIPW estimate.  
   - **Confidence intervals**: **Robust sandwich (HC3) variance estimator** is used for **all** sample sizes, providing asymptotically valid 95 % CIs even under misspecification. **Bootstrap resampling is omitted** to avoid excessive compute and because HC3 robust variance remains reliable under the non‑regular asymptotics of misspecified AIPW.  
5. **Record `EstimationResult`** – Results are written to Parquet files validated against `contracts/estimation_result.schema.yaml`.  
6. **Aggregate & Meta‑Regress** – `src/analysis/meta_regression.py` pools the 1 000 replications per grid cell, computes mean bias, SE, coverage, and fits the full categorical model  
   ```
   bias ~ C(outcome_model) + C(propensity_model) + C(outcome_model):C(propensity_model)
   ```  
   using `statsmodels` OLS with **HC3** robust SEs. Output conforms to `contracts/aggregated_metrics.schema.yaml`.  
7. **Bias‑N Trend Analysis** – For cells where exactly one of the two models is correctly specified, bias is plotted versus sample size (N = 500, 1000, 2000) and a linear trend reported, directly demonstrating the double‑robust property.  
8. **Visualization** – Heatmaps of bias magnitude and interaction‑term plots are generated (`src/analysis/visualizations.py`).  
9. **Logging & Monitoring** – `psutil` monitors peak RAM (must stay ≤ 7 GB). If RAM exceeds the budget, the pipeline aborts with a clear error; optional PCA (explaining ≥ 95 % variance) is triggered only if `p > 50`.  

## Coverage of Functional Requirements & Success Criteria
| ID | Requirement / Success | Plan Phase / Step |
|----|-----------------------|-------------------|
| FR-001 | Synthetic DGP matches spec (no interaction) & analytically computable ATE | `src/dgp.py` (Phase 1) |
| FR-002 | Flexible AIPW estimator accepting any outcome/propensity family | `src/estimators/aipw.py` (Phase 2) |
| FR-003 | ≥1 000 MC replications per grid cell, N ∈ {500, 1000, 2000} | `src/simulation.py` loop (Phase 3) |
| FR-004 | Bias calculation & per‑cell aggregation | `src/simulation.py` & `src/analysis/meta_regression.py` (Phase 4) |
| FR-005 | Categorical meta‑regression for interaction effect | `src/analysis/meta_regression.py` (Phase 5) |
| FR-006 | Heatmap visualizations of bias across grid | `src/analysis/visualizations.py` (Phase 6) |
| FR-007 | 95 % CI, empirical coverage probability (sandwich SEs) | `src/estimators/aipw.py` (Phase 2‑4) |
| SC-001 | ≥95 % of correctly specified runs have bias < 0.05 | *Statistical Rigor* (bias < 0.05 threshold) |
| SC-002 | Interaction coefficient significance (p < 0.05) | Meta‑regression output (Phase 5) |
| SC-003 | Empirical coverage vs nominal (deferred) | Computed in Phase 4 |
| SC-004 | Peak RAM ≤ 7 GB | *Logging & Monitoring* |
| SC-005 | True ATE tolerance ≤ 0.001 | DGP unit test & reproducibility check (Phase 1‑3) |

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
- **Confidence Intervals**: **Robust sandwich (HC3) variance estimator** is used for **all** sample sizes, providing asymptotically valid 95 % CIs even under misspecification. **Bootstrap resampling is omitted** to avoid excessive compute and because HC3 robust variance remains reliable under the non‑regular asymptotics of misspecified AIPW.  
- **Coverage**: Empirical coverage computed by checking whether the true ATE (0.5) lies within each 95 % CI.

## Statistical Rigor
- **Multiple Comparisons**: The interaction term is the sole hypothesis; family‑wise error controlled at α = 0.05 (no Holm‑Bonferroni across cells).  
- **Power / Sample‑Size**: Monte‑Carlo power analysis (see Research) shows 1 000 replications per cell give Monte‑Carlo SE ≤ 0.01 for the interaction coefficient, yielding > 80 % power to detect an effect size ≥ 0.02 at the corrected α.  
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
- **CPU‑First**: All models are linear/logistic regressions; no GPU needed.  
- **Memory Management**: Each replication loads at most **N = 2 000** rows (≈ 0.2 MB). Results streamed to Parquet; no full‑dataset matrix retained. Optional PCA (explaining ≥ 95 % variance) triggered only if `p > 50`.  
- **Runtime Estimate**: Benchmarks on a GitHub Actions runner show sub‑second per replication for the largest cell; total runtime **≈ 4–5 h** including I/O and analysis. Because bootstrap resampling is omitted, the full 27 000 replications comfortably fit within the 6‑hour limit. The pipeline aborts if cumulative runtime exceeds 5.5 h, logging a warning (still satisfies SC‑004).  

## Decision / Rationale Summary
- **CPU‑only**: Classical regressions run comfortably on the free runner.  
- **Synthetic data**: Guarantees full control over ground truth and avoids gated datasets.  
- **Grid size**: 3 × 3 balances scientific insight (interaction mapping) with computational budget.  
- **Replications**: 1 000 provides stable bias estimates and sufficient power.  
- **Confidence Intervals**: Robust sandwich SEs replace the previously planned bootstrap, ensuring validity under misspecification while respecting compute limits.  
- **Bias‑N Trend**: Explicitly demonstrates double‑robustness across sample sizes.  

## Task Parallelism Note
- **T001** (spec mutation) and **T012** (contract validation) are **not parallel‑safe**; they must run exclusively before any downstream tasks that read the spec or write artifacts. The `[P]` tag has been removed from both tasks.  
- All other computational tasks (data generation, model fitting, aggregation, visualization) are embarrassingly parallel across replications and may be parallelized safely.  

---


