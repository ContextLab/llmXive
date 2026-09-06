# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-07-16 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary

This project quantifies the deviation of Finite-Time Lyapunov Exponents (FTLE) from asymptotic baselines in high-dimensional coupled Lorenz systems under varying levels of observational noise. The technical approach involves: (1) generating synthetic trajectories using `scipy.integrate.solve_ivp` (DOP853) with additive Gaussian noise; (2) computing FTLE spectra via a sliding-window algorithm with rigorous boundedness and escape-time checks (replacing deterministic shadowing for stochastic regimes); (3) establishing a numerically computed asymptotic baseline for the specific coupled configuration via ultra-long integration ($T=50,000$) and Richardson extrapolation; and (4) performing regression analysis on the deviation $\Delta \lambda$ against noise amplitude $\sigma_{noise}$ and window size $T$ using a model selection step for non-linear scaling laws. The implementation adheres to a CPU-first strategy, leveraging deterministic chaos properties to ensure reproducibility on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `matplotlib`, `pandas`, `pytest`, `pyyaml`, `ruff`, `black`  
**Storage**: Local file system (`data/raw/`, `data/processed/`) for trajectory and result artifacts  
**Testing**: `pytest` with `conftest.py` fixtures for seeds and temp directories  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7 GB RAM)  
**Project Type**: Scientific computation / CLI  
**Performance Goals**: Full pipeline (generation + analysis) < 6 hours; individual trajectory generation < 30s  
**Constraints**: No GPU required (CPU-tractable ODE integration); memory footprint < 7 GB; strict reproducibility via pinned seeds  
**Scale/Scope**: $N \in \{3, 5\}$ oscillators; $\sigma_{noise} \in \{10^{-4}, 10^{-3}, 10^{-2}, 0.05, 0.1, 0.2, 0.5, 0.8, 1.0, 1.5, 2.0\}$ (explicitly covering the (0.1, 1.0] and >1.0 regimes); $k(\sigma)$ trials per noise level (variable, $k \ge 30$, $k=50$ for $\sigma < 0.01$).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Detail |
|-----------|--------|---------------------|
| I. Reproducibility | **PASS** | Random seeds pinned in `code/config.py`; `code/` runs end-to-end; no external data fetch required (synthetic). |
| II. Verified Accuracy | **PASS** | Citations to Lorenz (1963), Rosenstein et al. (1993) will be validated against primary sources in `research.md`. |
| III. Data Hygiene | **PASS** | All `data/` artifacts checksummed; raw generation logs preserved; no in-place modification. |
| IV. Single Source of Truth | **PASS** | All figures/statistics trace to `data/processed/` JSON/CSV; no hand-typed numbers in paper. |
| V. Versioning Discipline | **Design Complete** | Mechanism designed; `state/manifest.yaml` artifact pending T001a completion. |
| VI. Numerical Stability | **PASS** | Plan explicitly includes `validate_baseline()` task (T024) using ultra-long integration ($T=50,000$) and Richardson extrapolation to confirm asymptotic limit for the *specific coupled configuration* before noisy analysis. |
| VII. Explicit Noise Scaling | **PASS** | Pipeline enforces regression model $\Delta \lambda(T, \sigma_{noise})$ as a hard gate; single averages are forbidden. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-initial-conditions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-101-quantifying-the-influence-of-initial-con/
├── code/
│   ├── __init__.py
│   ├── config.py              # Global constants, seeds, paths
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── numerical_stability.py  # T007: Convergence, boundedness checks
│   │   └── io_utils.py            # T017: Load/Save utilities
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── lorenz.py              # T046: Coupled Lorenz generator
│   │   └── noise.py               # T046: Noise injection logic
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── ftle.py                # T022/T023: FTLE algorithm + sliding window
│   │   ├── boundedness.py         # T043: Boundedness/Escape time checks (replaces Shadowing)
│   │   └── regression.py          # T033: Deviation modeling + t-test on bias term
│   └── main.py                    # T028: Gating & orchestration
├── data/
│   ├── raw/                       # Generated trajectories (checksummed)
│   └── processed/                 # FTLE results, regression outputs
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # T008: Pytest fixtures (seeds, tmp)
│   ├── unit/                      # T001c: Unit tests (stability, noise)
│   └── integration/               # T001c: End-to-end pipeline tests
├── docs/                          # Quickstart, data-model
├── state/                         # Project state manifest (T001a)
├── pyproject.toml                 # T003: Dependencies + Black/Ruff config
└── requirements.txt               # T003: Pinned dependencies
```

**Structure Decision**: Single project structure selected to minimize overhead for a computational study. The `code/` directory is split into `simulation`, `analysis`, and `utils` to enforce separation of concerns (data generation vs. metric calculation vs. utility logic). This satisfies the dependency chain: Generation (T046) -> Baseline Validation (T024) -> Gating (T028) -> FTLE Calculation (T022/23) -> Regression (T033).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Boundedness/Escape Time Check (T043) | Required to distinguish true chaos from numerical artifacts in high-noise regimes (Edge Case 1) and to measure "escape time" rather than a binary "unphysical" flag. Shadowing Lemma is invalid for stochastic trajectories. | A simple boundedness check (FR-007) is insufficient; we need to quantify the *time* until escape for stochastic trajectories. Shadowing Lemma is rejected as scientifically invalid for SDEs. |
| Separate Baseline Validation (T024) | Constitution VI requires verifying the *numerically computed* baseline for the *specific coupled configuration* using an ultra-long integration ($T=50,000$). | Relying on theoretical values (0.905) is invalid for *coupled* systems; the baseline must be derived from the specific configuration's integration. |
| Variable Trial Count (k) | SC-003 requires t-test with sufficient power for effect size, which varies with noise level. | Fixed $k=30$ is underpowered for low-noise regimes; variable $k$ ensures power across the entire range. |
| Non-linear Model Selection | The physics of FTLE bias is non-linear (power-law/logarithmic). | Simple linear regression is a misspecification; model selection (AIC/BIC) is required. |

## Task Dependency Chain (Corrected)

The following dependency chain ensures no race conditions and correct data flow:

1.  **T024 (Baseline Validation)**: Computes $\lambda_{asymptotic}$ via ultra-long integration ($T=50,000$) + Richardson extrapolation.
2.  **T028 (Gating)**: Validates T024 output. **DEPENDS ON T024**. Only if T024 passes, proceed.
3.  **T046 (Data Generation)**: Generates trajectories for all $\sigma_{noise}$ levels (including $>1.0$).
4.  **T019 (Generate Trial Sweep)**: Loops $k(\sigma)$ times per noise level. **DEPENDS ON T046**.
5.  **T022/T023 (FTLE Calculation)**: Computes FTLE for each trial. **DEPENDS ON T028** (via T024) and T019.
6.  **T033 (Analyze Bias)**: Performs regression and t-test on bias term. **DEPENDS ON T022/T023**.
7.  **T036 (Visualization)**: Generates plots. **DEPENDS ON T033**.

**Critical Correction**: T028 (Gating) is now explicitly listed as a prerequisite for T022/T023. T043 (Boundedness) is a diagnostic check run *during* T022/T023, not a blocking dependency for the algorithm itself.

## FR/SC Coverage Matrix

| ID | Requirement | Plan Element | Status |
|----|-------------|--------------|--------|
| FR-001 | Generate noisy data (broad range) | T046, T019 (includes $\sigma \in \{0.2, \dots, 2.0\}$) | Covered |
| FR-002 | Compute FTLE (sliding window) | T022, T023 | Covered |
| FR-003 | Calculate asymptotic baseline (numerical) | T024 (Ultra-long + Richardson) | Covered |
| FR-004 | Regression analysis | T033 (Model selection + regression) | Covered |
| FR-005 | Convergence plot | T036 | Covered |
| FR-006 | Validate numerical stability | T024 (Gated by T028) | Covered |
| FR-007 | Flag high-noise ($\sigma > 0.1$) | T022/T023 (Boundedness/Escape time check) | Covered |
| SC-001 | Convergence validation | T024 (Error < 5% via Richardson) | Covered |
| SC-002 | Bias scaling | T033 (Regression coefficients) | Covered |
| SC-003 | t-test on bias term | T033 (Explicit t-test on $\beta$) | Covered |
| SC-004 | Runtime | CPU-first strategy, < 6h | Covered |