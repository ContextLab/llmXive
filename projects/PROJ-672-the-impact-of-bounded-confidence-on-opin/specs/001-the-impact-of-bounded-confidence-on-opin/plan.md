# Implementation Plan: The Impact of Bounded Confidence on Opinion Polarization Speed

**Branch**: `001-gene-regulation` | **Date**: 2026-07-13 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `specs/001-gene-regulation/spec.md`

## Summary

This feature implements a computational study to determine how network topology (Erdős-Rényi, Barabási-Albert, Watts-Strogatz) affects the scaling exponent $\gamma$ of convergence time in the discrete-time Hegselmann-Krause (HK) bounded confidence model. The system will generate $N=500$ synthetic networks, run multiple simulations (a set of topologies × multiple $\epsilon$ values × 50 seeds), fit power-law models to convergence times near the critical threshold $\epsilon_c$, and perform regression analyses to correlate $\gamma$ with structural metrics (assortativity, path length).

**Critical Methodological Clarifications**:
1.  **$\epsilon_c$ Detection Algorithm**: We will not assume $\epsilon_c$ is known. The plan implements a **grid-search algorithm**: for each of the network instances (distributed across multiple topologies), we will test candidate $\epsilon_c$ values in the range $[, ]$ in steps of 0.01. For each candidate, we fit the power-law model $T = A(\epsilon - \epsilon_c)^{-\gamma}$ to the convergence times for $\epsilon \in [\epsilon_c + \delta, 0.50]$, where $\delta$ represents a small positive offset above the critical threshold. The $\epsilon_c$ that minimizes the Residual Sum of Squares (RSS) is selected as the estimate for that specific network instance. This ensures the power-law fit is well-defined and reproducible.
2.  **Unit of Analysis**: To enable regression with sufficient statistical power, we perform **multiple independent power-law fits per topology type** (one for each of the 50 network instances). This yields a set of distinct $\gamma$ estimates (one per network instance), which serve as the dependent variable in the regression against structural metrics. We do *not* aggregate across networks before fitting.
3.  **Regression Strategy & Multicollinearity**: Recognizing that structural metrics (Assortativity, PathLength) are deterministic functions of the Topology generation algorithm, we cannot include Topology and these metrics in the same regression model without severe multicollinearity. The plan executes two distinct models:
    *   **Model A (Topology Effect)**: Regress $\gamma \sim \text{Topology}$ (Categorical). Tests if the *type* of network matters.
    *   **Model B (Structural Effect)**: Regress $\gamma \sim \text{Assortativity} + \text{PathLength}$ *within* each topology group. Tests if *variations* in structure *within* a topology affect $\gamma$.
    *   We explicitly acknowledge that Topology determines the distribution of metrics, and Model B isolates the effect of structural variance *conditional* on topology type.
4.  **Static vs. Adaptive**: Per FR-002, this plan implements the **static** discrete-time HK rule. The "adaptive" variant suggested by reviewers (e.g., T033) is excluded from the current execution scope to maintain spec fidelity. Adaptive variants are noted as Future Work.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph generation/metrics), `numpy` (numerical ops), `scipy` (curve fitting, optimization), `pandas` (data handling), `pytest` (testing), `matplotlib` (plotting), `statsmodels` (regression with robust standard errors).  
**Storage**: Local CSV/Parquet files under `data/` (checksummed); no external database.  
**Testing**: `pytest` with unit tests for HK update logic and integration tests for full simulation batches.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7 GB RAM, no GPU).  
**Project Type**: Computational research / CLI tool.  
**Performance Goals**: Complete 1,500 simulations + analysis within 5 hours; RAM usage < 7 GB.  
**Constraints**: No GPU; strict memory limits; deterministic reproducibility via pinned seeds.  
**Scale/Scope**: Several topologies, $\epsilon$ values, A fixed number of seeds, $N=500$ nodes.

**Reproducibility Enforcement**:
To enforce Constitution Principle I (Reproducibility), the test suite uses `pytest` with a `conftest.py` file that defines a global `seed` fixture. This fixture is injected into all test functions and simulation scripts. Additionally, `pytest.ini` is configured to fail any test run if a random seed is not explicitly set or if non-deterministic operations are detected. This ensures that every test and simulation run is reproducible by re-running the project's `code/` against the project's `data/` on a fresh GitHub Actions runner.

## Constitution Check

**Status**: PASS (with explicit alignment notes)

-   **I. Reproducibility**: The plan mandates pinned random seeds for network generation and simulation initialization. All code runs from `code/` against `data/` on a fresh runner. **Mechanism**: A `conftest.py` file in `tests/` and `pytest.ini` configuration will enforce seed pinning in all pytest fixtures and test runs.
-   **II. Verified Accuracy**: Citations to Hegselmann & Krause and Deffuant et al. will be validated against primary sources. The scaling law hypothesis is grounded in established opinion dynamics literature.
-   **III. Data Hygiene**: Raw simulation outputs (CSV) will be checksummed. Derived metrics (regression coefficients) will be generated from these raw files, not hand-entered.
-   **IV. Single Source of Truth**: All figures in the final paper will be generated by `code/` scripts reading from `data/`.
-   **V. Versioning**: **Mechanism**: A post-processing script `code/utils/update_state.py` is configured to run automatically as a pre-commit hook and a CI step. Upon any modification to `plan.md` or other research artifacts, this script computes the SHA-256 hash of the changed files and updates the project's `state.yaml` file's `updated_at` timestamp and `artifact_hashes` map. This ensures the state file reflects the exact content of the research-stage artifacts *before* the next stage begins.
-   **VI. Topological Robustness Validation**: The plan explicitly requires comparative analysis across Scale-Free (BA) and Small-World (WS) topologies to test the universality of $\gamma$, directly addressing this principle.
-   **VII. Emergent Property Isolation**: The implementation separates `NetworkInstance` generation from `SimulationRun` execution. Convergence time is recorded as an outcome of the dynamic interaction, not a pre-calculated function of static metrics.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── generate_networks.py       # FR-001: Network generation
│   ├── simulate_hk.py             # FR-002, FR-003, FR-004: HK simulation
│   ├── analyze_scaling.py         # FR-005, FR-006: Power-law fit & regression
│   ├── run_sensitivity.py         # FR-008: Sensitivity analysis
│   ├── utils/
│   │   ├── metrics.py             # Structural metric calculators
│   │   ├── convergence.py         # Convergence logic
│   │   └── update_state.py        # Constitution V: State file updater
│   └── tests/
│       ├── conftest.py            # Seed pinning enforcement
│       ├── pytest.ini             # Test configuration
│       ├── unit/
│       │   ├── test_hk_update.py
│       │   └── test_network_gen.py
│       └── integration/
│           └── test_full_pipeline.py
├── data/
│   ├── raw/                       # Raw simulation outputs (checksummed)
│   └── processed/                 # Aggregated metrics, regression data
└── outputs/
    └── figures/                   # Generated plots
```

**Structure Decision**: A monolithic `code/` directory with modular scripts for each phase (Generation, Simulation, Analysis). This minimizes overhead on the CI runner and ensures a linear execution flow: `generate` -> `simulate` -> `analyze`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The current scope (3 topologies, 10 $\epsilon$, 50 seeds) fits within the available RAM and time limits without complex parallelization strategies. | A distributed cluster approach is unnecessary and would add complexity to the CI setup. |