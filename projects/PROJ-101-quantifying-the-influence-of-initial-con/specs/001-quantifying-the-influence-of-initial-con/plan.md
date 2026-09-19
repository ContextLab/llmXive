# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-08-05 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary

This project implements a computational physics study to quantify how observational noise biases Finite-Time Lyapunov Exponents (FTLE) in high-dimensional chaotic systems (coupled Lorenz oscillators). The approach involves: (1) generating synthetic time-series data with controlled Gaussian noise using `scipy.integrate.solve_ivp` (DOP853); (2) computing FTLE spectra via QR-decomposition based tangent linear propagation; (3) establishing a numerically converged asymptotic baseline for the clean system using **Rosenstein's algorithm** for validation; and (4) performing regression analysis to model the deviation $\Delta \lambda$ as a function of noise amplitude ($\sigma$) and system dimension ($N$). The implementation targets GitHub Actions free-tier constraints (limited CPU, ~7GB RAM) by streaming data and using vectorized NumPy operations. CPU-first strategy is confirmed feasible; no GPU fallback is planned to ensure strict CI reproducibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `matplotlib`, `pandas`, `pytest`, `pyyaml`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`), no external DB  
**Testing**: `pytest` with `conftest.py` fixtures for random seeds and temp directories  
**Target Platform**: Linux (GitHub Actions runner, CPU-first)  
**Project Type**: scientific-computation  
**Performance Goals**: Full pipeline (N=3,5; broad noise range; k≥30 trials/level) completes < 4 hours on CPU; memory < 4GB.  
**Constraints**: No external data downloads (synthetic generation only); strict reproducibility via pinned seeds; numerical stability checks before analysis.  
**Scale/Scope**: System dimensions $N \in \{ \text{small integers} \}$; Noise levels: broad range from negligible ($\sim 10^{-4}$) to significant ($\sim 2.0$); Minimum $k=30$ trials per level (exact counts deferred to implementation).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `random.seed` pinning in `code/`; synthetic data generation is deterministic given inputs. |
| **II. Verified Accuracy** | **PASS** | Verified against Spec 'Assumptions': No external citations required for core algorithm; baseline validation is self-contained. The absence of external citations was explicitly verified against the Spec's 'Assumptions' section. |
| **III. Data Hygiene** | **PASS** | Plan mandates checksums for `data/processed/` artifacts; raw generated data is immutable. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/processed/` JSON/CSV; no hand-typed values in `paper/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; state file updated on change. |
| **VI. Numerical Stability** | **PASS** | **Critical**: Plan includes a mandatory validation phase (US-2) where clean-system FTLE must converge to the *numerically computed baseline for the specific coupled configuration* (N=3,5) using **Rosenstein's algorithm** before any noisy analysis proceeds. |
| **VII. Explicit Noise Scaling** | **PASS** | Plan mandates recording $\sigma_{noise}$ and $T$ for every trial; regression modeling $\Delta \lambda(T, \sigma)$ and the **scaling exponent** relating system dimension to bias magnitude is the primary output. **Every trial record includes the specific window size T used for that calculation as a metadata field.** The scaling exponent is stored as a primary artifact. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-initial-conditions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-101-quantifying-the-influence-of-initial-con/
├── code/
│   ├── __init__.py
│   ├── main.py              # Entry point for pipeline execution
│   ├── config.py            # Constants: N values, noise ranges, integration params
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── lorenz.py        # Coupled Lorenz ODE definition
│   │   └── generator.py     # Trajectory generation with noise injection
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── ftle.py          # QR-based FTLE calculation
│   │   ├── baseline.py      # Asymptotic convergence validation (Rosenstein)
│   │   └── regression.py    # Deviation modeling, t-tests, effect sizes, scaling exponent
│   └── utils/
│       ├── __init__.py
│       └── stability.py     # Attractor bounding checks, non-chaotic detection
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures (seed, temp dir)
│   ├── unit/
│   │   ├── test_lorenz.py
│   │   ├── test_ftle.py
│   │   └── test_edge_cases.py
│   └── integration/
│       └── test_pipeline.py
├── data/
│   ├── raw/                 # Generated trajectory shards (immutable)
│   └── processed/           # FTLE results, regression stats, plots
├── state/
│   └── projects/
│       └── PROJ-101-quantifying-the-influence-of-initial-con.yaml
└── docs/
    ├── quickstart.md
    └── README.md
