# Implementation Plan: Quantifying Uncertainty in Small Sample Regression Models

**Branch**: `001-quantify-uncertainty-small-sample` | **Date**: 2026-06-27 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-quantify-uncertainty-small-sample/spec.md`

## Summary

This project implements a Monte Carlo simulation engine to empirically compare the coverage probabilities of three uncertainty quantification methods (OLS, Non-parametric Bootstrap with BCa intervals, Bayesian Regression with weakly informative priors) under small sample conditions ($N < 50$) with varying degrees of predictor collinearity. The implementation prioritizes CPU-tractability to ensure execution within GitHub Actions free-tier limits (2 CPU, 7GB RAM, 6h), focusing on generating synthetic data with controlled correlation structures and validating findings on a subsampled UCI dataset. A key methodological refinement is the grouping of results by *realized* collinearity metrics rather than target parameters to avoid ecological fallacy.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scipy`, `scikit-learn`, `cmdstanpy` (CPU-optimized Stan backend), `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/simulated`)  
**Testing**: `pytest` (unit tests for simulation logic, coverage checks for pipeline)  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Project Type**: Computational Research / Simulation Library  
**Performance Goals**: Complete 200 Monte Carlo replications with 500 bootstrap samples and 2000 MCMC samples per chain within 6 hours.  
**Constraints**: No GPU; memory usage < 7GB; disk usage < 14GB; strict adherence to $N < 50$; no external API calls during execution (datasets cached locally).  
**Scale/Scope**: A substantial number of simulation runs, multiple methods, 1 real-world validation dataset (subsampled).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/simulation/engine.py`; dependencies pinned in `requirements.txt`; execution isolated in virtualenv. |
| **II. Verified Accuracy** | **Provisional** | The selection of specific priors (Normal(0,10)) and the UCI Concrete dataset are **provisional** pending validation in Phase 0 (Research). Citations will be verified against primary sources before inclusion in `research.md` and `paper/`. |
| **III. Data Hygiene** | **Pass** | Synthetic data generated on-the-fly (checksummed via content hash); UCI dataset downloaded and checksummed; no in-place modifications. |
| **IV. Single Source of Truth** | **Pass** | All figures/statistics in `paper/` will be generated directly from `data/` artifacts via `code/` scripts; no hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Artifact hashes recorded in `state/`; `updated_at` timestamps managed by the Advancement-Evaluator. |
| **VI. Empirical Coverage Validation** | **Pass** | Core metric: `empirical_coverage = (count(covered) / N_replications)`. Validated against nominal level in `code/metrics/coverage.py`. |
| **VII. Small-Sample Regime Integrity** | **Pass** | Simulation config enforces $3 \le N \le 49$; validation dataset subsampled to $N < 50$; collinearity diagnostic (VIF) enforced on *realized* data. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-uncertainty-small-sample/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Pre-defined design artifacts/schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-034-quantifying-uncertainty-in-small-sample-/
├── code/
│   ├── __init__.py
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── engine.py          # Synthetic data generation (FR-001, FR-006)
│   │   └── config.py          # SimulationConfig schema
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ols.py             # OLS implementation (FR-002)
│   │   ├── bootstrap.py       # Non-parametric bootstrap with BCa (FR-002)
│   │   └── bayesian.py        # Bayesian regression with weakly informative priors (FR-003)
│   ├── metrics/
│   │   ├── __init__..py
│   │   └── coverage.py        # Coverage probability calculation (FR-004)
│   ├── validation/
│   │   ├── __init__.py
│   │   └── uci_runner.py      # Real-world validation (FR-005)
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded UCI dataset
│   ├── simulated/             # Generated synthetic datasets (N < 50)
│   └── results/               # Aggregated coverage metrics
├── tests/
│   ├── unit/
│   │   └── test_simulation.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── paper/                 # Draft manuscript (generated from results)
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected to minimize overhead for a computational research project. The `code/` directory is modularized by function (simulation, models, metrics) to align with the distinct user stories (US-1, US-2, US-3). No separate frontend/backend is required as this is a batch-processing research tool. The `contracts/` directory contains pre-defined schema artifacts established in Phase 1 to guide implementation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Bayesian Inference Engine (cmdstanpy)** | Required for FR-003 to compare against Bootstrap/OLS. | Using a heavy GPU-based framework (e.g., PyTorch with full LLMs) is infeasible on the 2-CPU runner; `cmdstanpy` is the standard CPU-tractable choice for small regression models. |
| **Monte Carlo Replications (200)** | Required for SC-004 (statistical power) within 6h limit. | Fewer replications (e.g., 50) would yield high Monte Carlo error (SE ~0.14), failing to detect subtle coverage differences; more replications exceed the 6h runtime. |
| **Collinearity Diagnostic (Realized VIF)** | Required for FR-006 to ensure "high collinearity" condition. | Relying solely on target correlation $\rho$ is insufficient due to random variation in small samples; filtering by *realized* VIF ensures the analysis subset meets the stress condition without selection bias. |
| **BCa Bootstrap Intervals** | Required for methodological rigor in small samples. | Standard percentile intervals are known to have poor coverage properties in small samples ($N < 50$); BCa corrects for bias and skewness. |