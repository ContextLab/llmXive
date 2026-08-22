# Implementation Plan: Investigating the Impact of Network Structure on Energy Dissipation in Driven Oscillators

**Branch**: `001-investigate-network-dissipation` | **Date**: 2026-08-05 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-investigate-network-dissipation/spec.md`

## Summary

This project implements a computational physics study to correlate static network topology metrics with dynamic energy dissipation rates in driven damped harmonic oscillator networks. The approach involves three phases: (1) generating synthetic topologies (Random, Scale-Free, Small-World, Lattice, Star) and computing structural metrics; (2) numerically integrating coupled oscillator equations of motion to extract energy decay rates; and (3) performing **Partial Least Squares (PLS) Regression** with multiple-comparison corrections, sensitivity analysis, and **null model validation**. The entire pipeline is designed to run within the constraints of a GitHub Actions free-tier runner (limited CPU, constrained RAM, 6h limit). using `scipy`, `networkx`, and `sklearn`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph generation), `scipy` (ODE integration, stats), `numpy` (numerical ops), `pandas` (data handling), `matplotlib` (plotting), `scikit-learn` (PLS regression, PCA), `statsmodels` (regression diagnostics).  
**Storage**: Local CSV/JSON files in `data/` (checksummed per Constitution Principle III).  
**Testing**: `pytest` (unit tests for generation, integration checks, regression validation).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`).  
**Project Type**: Computational simulation / Data analysis pipeline.  
**Performance Goals**: Complete 50+ simulations + analysis in ≤ 6 hours; RAM ≤ 7 GB.  
**Constraints**: CPU-only execution; no external data downloads (synthetic data only); strict reproducibility (random seeds).  
**Scale/Scope**: 50 network realizations (N=100-200 nodes); topological classes; + seeds for convergence testing.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan mandates pinned random seeds in `code/` and reproducible `requirements.txt`. All external libraries are pinned. Random seeds ensure that the "random" topology generation process is fully deterministic and reproducible.
- **Principle II (Verified Accuracy)**: While no external citations are required for synthetic data generation or numerical integration methods (all methods are standard), the plan ensures internal accuracy by validating the solver against analytical Laplacian eigenvalues for coupled modes (see Numerical Stability).
- **Principle III (Data Hygiene)**: Plan includes checksumming of generated `data/` files and immutable derivation steps (raw generation → simulation → analysis).
- **Principle IV (Single Source of Truth)**: All figures and statistics in the final output will trace back to specific rows in `data/` and code blocks in `code/`.
- **Principle V (Versioning Discipline)**: Implementation will use content hashes for artifacts; `state/` files will be updated on change.
- **Principle VI (Numerical Stability)**: Plan explicitly includes convergence testing (FR-008) across 10+ seeds and validation of `solve_ivp` stability against analytical Laplacian eigenvalues before recording results.
- **Principle VII (Topological Metric Isolation)**: Plan enforces fixed node count (N=100-200) while varying only topology class to isolate structural effects (FR-001). The randomization protocol for topology generation (fixed seeds, randomized edge parameters) ensures exchangeability within the simulation model.

## Project Structure

### Documentation (this feature)

```text
specs/001-investigate-network-dissipation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-440-investigating-the-impact-of-network-stru/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── generate_networks.py       # FR-001: Topology generation & metrics
│   ├── simulate_oscillators.py    # FR-002, FR-003: ODE integration & decay extraction
│   ├── analyze_regression.py      # FR-004, FR-005, FR-006: PLS & sensitivity & null model
│   └── utils/
│       ├── metrics.py             # Clustering, path length, degree dist
│       └── diagnostics.py         # Convergence plots, VIF checks, Null model
├── data/
│   ├── raw/
│   │   └── networks.csv           # Generated topologies (checksummed)
│   ├── processed/
│   │   └── energy_decay.csv       # Simulation results (checksummed)
│   └── analysis/
│       └── regression_results.json
├── tests/
│   ├── test_generation.py
│   ├── test_simulation.py
│   └── test_regression.py
└── state/
    └── projects/PROJ-440-investigating-the-impact-of-network-stru.yaml
```

**Structure Decision**: Single project structure chosen for simplicity and tight coupling between generation, simulation, and analysis. All scripts are modular but share a common `data/` directory for intermediate artifacts, ensuring the "Single Source of Truth" (Principle IV).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. The scope is strictly bounded by synthetic data and CPU-tractable ODEs. | N/A |

## Phase Breakdown

