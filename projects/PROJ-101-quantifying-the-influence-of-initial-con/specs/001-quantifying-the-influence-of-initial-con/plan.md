# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-08-06 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary

This project implements a computational study to quantify how observational noise biases Finite-Time Lyapunov Exponent (FTLE) estimates in high-dimensional coupled Lorenz systems. The technical approach involves: (1) generating synthetic trajectory data using `scipy.integrate.solve_ivp` with strict tolerances; (2) numerically computing the asymptotic Lyapunov spectrum for the specific coupled configuration to establish a ground-truth baseline (validated via Richardson extrapolation); (3) calculating FTLEs over sliding windows for noisy trajectories; and (4) performing regression analysis with a model-selection step (Power-law vs. LOESS) to determine the true functional form of the deviation $\Delta \lambda$. The implementation strictly adheres to the project constitution, enforcing a "fail-stop" mechanism if the baseline convergence, shadowing lemma, or non-chaotic checks fail, and resolving spec ambiguities regarding noise thresholds by implementing a two-tier check: a "high-noise" warning at $\sigma > 0.1$ and an "unphysical" abort if the trajectory leaves the attractor bounds, while explicitly validating the $N=5$ runtime constraint ($\le 30$s) via a dedicated benchmark task.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy` (specifically `scipy.integrate.solve_ivp` with 'DOP853'), `matplotlib`, `pandas`, `pytest`, `pyyaml`, `mpmath` (for high-precision error floor checks), `statsmodels` (for model selection)  
**Storage**: Local file system (`data/raw`, `data/processed`), Parquet/JSON for artifacts  
**Testing**: `pytest` (unit, integration, and performance benchmarks)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Scientific Computing Library / CLI  
**Performance Goals**: N=5 trajectory generation $\le 30$s; Full analysis pipeline $\le 6$h (CPU); Numerical convergence $< 5\%$ error at $T=5000$; Baseline convergence via Richardson extrapolation  
**Constraints**: No GPU required (ODE integration and linear algebra for FTLE are CPU-tractable); Memory $\le 7$GB (streaming if trajectory length $> 10^6$); Strict reproducibility (pinned seeds)  
**Scale/Scope**: Dimensions $N \in \{1, 3, 5, 10\}$; Noise levels $\sigma \in [0, 1.0]$; Trajectory lengths $T \in [500, 5000]$

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Plan Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned; CI re-runnable. | `code/config.py` defines `GLOBAL_SEED = 42`. `pytest` fixtures enforce seed reset. CI workflow explicitly sets `RANDOM_SEED` env var. |
| **II. Verified Accuracy** | Citations verified against primary sources. | Standard mathematical definitions (Lorenz, FTLE) are cited in `research.md` and validated by the Reference-Validator Agent. No external citations in code logic. |
| **III. Data Hygiene** | Checksums; no in-place modification. | `scripts/checksums.sh` generates SHA-256 for all `data/` files. `data/raw` is read-only; `data/processed` contains derived artifacts with `_v1` versioning. |
| **IV. Single Source of Truth** | Figures trace to `data/` and `code/`. | Visualization scripts (`code/visualize.py`) read strictly from `data/processed/*.json`. No manual data entry in `paper/`. |
| **V. Versioning** | Content hashes; `updated_at` timestamps. | `state/projects/PROJ-101-...yaml` updated on every artifact write. Hashes stored in `state/artifact_hashes`. |
| **VI. Numerical Stability** | Baseline validation *before* noisy analysis. | **Gating Mechanism**: Task `T_gate_baseline_validation` explicitly implements the orchestrator logic. It runs `T_compute_baseline` and `T_check_nonchaotic`. If `lambda_max` does not converge (error $> 5\%$) or system is non-chaotic ($\lambda_{max} \le 0$), the process raises `NonChaoticSystemError` and halts. No noisy tasks execute. |
| **VII. Explicit Noise Scaling** | Record $\sigma$ and $T$; regression modeling. | `data/processed/results.json` schema includes `noise_level`, `window_size`, `deviation`. Regression is mandatory; single averages are forbidden. Model selection (Power-law vs. LOESS) is enforced. |

**Resolved Ambiguities (from Unresolved Concerns):**
1.  **Noise Threshold ($\sigma > 0.1$ vs $1.0$):** The plan implements a dual-check. A `HighNoiseWarning` is triggered at $\sigma > 0.1$ (per FR-007 text). An `UnphysicalTrajectoryError` is raised *only* if the trajectory state exceeds physical bounds (e.g., $|x| > 100$) OR if $\sigma > 1.0$ *and* the trajectory diverges. This resolves the spec conflict by distinguishing "high noise" (warning) from "unphysical" (abort). Task `T_check_unphysical_bounds` implements this logic.
2.  **Gating Mechanism:** Task `T_gate_baseline_validation` explicitly wires the validation logic from `T_compute_baseline` and `T_check_nonchaotic` into the main execution flow, ensuring a fail-stop before noisy analysis.
3.  **Runtime Constraint:** Task `T_bench_runtime_n5` is added to specifically verify the $N=5, \le 30$s constraint.
4.  **Non-Chaotic Abort:** Task `T_check_nonchaotic` defines the specific error class `NonChaoticSystemError` and the input source (config `rho`). The check is based on the *numerically computed* $\lambda_{max} > 0$, not a fixed $\rho$ threshold.
5.  **Baseline Output:** Task `T_compute_baseline` specifies the output schema: `data/processed/baseline_{N}.json` with keys `lambda_max`, `convergence_error`, `trajectory_length`.
6.  **Regression Model:** The plan includes a model selection step (LOESS vs Power-law) to determine the true functional form of the deviation, addressing the non-linearity concern.
7.  **Numerical Error Floor:** The plan mandates a "clean-noise" baseline computation using Richardson extrapolation to establish the integration error floor. Bias is only reported if it exceeds this floor.
8.  **Shadowing Lemma:** Task `T_shadowing_check` validates that the noisy trajectory still shadows a true orbit before FTLE is computed.
9.  **Baseline Validation Target:** The baseline is validated against the *numerically computed asymptotic limit for the specific coupled configuration*, not a fixed theoretical value.

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-initial-conditions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── trajectory.schema.yaml
│   ├── baseline.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-101-quantifying-the-influence-of-initial-con/
├── code/
│   ├── __init__.py
│   ├── config.py              # Seeds, parameters, thresholds
│   ├── generator.py           # Lorenz ODE, noise injection
│   ├── ftle.py                # Sliding window FTLE, tangent linear
│   ├── baseline.py            # Asymptotic computation, Richardson extrapolation
│   ├── analysis.py            # Regression, statistical tests, model selection
│   ├── visualize.py           # Plotting
│   ├── orchestrator.py        # Pipeline flow, gating logic
│   └── errors.py              # Custom exceptions (UnphysicalTrajectoryError, etc.)
├── tests/
│   ├── unit/
│   │   ├── test_generator.py
│   │   ├── test_ftle.py
│   │   ├── test_baseline.py
│   │   └── test_errors.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── performance/
│       └── test_runtime_benchmark.py  # Verifies 30s constraint
├── data/
│   ├── raw/                   # Generated trajectories (parquet)
│   └── processed/             # Baselines, FTLE results, regression outputs (json)
├── scripts/
│   ├── checksums.sh
│   └── run_analysis.sh
└── requirements.txt
```

**Structure Decision**: Single project structure (Option 1) chosen to minimize overhead for a computational science pipeline. All logic resides in `code/` with clear separation of concerns (generator, solver, analyzer). The `orchestrator.py` handles the critical gating logic required by Constitution Principle VI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Custom Exception Hierarchy | Required to distinguish `UnphysicalTrajectoryError` from `NonChaoticSystemError` for precise gating. | Generic `RuntimeError` would not allow the orchestrator to implement specific recovery or abort logic per FR-007 and FR-006. |
| Dual Noise Threshold Logic | Spec ambiguity (0.1 vs 1.0) requires explicit handling to avoid premature aborts or silent failures. | A single threshold would either block valid high-noise experiments or fail to catch unphysical divergence. |
| Gating Orchestrator | Constitution Principle VI mandates baseline validation *before* noisy analysis. | A linear script without explicit gating risks executing noisy analysis on an unstable baseline, invalidating results. |
| Model Selection (LOESS vs Power-law) | The true functional form of noise bias is unknown and likely non-linear. | A fixed linear model risks incorrect conclusions about scaling laws. |
| Numerical Error Floor Check | To distinguish true noise bias from integration artifacts. | Without this, "infinite power" is a fallacy if the signal is buried in numerical noise. |
| Shadowing Lemma Check | To ensure the noisy trajectory is still a valid estimate of the system's dynamics. | If the trajectory no longer shadows a true orbit, the FTLE is meaningless. |

## Task List (Draft for Phase 2)

*Note: This list is a draft for the Implementer Agent. It explicitly maps requirements to tasks.*

- **T001**: Create project structure per implementation plan (atomized into file creation tasks).
- **T012**: Implement noise injection logic (additive Gaussian).
- **T016**: Implement `T_check_unphysical_bounds` logic (detects |x| > 100 or divergence) and raises `UnphysicalTrajectoryError`.
- **T018**: Orchestrate generation loop (N, sigma) and trigger `T_check_unphysical_bounds`.
- **T024**: Implement `T_compute_baseline` (QR-based algorithm, Richardson extrapolation for error floor).
- **T025**: Implement `T_check_nonchaotic` (checks numerical $\lambda_{max} > 0$).
- **T_gate_baseline_validation**: Implement orchestrator gating logic: Run `T_compute_baseline` -> Run `T_check_nonchaotic` -> If pass, proceed; else abort.
- **T026**: Implement `T_shadowing_check` (validates divergence rate).
- **T036**: Implement regression analysis with model selection (Power-law vs. LOESS).
- **T_bench_runtime_n5**: Implement performance benchmark to verify N=5 generation $\le 30$s.
- **T037**: Documentation updates (atomized into specific doc generation tasks).
