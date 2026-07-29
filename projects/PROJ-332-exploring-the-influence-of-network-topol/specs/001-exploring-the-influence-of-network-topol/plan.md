# Implementation Plan: Influence of Network Topology on Thermal Conductivity in Nanomaterials

**Branch**: `001-network-topology-thermal` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-network-topology-thermal/spec.md`

## Summary

This feature implements a computational pipeline to investigate how the connectivity distribution of randomly assembled nanowire networks modulates effective thermal conductivity. The system generates Random Geometric Graphs (RGGs) with controlled average degrees, assigns thermal resistances based on the Fuchs-Sondheimer model (incorporating size effects and junction resistance), solves Kirchhoff's heat-flow equations, and performs a **two-stage statistical analysis** to extract scaling exponents near the percolation threshold while correcting for selection bias. The implementation adheres to strict reproducibility, numerical stability (double precision, convergence checks), and CI feasibility constraints (CPU-only, <6h runtime).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `scipy`, `networkx`, `pandas`, `matplotlib`, `pytest`, `scikit-learn`, `statsmodels`
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`)
**Testing**: `pytest` (unit, integration, contract tests)
**Target Platform**: Linux (GitHub Actions CPU runner: 2 vCPU, 7GB RAM)
**Project Type**: Scientific CLI / Simulation Library
**Performance Goals**: Complete 1000 simulations (10 levels x 100 runs) within 6 hours; solver convergence < 1s per graph.
**Constraints**: No GPU; memory < 7GB; strict timeout enforcement; double-precision arithmetic only.
**Scale/Scope**: N=1000 nodes per graph; connectivity levels; runs per level; sensitivity sweeps.

> **Note on Compute Feasibility**: The entire pipeline is CPU-tractable. Graph generation and resistor network solving for N=1000 using `scipy.sparse` linear solvers are efficient on 2 cores. No GPU offload is required or permitted for this simulation-based study.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | All random seeds pinned in `code/simulate.py`; `requirements.txt` pins versions; `data/` checksummed. |
| **II. Verified Accuracy** | ✅ PASS | No external dataset URLs required; material constants hardcoded per NIST (FR-010) with source citation in code. |
| **III. Data Hygiene** | ✅ PASS | Raw data (generated graphs) immutable; processed results written to new CSVs; PII scan N/A (synthetic data). |
| **IV. Single Source of Truth** | ✅ PASS | All statistics (exponents, p-values) derived directly from `data/processed/simulation_results.csv` via `code/analysis.py`. |
| **V. Versioning Discipline** | ✅ PASS | Content hashes tracked in state file; artifact invalidation logic in CI. |
| **VI. Numerical Stability** | ✅ PASS | `scipy.sparse.linalg.spsolve` used with `tol=1e-6`; convergence check implemented; double precision enforced. |
| **VII. Physical Units** | ✅ PASS | All inputs converted to SI (W/m·K, m); outputs in SI; constants validated against NIST. |

## Project Structure

### Documentation (this feature)