### Phase 0: Research & Feasibility
- **Goal**: Confirm theoretical bounds for network metrics and ODE stability.
- **Task**: Verify that `scipy.integrate.solve_ivp` with `RK45` or `DOP853` can handle stiff networks (Scale-Free) within 6h.
- **Task**: Confirm that 50 samples provide sufficient power for PLS with A set of predictors. **Assumption**: Minimum Detectable Effect Size (MDES) is set to a medium effect size (f² = 0.15) based on pilot simulations of similar coupled systems. Acknowledgement: Power may be low for small effect sizes; results will be interpreted as exploratory.
- **Output**: `research.md`

### Phase 1: Data Model & Contracts
- **Goal**: Define schemas for generated networks, energy time-series, and regression outputs.
- **Task**: Create `contracts/network_schema.schema.yaml`, `contracts/energy_schema.schema.yaml`, `contracts/regression_schema.schema.yaml`.
- **Task**: Define `quickstart.md` for setting up the environment and running the full pipeline.
- **Output**: `data-model.md`, `quickstart.md`, `contracts/`

### Phase 2: Implementation
- **Goal**: Implement scripts per `plan.md` phases.
- **Task**: Write `generate_networks.py` (FR-001).
- **Task**: Write `simulate_oscillators.py` (FR-002, FR-003).
- **Task**: Write `analyze_regression.py` (FR-004, FR-005, FR-006): Implement PLS regression, Bonferroni correction, sensitivity analysis, VIF checks, and **permutation test (null model)**.
- **Task**: Implement convergence testing (FR-008) and **Laplacian eigenvalue validation**.
- **Output**: Executable code in `code/`

### Phase 3: Validation & Reporting
- **Goal**: Run full pipeline, validate against acceptance criteria, generate figures.
- **Task**: Execute pipeline on GitHub Actions.
- **Task**: Verify R² ≥ 0.95 for decay fits; check VIF < 5; confirm p-value corrections; **verify model outperforms null distribution**.
- **Task**: Generate final report and figures.
- **Output**: Final results in `data/analysis/`

## Statistical Rigor & Methodological Notes

- **Partial Least Squares (PLS) Regression**: Replaced PCR with PLS. PLS maximizes covariance between predictors (topological metrics) and the response (decay rate), allowing for the extraction of **Variable Importance in Projection (VIP)** scores. This directly addresses the research question by identifying which specific structural features drive dissipation while handling collinearity.
- **Multiple Comparisons**: Bonferroni or Holm-Bonferroni correction applied to all p-values in PLS.
- **Sample Size & Power**: A sufficient number of samples (a balanced number of instances per class) is the minimum feasible for regression with 5 predictors. **Limitation**: Power may be low for small effect sizes (Type II errors possible). The study is framed as **exploratory/hypothesis-generating**. Results will emphasize effect sizes and confidence intervals over binary significance.
- **Causal Framing**: Findings will be framed as "associations" (Assumption: Inference Framing) due to synthetic data. However, the **randomization protocol** (fixed seeds, randomized edge parameters) ensures exchangeability *within the simulation model*, allowing for "simulation-causal" claims (valid within the synthetic universe) but not "real-world-causal" claims.
- **Collinearity**: VIF calculation; if VIF > 5, results are reported descriptively without claiming independent effects. PLS inherently handles collinearity, but VIF is still reported for diagnostics.
- **Measurement Validity**: Validity of decay rates depends on numerical stability, verified via:
    1. Convergence plots across seeds (FR-008).
    2. **Laplacian Eigenvalue Validation**: Comparing numerical decay rates against analytical eigenvalues of the Laplacian for a known small graph (e.g., ring) to prove network-dependent dissipation modes are captured correctly.
- **Null Model Validation**: A permutation test (shuffling topology-to-decay mapping repeatedly) will be performed. The observed correlation must exceed the a high percentile of the null distribution to be considered non-trivial, addressing the risk of tautological results.

## Compute Feasibility

- **CPU-First**: All methods (`networkx`, `scipy`, `sklearn`, `statsmodels`) are CPU-tractable.
- **Memory**: Multiple networks × 200 nodes × 200 time steps is well within 7 GB RAM.
- **Time**: A series of simulations, each running for 200 time units, will be conducted to investigate the research question using the established method (Citation). (with `solve_ivp` adaptive steps) estimated at < 2 hours total on 2 cores.
- **GPU Escape Hatch**: Not required; no transformer or diffusion models involved.

## Data Availability

- **Synthetic Data**: No external datasets required. All data generated internally via `networkx` and `scipy`.
- **Reproducibility**: Random seeds pinned in code; `requirements.txt` ensures identical library versions.