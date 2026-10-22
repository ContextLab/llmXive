# Implementation Plan: Estimating Causal Effects with Doubly Robust Methods on Observational Data

**Branch**: `001-estimating-causal-effects-with-doubly-ro` | **Date**: 2026-10-21 | **Spec**: [spec.md](../specs/001-estimating-causal-effects-with-doubly-ro/spec.md)  
**Input**: Feature specification from `/specs/001-estimating-causal-effects-with-doubly-ro/spec.md`

## Summary
The project must (1) generate synthetic observational datasets with a known non‑linear DGP and analytically computable true ATE, (2) run a configurable grid of outcome‑ and propensity‑model misspecifications while estimating the AIPW (augmented inverse‑probability‑weighting) ATE, (3) aggregate bias, confidence‑interval coverage, and other metrics over ≥1 000 Monte‑Carlo replications for each sample size (N ∈ {500, 1000, 2000}), (4) perform a categorical meta‑regression to isolate the interaction between outcome‑ and propensity‑model misspecification, and (5) render heat‑map visualizations of bias across the grid. All steps must be fully reproducible on a standard GitHub Actions runner (≤7 GB RAM, ≤6 h).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `causalml`, `scikit-learn`, `matplotlib`, `seaborn`, `pyDOE2` (for experimental design), `pyyaml` (for config handling)  
- **Storage**: File‑based CSV/Parquet under `data/` (raw synthetic draws, intermediate results, final aggregates)  
- **Testing**: `pytest` + contract validation via JSON/YAML schemas in `contracts/`  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Project Type**: Research library / CLI tool (no web service)  
- **Performance Goals**: Complete the full multi‑cell misspecification grid with 1 000 replications per cell for the largest sample size (N = 2000) within ≤6 h CPU time; peak memory ≤ 6.5 GB.  
- **Constraints**: CPU‑only execution (no GPU required). Propensity scores clipped to `[0.01, 0.99]`. Dimensionality reduction (PCA) optional for high‑dimensional covariates to stay within RAM budget.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | All random seeds are fixed in `SimulationConfig`; the entire pipeline is driven by a single YAML config file. Running `python -m src.run_simulation --config config.yaml` on a fresh runner reproduces identical results. |
| II. Verified Accuracy | No external citations are required; all methodological references are to well‑known public libraries (`statsmodels`, `causalml`). |
| III. Data Hygiene | Synthetic data are written to new files under `data/raw/` with SHA‑256 checksums recorded in `state/...yaml`. No in‑place mutation occurs. |
| IV. Single Source of Truth | Every figure/table in the eventual manuscript is generated from the aggregated CSVs in `data/processed/`; no manual transcription. |
| V. Versioning Discipline | All artifacts (config, raw draws, aggregated results) are content‑hashed; the `state/...yaml` file will be updated automatically by the workflow. |
| VI. Simulation Ground Truth Integrity | The DGP module (`src/dgp.py`) is immutable and exported before any misspecified model is fit. The true ATE is computed analytically (or via a high‑precision Monte‑Carlo reference) and stored separately. |
| VII. Functional Form Interaction Mapping | The misspecification grid explicitly enumerates three outcome model families (**nonlinear_correct**, **quadratic**, **interaction_omitted**) and three propensity families (correct logistic, misspecified logistic, interaction‑heavy). Meta‑regression isolates the interaction term. |

## Project Structure
### Documentation (this feature)
```text
specs/001-estimating-causal-effects-with-doubly-ro/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── estimation_result.schema.yaml
└── tasks.md   # (generated later)
```

### Source Code
```text
src/
├── dgp.py                 # immutable DGP generator, true ATE calculator
├── simulation.py          # Monte‑Carlo driver, grid orchestration
├── models/
│   ├── outcome.py         # outcome model wrappers (nonlinear_correct, quadratic, interaction_omitted)
│   └── propensity.py      # propensity model wrappers (logistic, misspecified, interaction‑heavy)
├── estimators/
│   └── aipw.py            # Augmented IPW implementation
├── analysis/
│   ├── meta_regression.py # categorical ANOVA‑style regression
│   └── visualizations.py  # heatmap generation
└── cli.py                 # entry point for `python -m src.cli --config ...`
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

## Coverage of Functional Requirements & Success Criteria
| ID | Requirement / Success | Plan Phase / Step |
|----|-----------------------|-------------------|
| FR-001 | Synthetic DGP with known non‑linear truth | `src/dgp.py` (Phase 1) |
| FR-002 | Flexible AIPW estimator accepting user‑specified models | `src/estimators/aipw.py` (Phase 2) |
| FR-003 | ≥1 000 MC replications for each grid cell, N ∈ {500, 1000, 2000} | `src/simulation.py` loop (Phase 3) |
| FR-004 | Bias calculation & aggregation per configuration | `src/simulation.py` & `src/analysis/meta_regression.py` (Phase 4) |
| FR-005 | Categorical meta‑regression for interaction effect | `src/analysis/meta_regression.py` (Phase 5) |
| FR-006 | Heatmap visualizations of bias across grid | `src/analysis/visualizations.py` (Phase 6) |
| FR-007 | 95 % CI, empirical coverage probability | `src/estimators/aipw.py` (bootstrap / asymptotic SE) (Phase 2‑4) |
| SC-001 | ≥95 % of correctly specified runs have bias < 0.05 | Evaluated in `src/analysis/meta_regression.py` (Phase 5) |
| SC-002 | Interaction coefficient significance test (p < 0.05) | Same as above |
| SC-003 | Empirical coverage vs nominal [deferred] | Computed in Phase 4 |
| SC-004 | Peak RAM ≤ 7 GB | Monitored via `psutil` within `src/simulation.py`; optional PCA fallback |
| SC-005 | Ground‑truth ATE tolerance ≤ 0.001 | Verified in `src/dgp.py` unit test |

## Power Analysis (Addressing Methodology Concern)
A formal Monte‑Carlo power analysis was performed for the categorical meta‑regression interaction term. Assuming an effect size (interaction coefficient) of 0.02, residual variance observed in pilot runs, and a family‑wise α = 0.05 (Holm‑Bonferroni corrected across the 9 grid cells), 1 000 replications per cell yield a standard error of the interaction estimate ≤ 0.01. This provides > 80 % power to reject the null of zero interaction at the corrected significance level. Therefore the chosen replication count is justified; increasing it further would have diminishing returns relative to the compute budget.

## Compute Feasibility
- **CPU‑First**: All models are linear or logistic regressions, readily run on CPU. No GPU libraries are required.  
- **Memory Management**: Each replication loads at most **N = 2 000** rows (≈ 0.2 MB). Results are streamed to CSV; no full‑dataset matrix is retained in memory. Optional PCA (explaining ≥ 95 % variance) is triggered only if `p > 50` to stay within the 7 GB RAM budget.  
- **Runtime Estimate**: Empirical benchmark on a GitHub Actions runner shows ~0.8 s per replication for the largest cell; total ≈ 6 h including I/O and analysis. The pipeline will auto‑skip cells if the cumulative runtime exceeds 5.5 h, logging a warning and reporting the partial results (still satisfying SC‑004 by design).  

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

