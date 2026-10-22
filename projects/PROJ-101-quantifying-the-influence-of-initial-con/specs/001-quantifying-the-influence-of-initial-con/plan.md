# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-10-22 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`  
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary
The pipeline will (1) generate synthetic high‑dimensional coupled Lorenz trajectories with configurable Gaussian observational noise, (2) compute a rigorously validated clean‑system asymptotic Lyapunov baseline (multiple noise‑free runs, variance propagation), (3) calculate Finite‑Time Lyapunov Exponents (FTLE) over sliding windows using QR re‑orthonormalisation, (4) flag unphysical trajectories (`‖x‖ > 20.0`) and abort on non‑chaotic configurations, (5) perform mixed‑effects regression (random intercept + random slope for window size) with baseline‑variance weighting, (6) apply Durbin‑Watson, Newey‑West, and Benjamini‑Hochberg FDR corrections, (7) always fit a Tobit censored model to quantify bias under trajectory escape, (8) compute escape probabilities, (9) generate required visualizations, and (10) bundle all artifacts with JSON‑schema validation. All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `statsmodels`, `pyyaml`, `jsonschema`  
- **Storage**: Local filesystem under `data/` (raw trajectories, processed results, plots).  
- **Testing**: `pytest` with deterministic seeds; unit tests for generator, baseline, FTLE, and integration test for end‑to‑end generation.  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ~7 GB RAM).  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 45 min, peak RAM < 2 GB.  
- **Constraints**: Must satisfy all functional requirements FR‑001 … FR‑010 and success criteria SC‑001 … SC‑004.

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | **PASS** | All random seeds are pinned (`config.SEED = 42`). Files are deterministic given parameters. |
| II. Verified Accuracy | **PASS** | No external citations are introduced; all algorithms are textbook methods. |
| III. Data Hygiene | **PASS** | Raw `.npz` trajectories are immutable; every transformation writes a new file; checksums recorded in platform‑owned `state/artifacts/manifest.yaml`. |
| IV. Single Source of Truth | **PASS** | Figures and tables are generated directly from JSON artifacts; no manual transcription. |
| V. Versioning Discipline | **PASS** | Artifact hashes stored in `state/projects/...yaml`; pipeline never overwrites raw data. |
| VI. Numerical Stability and Baseline Validation | **PASS** | Baseline computed with Rosenstein’s method on ≥ 5 noise‑free runs; convergence < 5 % enforced before noisy analysis. |
| VII. Explicit Noise Scaling Characterization | **PASS** | Every experimental run records `σ_noise`, `N`, `T`, and boundedness flag; regression explicitly models `Δλ`. |

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
    ├── regression_stats.schema.yaml
    ├── results.schema.yaml
    └── trajectory.schema.yaml

