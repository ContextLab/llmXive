# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-10-16 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`  
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary
The pipeline will (1) generate synthetic trajectories of coupled Lorenz oscillators with configurable Gaussian noise, (2) compute a rigorously validated clean‑system asymptotic Lyapunov baseline, (3) calculate Finite‑Time Lyapunov Exponents (FTLE) over sliding windows, (4) flag unphysical trajectories (`‖x‖ > 20.0`) and non‑chaotic systems, (5) perform a mixed‑effects regression with Durbin‑Watson detection, Newey‑West HAC correction, Benjamini‑Hochberg FDR, and an always‑fit Tobit censored model, and (6) generate reproducible figures and JSON artifacts validated against explicit schemas. All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language**: Python 3.11  
- **Core Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `statsmodels`, `pyyaml`  
- **Storage**: Local filesystem under `data/` (raw trajectories, processed results, plots)  
- **Testing**: `pytest` with fixtures for deterministic seeds and temporary directories  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goal**: End‑to‑end wall‑clock ≤ 45 min, peak RAM < 2 GB (well within the 7 GB limit)  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | All random seeds are pinned (`config.SEED = 42`). Synthetic generation is deterministic given parameters. |
| II. Verified Accuracy | PASS | No external citations are required; all algorithms are standard and implemented directly. |
| III. Data Hygiene | PASS | Raw `.npz` files are immutable; every transformation writes a new file and records a SHA‑256 checksum in `state/artifacts/manifest.yaml`. |
| IV. Single Source of Truth | PASS | Figures and tables are generated directly from the JSON artifacts; no manual transcription. |
| V. Versioning Discipline | PASS | Artifact hashes are stored in `state/projects/PROJ-101-...yaml`. |
| VI. Numerical Stability and Baseline Validation | PASS | Baseline computed with Rosenstein’s method; convergence < 5 % error at `T=5000` is enforced before any noisy analysis. |
| VII. Explicit Noise Scaling Characterization | PASS | Every trial records `σ_noise`, `N`, `T`, and boundedness flag; regression explicitly models `Δλ` as a function of these variables. |

## Project Structure
```
specs/001-quantify-initial-conditions/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── baseline.schema.yaml
    ├── ftle_result.schema.yaml
    ├── ftle_results.schema.yaml
    ├── regression_results.schema.yaml
    ├── trajectory.schema.yaml
    └── results.schema.yaml

projects/PROJ-101-quantifying-the-influence-of-initial-con/
├── code/
│   ├── __init__.py
│   ├── main.py                # CLI entry point
│   ├── config.py              # Global constants & defaults
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── lorenz.py          # Coupled Lorenz ODE definition
│   │   └── generator.py       # Trajectory generation, noise injection, warnings, errors
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── baseline.py        # Rosenstein baseline + convergence check
│   │   ├── ftle.py            # QR‑based FTLE over sliding windows
│   │   ├── regression.py      # Mixed‑effects, Newey‑West, BH‑FDR, Tobit
│   │   └── plotting.py        # Convergence & bias‑scaling figures
│   └── utils/
│       ├── __init__.py
│       └── stability.py       # Boundedness, chaos detection, DW test
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # seed & temp‑dir fixtures
│   ├── unit/
│   │   ├── test_lorenz.py
│   │   ├── test_generator.py   # verifies HighNoiseWarning & UnphysicalTrajectoryError
│   │   └── test_stability.py
│   └── integration/
│       └── test_generation.py   # end‑to‑end generation verification
├── data/
│   ├── raw/                    # Immutable `.npz` trajectories
│   └── processed/
│       ├── ftle_results.json
│       ├── baseline_{N}.json
│       ├── regression_results.json
│       ├── results.json
│       └── plots/
│           ├── convergence.png
│           ├── bias_scaling.png
│           └── dimension_scaling.png
└── state/
    └── artifacts/
        └── manifest.yaml        # Checksums & metadata (platform‑owned)
```