```

**Structure Decision**: Single project structure with modular `code/` subpackages. This minimizes overhead for a scientific script while maintaining separation of concerns (simulation vs. analysis).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project is strictly bounded by CPU constraints and synthetic data. | No unnecessary complexity introduced. |

## Methodological Rigor & Statistical Plan

- **Statistical Test**: **One-sample t-test** comparing the distribution of noisy FTLE estimates against the fixed, deterministic asymptotic baseline. Two-sample tests are avoided as the baseline has no sampling variance.
- **Regression Inference**: Primary hypothesis testing relies on the p-value and confidence interval of the regression slope (bias term) in $\Delta \lambda \sim f(\sigma, N)$. **Bonferroni/FDR corrections are explicitly NOT applied.** The plan commits to **only** regression coefficient inference and one-sample t-tests against the baseline; no pairwise comparisons across noise levels will be conducted, thus rendering Bonferroni/FDR irrelevant.
- **Survivorship Bias**: Unphysical trajectories (leaving attractor) are excluded from $\Delta \lambda$ regression but included in a separate analysis of escape probability $P(\text{escape} | \sigma)$. The bias analysis is explicitly conditional on "bounded trajectories only". For unphysical trajectories, the deviation metric is set to null.
- **Variance Estimation**: Variance is calculated across independent trials ($k$), **not** across sliding windows of the same trial, to avoid autocorrelation inflation.
- **Baseline Validation**: The asymptotic baseline is computed numerically for the *specific coupled configuration* (N=3,5) using **Rosenstein's algorithm**, not a generic single-oscillator value.
- **Measure Shift**: The analysis distinguishes between small-noise bias (observational) and large-noise regime shifts (dynamical measure change) if $\sigma$ is high enough to alter the attractor. A threshold $\sigma_c$ will be determined empirically to separate these regimes.
- **Algorithm Clarification**: **QR-decomposition** is used for the general FTLE calculation over sliding windows (requiring tangent space re-orthonormalization), while **Rosenstein's algorithm** is used *specifically* for the baseline validation step to satisfy Constitution Principle VI and ensure convergence of the clean system.
- **Metadata Recording**: The sliding window size $T$ is explicitly recorded as a metadata field for every trial in the output artifacts.

## FR/SC Mapping

- **FR-001 / US-1**: `code/simulation/generator.py` handles trajectory generation with noise.
- **FR-002 / US-2**: `code/analysis/ftle.py` computes FTLE with sliding windows.
- **FR-003 / US-2**: `code/analysis/baseline.py` computes asymptotic baseline using Rosenstein's algorithm for the *specific coupled configuration*.
- **FR-004 / US-3**: `code/analysis/regression.py` performs regression modeling, **one-sample t-tests**, and calculates **effect sizes** (Cohen's d) and the **scaling exponent**.
- **FR-005 / US-3**: `code/analysis/plotting.py` generates convergence and bias scaling plots.
- **FR-006 / US-2**: `code/utils/stability.py` validates numerical stability and non-chaotic detection.
- **FR-007 / Edge Cases**: `code/simulation/generator.py` flags unphysical trajectories ($\sigma > 0.1$) and checks attractor bounds.
- **SC-001**: Validated via baseline convergence check in `code/analysis/baseline.py`.
- **SC-002**: Measured via regression slope and scaling exponent in `code/analysis/regression.py`.
- **SC-003**: Measured via t-test p-values and effect sizes in `code/analysis/regression.py`.
- **SC-004**: Measured via runtime logging in `code/main.py`.