```text
specs/001-network-topology-thermal/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code

```text
code/
├── __init__.py
├── cli.py               # Entry point, argument parsing (FR-016)
├── config.py            # Constants, NIST defaults, thresholds
├── generate.py          # RGG generation, topology metrics (FR-001, FR-004, FR-014)
├── physics.py           # Resistance calculation, Fuchs-Sondheimer, Kirchhoff solver (FR-002, FR-003, FR-011, FR-012, FR-013)
├── analysis.py          # Regression, sensitivity, percolation threshold (FR-005, FR-006, FR-007, FR-017, FR-018)
├── utils.py             # Logging, CSV handling, watchdog (FR-009, FR-015)
└── main.py              # Orchestration loop
tests/
├── unit/
│   ├── test_generate.py
│   ├── test_physics.py
│   └── test_analysis.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py
requirements.txt
```

**Structure Decision**: Single `code/` directory with modular separation of concerns (Generation, Physics, Analysis) to facilitate unit testing and maintainability. No separate frontend/backend required for a CLI simulation tool.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Fuchs-Sondheimer Model** | Required by FR-002/FR-011 for nanoscale validity (d < 100nm). | Simple bulk conductivity would violate physical assumptions for nanowires. |
| **Sparse Linear Solver** | Required for N=1000 graphs to meet 6h runtime. | Dense matrix inversion (N x N) would exceed memory/time limits. |
| **Dynamic Sample Size** | Required by FR-018 for variance estimation. | Fixed sample size risks low power at critical threshold. |
| **Two-Part Statistical Model** | Required to correct selection bias from disconnected graphs (Scientific Soundness concern). | Simple exclusion of disconnected graphs biases the exponent $t$ and shifts $k_c$. |
| **Isotropic Averaging** | Required to mitigate directional bias in RGGs (Methodology concern). | Single X-axis boundary conditions introduce systematic bias in $k_{eff}$. |
| **Two-Stage Threshold Estimation** | Required to avoid circular validation (Scientific Soundness concern). | Simultaneous fitting of $k_c$ and $t$ introduces severe overfitting. |

## FR/SC Mapping

| Requirement | Plan Phase/Step |
| :--- | :--- |
| **FR-001** (RGG Gen) | `generate.py`: `create_rgg(N, p, seed)` |
| **FR-002** (Resistance) | `physics.py`: `calc_resistance(d, l, k_bulk, p_factor)` |
| **FR-003** (Solver) | `physics.py`: `solve_kirchhoff(G, source, sink)` |
| **FR-004** (Metrics) | `generate.py`: `compute_metrics(G)` |
| **FR-005** (Regression) | `analysis.py`: `fit_power_law(results, k_c_fixed)` (Two-step: fix $k_c$ then fit) |
| **FR-006** (Correlation) | `analysis.py`: `compute_correlation_matrix(results)` |
| **FR-007** (Sensitivity) | `analysis.py`: `run_sensitivity_sweep(results)` (General scaling factor) |
| **FR-008** (Runtime) | `utils.py`: `Watchdog` class; CI timeout config |
| **FR-009** (Logging) | `utils.py`: `save_results_csv()` (Includes `connectivity_probability`, `percolation_threshold`) |
| **FR-010** (NIST) | `config.py`: `MATERIAL_CONSTANTS` dict |
| **FR-011** (Size Effect) | `physics.py`: `fuchs_sondheimer_correction()` |
| **FR-012** (Junction) | `physics.py`: `add_junction_resistance()`; **Sensitivity**: `analysis.py` separate sweep for $R_{junction}$ $\pm 10\%$ |
| **FR-013** (Source/Sink) | `generate.py`: `select_boundary_nodes()` (-directional averaging: X, Y, Diag1, Diag2) |
| **FR-014** (Domain) | `config.py`: `DOMAIN_SIZE = 10.0` (µm) |
| **FR-015** (Watchdog) | `utils.py`: `Watchdog` integration |
| **FR-016** (CLI) | `cli.py`: `--material-override` arg |
| **FR-017** (Percolation) | `analysis.py`: `estimate_percolation_threshold()` (Sigmoid fit on $P_{\infty}$) |
| **FR-018** (Pilot) | `analysis.py`: `dynamic_sample_adjustment()` (N=10 pilot -> variance check -> power calc -> double N if power < 0.8) |
| **FR-019** (Log Degree) | `utils.py`: CSV column `avg_degree` |
| **SC-001** (Degree Tolerance) | `tests/unit/test_generate.py`: assert range |
| **SC-002** (Solver Convergence) | `tests/unit/test_physics.py`: assert residual |
| **SC-003** (Scaling Exponent) | `tests/integration/test_pipeline.py`: verify regression output **and** deviation from theoretical $t=1.3$ (report $|t_{fitted} - 1.3|$ and p-value for $H_0: t=1.3$) |
| **SC-004** (Sensitivity Range) | `tests/integration/test_pipeline.py`: verify range |
| **SC-005** (6h Runtime) | CI Workflow: `timeout-minutes:` |
| **SC-006** (Variance Report) | `analysis.py`: log variance adjustment decision |

**Spec Note on FR-012**: The source spec text for FR-012 is malformed ("...as established in prior studies (). This research question... (default)."). The plan assumes a default junction resistance of $10^{-9}$ K/W based on standard high-performance thermal interface literature and implements the sensitivity sweep over $\pm 10\%$ of this value. This discrepancy is flagged for a future spec amendment (kickback).

## Constitution Check (Detailed)

*   **Reproducibility**: All seeds logged.
*   **Verified Accuracy**: NIST values cited.
*   **Data Hygiene**: Checksums.
*   **Single Source of Truth**: CSV -> Analysis.
*   **Versioning**: Hashes.
*   **Numerical Stability**: `tol=1e-6`.
*   **Physical Units**: SI.

## Statistical Rigor & Methodology

-   **Multiple Comparisons**: Only one primary regression (vs. $\langle k \rangle$) reported. Correlation matrix is descriptive.
-   **Power Analysis**: Formal calculation based on pilot variance. If power < 0.8, N doubles (max 200).
-   **Causal Claims**: None. The study reports associational scaling laws.
-   **Collinearity**: Acknowledged. $\langle k \rangle$, path length, and clustering are inherently correlated. $\langle k \rangle$ is the primary predictor.
-   **Selection Bias Correction**: Disconnected graphs are NOT excluded. A two-part model is used: (1) Logistic regression for $P_{\infty}(\langle k \rangle)$, (2) Power law for $k_{eff}$ (connected). Final $k_{eff}^{adj} = k_{eff} \times P_{\infty}$.
-   **Circular Validation**: $k_c$ is estimated from the *entire* dataset (via $P_{\infty}$ sigmoid) and **fixed** before fitting the power law for $k_{eff}$.
-   **Compute Feasibility**:
    -   **CPU**: All operations CPU-tractable.
    -   **Memory**: Sparse matrices < 1MB.
    -   **Time**: ~1000 graphs * 0.1s/graph = 100s total.
    -   **GPU**: Not required.

## Pilot Study & Dynamic Adjustment (FR-018 Detail)

The pilot study logic is implemented as follows:
1.  **Run**: Execute N=10 simulations at the target connectivity level.
2.  **Variance**: Calculate sample variance $\sigma^2$ of $k_{eff}$.
3. **Power Calc**: Compute required sample size $N_{req} = (Z_{\alpha/2} + Z_{\beta})^2 \sigma^2 / \delta^2$, where $\delta$ is the minimum detectable effect size (defined as [deferred] deviation from theoretical $t=1.3$, i.e., $\delta = 0.13$), $\alpha=0.05$, $\beta=0.2$ (80% power).
4.  **Adjust**: If $N_{req} > 100$, set $N_{final} = \min(200, 2 \times N_{req})$. Else $N_{final} = 100$.
5.  **Log**: Record $N_{req}$, $\sigma^2$, and adjustment decision in the CSV.

## Sensitivity Analysis Detail (FR-007 & FR-012)

Two distinct sensitivity sweeps are performed:
1.  **General Scaling**: Sweep global resistance scaling factor $\alpha \in \{0.9, 1.0, 1.1\}$.
2.  **Junction Resistance**: Sweep $R_{junction}$ by $\pm 10\%$ around the nominal $10^{-9}$ K/W.
Both sweeps report the resulting range of $k_{eff}$ values.

### Theoretical Comparison (SC-003)

The implementation explicitly calculates the deviation $|t_{fitted} - 1.3|$ and reports the p-value for the hypothesis $H_0: t = 1.3$ using bootstrapped standard errors. This comparison is framed as a consistency check for the RGG model in the finite-size regime (N=1000), acknowledging that finite-size effects may cause deviations from the asymptotic $t \approx 1.3$.