## Phase‑by‑Phase Tasks (covers every FR/SC)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0. Bootstrap** | Create `requirements.txt`, `pyproject.toml`, seed fixture, and ensure `state/artifacts/manifest.yaml` is generated only by platform. | – |
| **1. Trajectory Generation** (`code/simulation/generator.py`) | <ul><li>Integrate coupled Lorenz ODE with `solve_ivp` (method `DOP853`, `rtol=1e-9`, `atol=1e-12`).</li><li>Inject i.i.d. Gaussian noise `σ_noise` at each step.</li><li>Emit `HighNoiseWarning` when `σ_noise > 0.1`.</li><li>Raise `UnphysicalTrajectoryError` if any state norm exceeds 20.0 **during** integration (covers FR‑007).</li><li>Save immutable `.npz` file containing `time`, `state`, `noise`, and `params` (including seed, N, σ_noise, trial id).</li></ul> | **FR‑001**, **FR‑007**, **FR‑009** (store `σ_noise` for later residual analysis) |
| **2. Baseline Validation** (`code/analysis/baseline.py`) | <ul><li>Integrate a **noise‑free** trajectory of length ≥ 50 000 steps (ensures sufficient data for convergence).</li><li>Apply Rosenstein’s algorithm to compute FTLE for a series of increasing window sizes.</li><li>Determine the asymptotic exponent `λ_∞` when relative change between `T=5000` and `T=10 000` is < 5 %.</li><li>Write `baseline_{N}.json` with fields `system_dimension`, `lambda_max`, `convergence_error`, `status="valid"` (or `"invalid"`), `trajectory_length`, `algorithm`.</li><li>Abort pipeline if `status!="valid"`.</li></ul> | **FR‑003**, **FR‑006**, **SC‑001** |
| **3. FTLE Computation** (`code/analysis/ftle.py`) | <ul><li>For each noisy trajectory, compute FTLE over sliding windows `T ∈ {500, 1000, 5000}` using QR re‑orthonormalisation (stable for high‑dim ODE).</li><li>Record `trial_id`, `system_dimension`, `noise_level`, `window_size`, `lambda_max`, `deviation` (null if status ≠ “valid”), `status` (`valid`, `unphysical`, `non‑chaotic`).</li><li>Append each entry to an in‑memory list; after all trials, dump aggregated list to `data/processed/ftle_results.json` and validate against `contracts/ftle_results.schema.yaml`.</li></ul> | **FR‑002**, **FR‑010**, **FR‑007**, **FR‑009** |
| **4. Edge‑Case & Stability Checks** (`code/utils/stability.py`) | <ul><li>`check_boundedness(state) → bool` (‖x‖ ≤ 20.0).</li><li>`raise_if_unphysical(state)` raises `UnphysicalTrajectoryError` if bound violated.</li><li>`detect_chaos(lambda_max) → bool` aborts with `NonChaoticSystemError` if `lambda_max ≤ 0`.</li><li>`durbin_watson_test(series) → (DW, p)`; store p‑value in FTLE result metadata.</li></ul> | **FR‑007**, **FR‑009**, **SC‑003** |
| **5. Regression & Statistical Analysis** (`code/analysis/regression.py`) | <ul><li>Build dataset of `Δλ = λ_FTLE – λ_baseline` **only** for rows with `status="valid"`.</li><li>Fit a **mixed‑effects linear model**: `Δλ ~ σ_noise + N + σ_noise·N + 1/T` with random intercept per trajectory (using `statsmodels` MixedLM).</li><li>Compute Durbin‑Watson on residuals; if `p < 0.05`, recompute standard errors with Newey‑West HAC (`cov_type="HAC"`).</li><li>Apply Benjamini‑Hochberg FDR (q ≤ 0.05) to all fixed‑effect p‑values.</li><li>Fit a **Tobit censored regression** on the full dataset (including `unphysical` points) to estimate latent bias.</li><li>Estimate escape probability per `σ_noise` as fraction of trials flagged `unphysical`.</li><li>Write `regression_results.json` (validated against `contracts/regression_results.schema.yaml`).</li></ul> | **FR‑004**, **FR‑005**, **FR‑008**, **FR‑009**, **SC‑002**, **SC‑003**, **SC‑004** |
| **6. Artifact Packaging & Validation** | <ul><li>Generate `results.json` bundling `ftle_results.json`, `baseline_{N}.json`, `regression_results.json`, and escape probabilities.</li><li>Validate each JSON file against its schema using `jsonschema`. </li><li>Compute SHA‑256 checksums for every file in `data/` and write them to `state/artifacts/manifest.yaml` (platform‑owned, not part of the project’s own outputs).</li></ul> | **III**, **V**, **VI**, **VII** |
| **7. Visualization** (`code/analysis/plotting.py`) | <ul><li>Convergence plot: λ vs. T for three noise levels (clean, moderate, high).</li><li>Bias‑scaling plot: Δλ vs. σ_noise with SEM error bars.</li><li>Dimension‑scaling plot: Δλ vs. N on log‑log axes; fit power‑law exponent.</li><li>Save PNGs under `data/processed/plots/`.</li></ul> | **FR‑005**, **FR‑004**, **SC‑002** |
| **8. CI / Testing** | <ul><li>Run unit tests (ODE correctness, noise statistics, warning/error emission).</li><li>Run integration test `tests/integration/test_generation.py` that checks at least one `.npz` file is created and conforms to `trajectory.schema.yaml`.</li><li>Benchmark: ensure generation of `N=5`, `T=10 000`, 5 trials completes < 30 s on the runner.</li></ul> | **All FRs** (verification) |
| **9. Documentation** | Update `quickstart.md`, `README.md`, and all schema files. | – |

