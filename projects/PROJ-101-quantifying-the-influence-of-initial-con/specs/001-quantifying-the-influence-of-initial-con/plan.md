# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-08-05 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary

This feature implements a computational study to quantify how observational noise and finite-time window lengths bias the estimation of Lyapunov exponents in high-dimensional chaotic systems. The approach involves generating synthetic trajectories from coupled Lorenz oscillators using `scipy.integrate.solve_ivp`, computing Finite-Time Lyapunov Exponents (FTLE) via a tangent-linear propagation algorithm using the *noisy* states (with Jacobians evaluated at noisy points), and performing regression analysis to model the deviation $\Delta \lambda$ as a function of noise amplitude $\sigma_{noise}$ and window size $T$. The implementation strictly adheres to the project constitution's requirements for reproducibility, numerical stability validation against numerically computed asymptotic baselines (via Richardson extrapolation), and explicit noise scaling characterization with rigorous model selection.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scipy` (integration), `numpy` (numerical arrays), `matplotlib` (visualization), `pandas` (data handling), `pytest` (testing), `statsmodels` (regression).  
**Storage**: Local file system (`data/` for generated trajectories and results; no external database).  
**Testing**: `pytest` with unit tests for ODE solvers, FTLE convergence, and regression statistics; integration tests for the full pipeline.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational research library/cli.  
**Performance Goals**: Full pipeline (generation + FTLE + regression) completes in ≤ 45 minutes on CPU. Trajectory generation for $N \le 10$ oscillators and $T_{total} \approx 10^5$ steps must complete in < 30s.  
**Constraints**: No external GPU required (CPU-first methodology); memory footprint < 7 GB; strict numerical tolerances (`rtol=1e-9`, `atol=1e-12`) enforced to ensure baseline validity. These tolerances are critical for **Constitution Principle VI** as they prevent integration error from biasing the asymptotic baseline used in model selection.  
**Scale/Scope**: $N \in \{1, 3, 5, 10\}$ coupled oscillators; $\sigma_{noise} \in [10^{-4}, 1.0]$; $T \in \{100, 500, 1000, 5000\}$.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/` (e.g., `np.random.seed(42)`). `requirements.txt` pins exact versions. CI runs from scratch. |
| **II. Verified Accuracy** | **PASS** | No external citations for data (synthetic). Mathematical methods (Rosenstein's algorithm, DOP853, Richardson extrapolation) are standard; references will be validated against primary literature if cited in `research.md`. |
| **III. Data Hygiene** | **PASS** | Generated trajectories are treated as "raw data". Checksums (SHA-256) recorded in `state/`. Derivations (FTLE results) written to new files. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in `paper/` will be generated programmatically from `data/` via scripts in `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes of `code/` and `data/` will be updated in `state/` upon any change. |
| **VI. Numerical Stability** | **PASS** | Plan includes a mandatory Phase 0 step: Validate clean system FTLE convergence to the *numerically computed* asymptotic baseline for the specific (N, D) configuration using **Richardson extrapolation**. This baseline is NOT the theoretical single-oscillator value (0.905) for coupled systems. Strict tolerances (`rtol=1e-9`, `atol=1e-12`) are enforced to ensure this baseline is not biased by integration error. |
| **VII. Explicit Noise Scaling** | **PASS** | Regression analysis explicitly models $\Delta \lambda(T, \sigma_{noise})$ using a **Model Selection Strategy** (AIC/BIC) to determine the functional form (additive, multiplicative, or saturation), rather than assuming a fixed power law. Escape events are modeled as a distinct outcome to prevent selection bias. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-initial-conditions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── trajectory.schema.yaml
    └── ftle_results.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-101-quantifying-the-influence-of-initial-con/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py              # Hyperparameters, seeds, paths
│   ├── data/
│   │   ├── __init__.py
│   │   ├── generator.py       # Coupled Lorenz + Noise injection
│   │   └── loader.py          # Data loading utilities
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── ftle.py            # FTLE calculation (Rosenstein/Tangent)
│   │   ├── baseline.py        # Asymptotic convergence validation
│   │   └── regression.py      # Statistical analysis & plotting
│   └── main.py                # Pipeline orchestrator
├── tests/
│   ├── unit/
│   │   ├── test_generator.py
│   │   └── test_ftle.py
│   └── integration/
│       └── test_pipeline.py
├── data/                      # Generated artifacts (gitignored, tracked in state)
│   ├── raw/
│   └── processed/
└── state/
    └── projects/PROJ-101-quantifying-the-influence-of-initial-con.yaml
```

**Structure Decision**: Single-project structure selected. The project is a self-contained computational study. No web/mobile components. `code/` is split into `data` (generation) and `analysis` (processing) to enforce the "Data Hygiene" principle (raw data generation separate from derived analysis).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **High-Dimensional Coupling** | Research question requires $N > 1$ to study dimensionality effects. | Single oscillator ($N=1$) is insufficient to answer the scaling hypothesis. |
| **Tangent Linear Propagation** | Accurate FTLE requires Jacobian integration, not just trajectory divergence. | Simple distance-based methods (e.g., Benettin) are less robust for high dimensions and finite windows. |
| **Strict Numerical Tolerances** | Chaos is sensitive to integration error; `rtol=1e-9` ensures bias is from noise, not solver. These tolerances are essential for the **Model Selection Strategy** to distinguish true signal from numerical noise. | Default tolerances (`rtol=1e-6`) introduce numerical drift indistinguishable from observational noise. |
| **Model Selection Strategy** | The functional form of noise bias is unknown (linear, power-law, or saturation). | Assuming a fixed power-law form risks model misspecification and invalid coefficients. |
| **Noisy Tangent Propagation** | Real-world estimation uses noisy data for both state and Jacobian. | Using clean Jacobians would measure a theoretical artifact, not the actual estimation bias. |
| **Richardson Extrapolation** | The asymptotic baseline for coupled systems is not a known constant. | Using a finite-time estimate (e.g., T=5000) as the baseline would create circular validation. |

## Compute Feasibility

- **CPU-First**: The entire pipeline (ODE integration, Jacobian propagation, regression) is computationally light enough for the GitHub Actions free-tier (2 CPU, 7 GB RAM).
- **Memory**: Storing $N=10$ trajectories of $10^5$ steps requires $\approx 10 \times 10^5 \times 30 \times 8$ bytes $\approx 240$ MB. Well within limits.
- **Runtime**:
  - ODE Integration: $\approx$ seconds per trajectory.
  - FTLE Calculation: Approximately a few seconds per trajectory.
  - Total for multiple trials $\times$ multiple noise levels $\times$ 4 dimensions $\approx 6000$ trajectories.
  - Estimated total time: approximately one workday on a single core.
  - **Optimization**: The plan will parallelize trials across the 2 available cores (using `multiprocessing`) to reduce runtime to $\approx 5$ hours, safely within the 6-hour CI limit. If needed, $k$ will be reduced to a small integer or $N$ limited to a small integer to guarantee completion.