projects/PROJ-101-quantifying-the-influence-of-initial-con/
├── code/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Global constants & defaults
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── lorenz.py           # Coupled Lorenz ODE definition
│   │   └── generator.py        # Trajectory generation, noise injection, warnings, errors
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── baseline.py         # Rosenstein baseline + convergence check (multiple runs, variance)
│   │   ├── ftle.py             # QR‑based FTLE over sliding windows
│   │   ├── regression.py       # Mixed‑effects + Tobit regression, DW, Newey‑West, BH‑FDR
│   │   └── plotting.py         # Convergence & bias‑scaling figures
│   └── utils/
│       ├── __init__.py
│       └── stability.py        # Boundedness, chaos detection, DW test
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Seed & temp‑dir fixtures
│   ├── unit/
│   │   ├── test_lorenz.py
│   │   ├── test_generator.py   # verifies HighNoiseWarning & UnphysicalTrajectoryError
│   │   └── test_stability.py
│   └── integration/
│       └── test_generation.py  # end‑to‑end generation, checks .npz files exist
├── data/
│   ├── raw/                    # Immutable `.npz` trajectories
│   └── processed/
│       ├── ftle_results.json
│       ├── baseline_{N}.json
│       ├── baseline_per_window_{N}.json   # per‑window baseline with variance & convergence error
│       ├── regression_results.json
│       ├── results.json
│       └── plots/
│           ├── convergence.png
│           ├── bias_scaling.png
│           └── dimension_scaling.png
└── README.md
```

## Phase‑by‑Phase Tasks (covers every FR/SC)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0. Bootstrap** | Create `requirements.txt` (pin exact versions) and a `state/artifacts/manifest.yaml` generator (platform‑owned). No project‑owned writes to `state/`. | **FR‑001**, **SC‑004** |
| **1. Trajectory Generation** (`code/simulation/generator.py`) | • Integrate coupled Lorenz ODE with `solve_ivp` (`method='DOP853'`, `rtol=1e-9`, `atol=1e-12`). <br>• Inject i.i.d. Gaussian noise `σ_noise` at each step. <br>• Emit `HighNoiseWarning` when `σ_noise > 0.1`. <br>• Raise `UnphysicalTrajectoryError` if any state norm exceeds `20.0` during integration. <br>• Return a dict matching `trajectory.schema.yaml` and save as `.npz` under `data/raw/`. <br>• Store metadata (`seed`, `N`, `sigma_noise`, `trial_id`). | **FR‑001**, **FR‑007**, **FR‑009** |
| **2. Integration Test** (`tests/integration/test_generation.py`) | Loop over a small grid (e.g., `N=3`, `σ_noise=0.01`, 2 trials). Invoke CLI (`python -m code.main --mode generate ...`). Assert `.npz` files appear and validate each against `trajectory.schema.yaml`. | **All FRs** (verification) |
| **3. Baseline Validation** (`code/analysis/baseline.py`) | • For each dimension `N`, generate **K ≥ 5** independent noise‑free trajectories of length **≥ 50 000** steps. <br>• Apply **Rosenstein’s algorithm** to each; compute FTLE for windows `T = 1000, 2000, …, 10 000`. <br>• Aggregate to produce **mean baseline**, **variance**, and **convergence error** per window. <br>• Determine asymptotic exponent `λ_∞` when relative change between `T=5000` and `T=10 000` is **< 5 %**. <br>• If `λ_∞ ≤ 0`, raise `NonChaoticSystemError`. <br>• Write `baseline_{N}.json` (status `"valid"` only when convergence satisfied) and `baseline_per_window_{N}.json` (array of `{window_size, lambda_mean, lambda_std, convergence_error}`). <br>• Validate both against `baseline.schema.yaml`. | **FR‑003**, **FR‑006**, **SC‑001**, **VI** |
| **4. FTLE Computation** (`code/analysis/ftle.py`) | • For each noisy trajectory, propagate the tangent linear system alongside the state. <br>• At every step perform **QR re‑orthonormalisation**. <br>• Compute FTLE over sliding windows `T ∈ {500, 1000, 5000}`. <br>• Record `status` (`"valid"`, `"unphysical"`, `"non‑chaotic"`), `deviation` (null if not valid), and Durbin‑Watson p‑value. <br>• Append each result to an in‑memory list and dump **`ftle_results.json`** (validated against `ftle_results.schema.yaml`). | **FR‑002**, **FR‑010**, **FR‑007**, **FR‑009** |
| **5. Edge‑Case & Stability Checks** (`code/utils/stability.py`) | • `check_boundedness(state) → bool` (‖x‖ ≤ 20.0). <br>• `raise_if_unphysical(state)` raises `UnphysicalTrajectoryError`. <br>• `detect_chaos(lambda_max) → bool` aborts with `NonChaoticSystemError` if ≤ 0. <br>• `durbin_watson_test(series) → (DW, p)`; store p‑value in FTLE metadata. <br>• Wire these helpers into **generator** (for unphysical detection) and **FTLE** (for DW test). | **FR‑007**, **FR‑009**, **SC‑003** |
| **6. Regression & Statistical Analysis** (`code/analysis/regression.py`) | • Build dataset of `Δλ = λ_FTLE – λ_baseline_mean` **only** for rows with `status="valid"`. <br>• Fit a **mixed‑effects linear model** with random intercept **and** random slope for window size (or AR(1) covariance) using `statsmodels.MixedLM`. <br>• Perform **Durbin‑Watson** on residuals; if `p < 0.05`, recompute SEs with **Newey‑West HAC** (`cov_type="HAC"`). <br>• Apply **Benjamini‑Hochberg FDR** (`q ≤ 0.05`) to all fixed‑effect p‑values. <br>• Incorporate **baseline variance** (from Phase 3) as observation‑level weights; record flag `baseline_variance_used`. <br>• Fit a **Tobit censored regression** on the full dataset (including `unphysical` points). <br>• Compute **escape probability** per `σ_noise` (fraction of `unphysical` trials). <br>• Write `regression_results.json` (validated against `regression_results.schema.yaml`). | **FR‑004**, **FR‑005**, **FR‑008**, **FR‑009**, **SC‑002**, **SC‑003**, **SC‑004**, **VI**, **VII** |
| **7. Artifact Bundling & Validation** | • Assemble `results.json` containing baseline, FTLE, regression, and escape probabilities. <br>• Validate each component against its schema using `jsonschema`. <br>• Compute SHA‑256 checksums for every file in `data/` and record them in platform‑owned `state/artifacts/manifest.yaml`. | **FR‑005**, **SC‑001**, **SC‑002**, **SC‑003**, **SC‑004** |
| **8. Visualization** (`code/analysis/plotting.py`) | • **Convergence plot**: λ vs. T for three noise levels (clean, moderate, high). <br>• **Bias‑scaling plot**: Δλ vs. σ_noise with SEM error bars. <br>• **Dimension‑scaling plot**: Δλ vs. N on log‑log axes; fit power‑law exponent. <br>• Save PNGs under `data/processed/plots/`. | **FR‑005**, **FR‑004**, **SC‑002** |
| **9. CI / Testing** | • Run full unit suite (`pytest -q`). <br>• Run integration test (`pytest tests/integration/test_generation.py`). <br>• Benchmark generation of `N=5`, `T=10 000`, 5 trials – must complete < 30 s. <br>• Ensure all schema validations pass. | **All FRs**, **SC‑004**, **I** |
| **10. Documentation** | • Update `quickstart.md`, `README.md`, and all schema files. <br>• Add a short “Design Decisions” section explaining why QR re‑orthonormalisation, Rosenstein baseline, and mixed‑effects with random slope were chosen. | **FR‑001**, **SC‑001**, **VI** |

## Statistical Rigor Checklist
- **Multiple comparisons** – Benjamini‑Hochberg FDR applied to all fixed‑effect coefficients.  
- **Power** – Simulation‑based power analysis (see Research) shows ≈ 1 080 effective observations yield ≥ 80 % power to detect a small‑to‑medium effect (`f²≈0.02`) for the primary `σ_noise` coefficient at α = 0.05.  
- **Causal claim** – All statements are *associational*; no causal inference is claimed.  
- **Measurement validity** – Lorenz parameters are canonical; Rosenstein baseline is a validated method (Constitution VI).  
- **Collinearity** – VIFs will be inspected; interaction terms dropped if VIF > 5.  

## Compute Feasibility (CPU‑First)
- **Memory**: One trajectory (N=5, 15 states, 10 000 steps) ≈ 1.2 MB; full grid ≈ 40 MB.  
- **CPU**: QR‑based FTLE and Rosenstein baseline are lightweight; total wall‑clock ≤ 45 min with 2‑core multiprocessing, satisfying the CI limit.  
- **GPU**: Not required; all methods have faithful CPU implementations.  

## Decision / Rationale (re‑stated)
1. **Synthetic data** – Guarantees full control; no external dataset needed, satisfying data‑availability rule.  
2. **DOP853 + tight tolerances** – Numerical error far below the smallest noise level studied.  
3. **QR re‑orthonormalisation** – Provides stable FTLE estimates for long windows.  
4. **Rosenstein baseline (multiple runs, variance)** – Meets Constitution VI, supplies variance for Δλ, and eliminates algorithmic mismatch.  
5. **Mixed‑effects regression with random slope & baseline variance weighting** – Properly handles hierarchical dependence of overlapping windows and propagates baseline uncertainty.  
6. **Durbin‑Watson + Newey‑West** – Satisfies FR‑009 while addressing autocorrelation; Newey‑West is a fallback when DW detects significance.  
7. **Always‑fit Tobit** – Removes post‑hoc selection bias.  
8. **Parallel trial execution** – Keeps runtime within CI limits while preserving reproducibility (each worker seeded independently).  

---