## Statistical Rigor Checklist
- **Multiple comparisons** – Benjamini‑Hochberg FDR applied to all fixed‑effect coefficients.  
- **Power** – Simulation‑based power analysis (see Research) indicates ≥ 80 % power to detect a small‑to‑medium effect (`f²≈0.02`) with the planned 1 080 observations.  
- **Causal claim** – All statements are *associational*; the system is purely observational.  
- **Measurement validity** – Lorenz parameters are standard; Rosenstein baseline is a validated method (Constitution VI).  
- **Collinearity** – VIFs will be reported; interaction term dropped if VIF > 5.

## Compute Feasibility (CPU‑First)
- **Memory**: One trajectory (N=5, 15 states, 10 000 steps) ≈ 1.2 MB; 30 trials ≈ 36 MB plus overhead.  
- **CPU**: Integration + QR decomposition are lightweight; full grid (N = 3,5; 6 noise levels; 30 trials; 3 windows) ≈ 2 h total compute; with 2‑core multiprocessing wall‑clock ≈ 42 min, satisfying the 45 min CI limit.  
- **GPU**: Not required; all methods have faithful CPU implementations.

## Decision / Rationale
1. **Synthetic data only** – Guarantees full control over noise and dimensionality; no external dataset needed, satisfying the data‑availability rule.  
2. **DOP853 + tight tolerances** – Guarantees numerical error far below the smallest noise level we study.  
3. **QR re‑orthonormalisation** – Provides numerically stable FTLE estimates for long windows.  
4. **Rosenstein baseline** – Meets Constitution VI and supplies a deterministic reference for Δλ.  
5. **Mixed‑effects regression** – Properly accounts for hierarchical dependence of overlapping windows.  
6. **Durbin‑Watson + Newey‑West** – Satisfy FR‑009 and handle autocorrelation.  
7. **Always‑fit Tobit** – Removes post‑hoc selection bias for censored observations.  
8. **Parallel trial execution** – Keeps total runtime within CI limits while preserving reproducibility (each worker seeded independently).  

---
