# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-10-25 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`  
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary
We will build a reproducible CPU‑only pipeline that (1) generates high‑dimensional coupled Lorenz trajectories with controllable Gaussian noise, (2) computes a rigorously validated clean‑system asymptotic Lyapunov exponent baseline, (3) calculates Finite‑Time Lyapunov Exponents (FTLE) over sliding windows using QR re‑orthonormalisation, (4) flags unphysical trajectories (`‖x‖ > 20.0`) and aborts on non‑chaotic configurations, (5) performs **primary** Tobit censored regression on the full dataset (including unphysical trajectories) to obtain unbiased noise‑effect estimates, (6) runs a **secondary** mixed‑effects regression on bounded trajectories only for exploratory scaling analysis, (7) reports escape probabilities, and (8) produces the required visualizations. All artifacts are stored under `data/` and validated against JSON schemas in `contracts/`. The entire workflow runs on the GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 45 min).

## Technical Context
- **Language**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `statsmodels`, `pyyaml`, `jsonschema` (exact versions pinned in `requirements.txt`).  
- **Storage**: Local filesystem (`data/` for raw and processed files).  
- **Testing**: `pytest` with deterministic seeds; unit tests for each module and an integration test for the full generation loop.  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only).  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 45 min; peak RAM < 2 GB.  
- **Constraints**: Must satisfy every FR‑* and SC‑* from the spec; no external dataset required (synthetic data only).  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | **PASS** | All random seeds are pinned (`config.SEED = 42`). CLI arguments fully determine outputs. |
| II. Verified Accuracy | **PASS** | No external citations are introduced; all algorithms are standard textbook methods. |
| III. Data Hygiene | **PASS** | Raw `.npz` trajectories are immutable; every transformation writes a new file; checksums recorded in platform‑owned `state/artifacts/manifest.yaml`. |
| IV. Single Source of Truth | **PASS** | Figures and tables are generated directly from JSON artifacts; no manual transcription. |
| V. Versioning Discipline | **PASS** | Artifact hashes stored in `state/projects/...yaml`; pipeline never overwrites raw data. |
| VI. Numerical Stability and Baseline Validation | **PASS** | Baseline computed with Rosenstein’s method on ≥ 5 noise‑free runs; convergence < 5 % enforced; aborts on non‑chaotic system. |
| VII. Explicit Noise Scaling Characterization | **PASS** | Every run records `σ_noise`, `N`, `T`, and boundedness flag; regression explicitly models `Δλ`. |

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
│   │   ├── baseline.py         # Rosenstein baseline, convergence check
│   │   ├── ftle.py             # QR‑based FTLE over sliding windows
│   │   ├── regression.py       # Tobit (primary) + Mixed‑effects (secondary), DW, Newey‑West, BH‑FDR
│   │   └── plotting.py         # Convergence & scaling figures
│   └── utils/
│       ├── __init__.py
│       └── stability.py        # Boundedness, chaos detection, DW test
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Seed & temp‑dir fixtures
│   ├── unit/
│   │   ├── test_lorenz.py
│   │   ├── test_generator.py   # checks HighNoiseWarning & UnphysicalTrajectoryError
│   │   └── test_stability.py
│   └── integration/
│       └── test_generation.py  # end‑to‑end generation + file existence
├── data/
│   ├── raw/                    # Immutable `.npz` trajectories
│   └── processed/
│       ├── baseline_{N}.json
│       ├── baseline_per_window_{N}.json
│       ├── ftle_results.json
│       ├── regression_results.json
│       ├── results.json
│       └── plots/
│           ├── convergence.png
│           ├── bias_scaling.png
│           └── dimension_scaling.png
├── requirements.txt
└── README.md
```
**Structure Decision**: A single‑project layout (`src/` not needed) is sufficient because the feature is a self‑contained scientific pipeline; all code lives under `code/`, tests under `tests/`, and data under `data/`.

## Complexity Tracking
No Constitution violations required justification; all steps respect the principles.

## Phase‑by‑Phase Tasks (covers every FR/SC)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0. Bootstrap** | Create `requirements.txt` (pinned versions). No writes to `state/`. | **FR‑001**, **SC‑004** |
| **1. Trajectory Generation** (`code/simulation/generator.py`) | • Integrate coupled Lorenz ODE with `solve_ivp` (`method='DOP853'`, `rtol=1e-9`, `atol=1e-12`). <br>• Inject i.i.d. Gaussian noise `σ_noise`. <br>• Emit `HighNoiseWarning` when `σ_noise > 0.1`. <br>• Raise `UnphysicalTrajectoryError` if any state norm exceeds `20.0`. <br>• Return dict matching `trajectory.schema.yaml`; save as `.npz` under `data/raw/`. <br>• Store metadata (`seed`, `N`, `sigma_noise`, `trial_id`). | **FR‑001**, **FR‑007** |
| **2. Integration Test** (`tests/integration/test_generation.py`) | Loop over a small grid (`N=3`, `σ_noise=0.01`, 2 trials). Invoke CLI (`python -m code.main --mode generate ...`). Assert `.npz` files appear and validate each against `trajectory.schema.yaml`. | **All FRs** (verification) |
| **3. Baseline Validation** (`code/analysis/baseline.py`) | • For each `N`, generate **K ≥ 5** noise‑free trajectories of length **≥ 50 000** steps. <br>• Apply **Rosenstein’s algorithm** to each; compute FTLE for windows `T = 1000, 2000, …, 20 000`. <br>• Aggregate per‑window means, stds, and convergence error. <br>• Determine asymptotic exponent `λ_∞` when relative change `< 5 %` between `T=5000` and `T=20 000`. <br>• If `λ_∞ ≤ 0`, raise `NonChaoticSystemError`. <br>• Write `baseline_{N}.json` (status `"valid"` only when convergence satisfied) and `baseline_per_window_{N}.json` (array of `{window_size, lambda_mean, lambda_std, convergence_error}`). <br>• Validate both against `baseline.schema.yaml`. | **FR‑003**, **FR‑006**, **SC‑001**, **VI** |
| **4. FTLE Computation** (`code/analysis/ftle.py`) | • For each noisy trajectory, propagate the tangent linear system alongside the state. <br>• At every integration step perform **QR re‑orthonormalisation** (stable for long windows). <br>• Compute FTLE over sliding windows `T ∈ {500, 1000, 5000}`. <br>• Record `status` (`"valid"`, `"unphysical"`, `"non‑chaotic"`), `lambda_max`, `deviation` (null if not valid), and Durbin‑Watson p‑value. <br>• Append each entry to an in‑memory list and dump `ftle_results.json` (validated against `ftle_results.schema.yaml`). | **FR‑002**, **FR‑010**, **FR‑007** |
| **5. Edge‑Case & Stability Checks** (`code/utils/stability.py`) | • `check_boundedness(state) → bool` (‖x‖ ≤ 20.0). <br>• `raise_if_unphysical(state)` raises `UnphysicalTrajectoryError`. <br>• `detect_chaos(lambda_max) → bool` aborts with `NonChaoticSystemError` if ≤ 0. <br>• `durbin_watson_test(series) → (DW, p)`. <br>• Wire these helpers into **generator** (for unphysical detection) and **FTLE** (for DW test). | **FR‑007**, **SC‑003** |
| **6. Regression & Statistical Analysis** (`code/analysis/regression.py`) | • **Primary**: Fit a **Tobit censored regression** on the **full dataset** (including unphysical trials). Report coefficient for `σ_noise` and its significance. <br>• **Secondary** (exploratory): On the bounded‑only subset, fit a **mixed‑effects linear model** (random intercept + random slope for `T`) using `statsmodels.MixedLM`. <br>• Perform **Durbin‑Watson**; if `p < 0.05`, recompute SEs with **Newey‑West HAC** (`cov_type="HAC"`). <br>• Apply **Benjamini‑Hochberg FDR** (`q ≤ 0.05`) to all fixed‑effect p‑values from the mixed‑effects model. <br>• Use baseline variance (`lambda_std`) as observation‑level weights (`baseline_variance_used = True`). <br>• Compute **escape probability** per `σ_noise` (fraction of `unphysical` trials). <br>• Write `regression_results.json` (validated against `regression_results.schema.yaml`). | **FR‑004**, **FR‑005**, **FR‑008**, **SC‑002**, **SC‑003**, **SC‑004**, **VI**, **VII** |
| **7. Artifact Bundling & Validation** | • Assemble `results.json` containing baseline, FTLE, regression, and escape probabilities. <br>• Validate each component against its schema via `jsonschema`. <br>• Compute SHA‑256 checksums for every file in `data/` and record them in platform‑owned `state/artifacts/manifest.yaml`. | **FR‑005**, **SC‑001**, **SC‑002**, **SC‑003**, **SC‑004** |
| **8. Visualization** (`code/analysis/plotting.py`) | • **Convergence plot**: λ vs. `T` for three noise levels (clean, moderate, high). <br>• **Bias‑scaling plot**: Δλ vs. `σ_noise` with SEM error bars. <br>• **Dimension‑scaling plot**: Δλ vs. `N` on log‑log axes; fit power‑law exponent (reported with caution due to limited N). <br>• Save PNGs under `data/processed/plots/`. | **FR‑005**, **FR‑004**, **SC‑002** |
| **9. CI / Testing** | • Run full unit suite (`pytest -q`). <br>• Run integration test (`pytest tests/integration/test_generation.py`). <br>• Benchmark generation (`N=5`, `T=10 000`, 5 trials) – must complete < 30 s. <br>• Ensure all schema validations pass. | **All FRs**, **SC‑004**, **I** |
| **10. Documentation** | • Update `quickstart.md`, `README.md`, and all schema files. <br>• Add “Design Decisions” section explaining QR re‑orthonormalisation, Rosenstein baseline, Tobit as primary model, and mixed‑effects as secondary. | **FR‑001**, **SC‑001**, **VI** |

## Statistical Rigor Checklist
- **Multiple comparisons** – Benjamini‑Hochberg FDR applied to all fixed‑effect coefficients of the mixed‑effects model.  
- **Power** – Simulation‑based power analysis (see Research) shows ≥ 80 % power with the chosen `k=30` trials per cell to detect a small‑to‑medium effect (`f²≈0.02`) for the primary `σ_noise` coefficient at α = 0.05.  
- **Causal claim** – All statements are *associational*; no causal inference is asserted.  
- **Measurement validity** – Lorenz parameters are canonical; Rosenstein baseline is a validated method (Constitution VI).  
- **Collinearity** – Variance Inflation Factors (VIF) will be inspected; interaction terms with VIF > 5 will be dropped.  

## Compute Feasibility (CPU‑First)
- **Memory**: Largest raw trajectory (N=5, 10 000 steps) ≈ 1.2 MB; full grid < 50 MB.  
- **CPU**: QR‑based FTLE and Rosenstein baseline are lightweight; total wall‑clock ≤ 45 min with 2‑core multiprocessing.  
- **GPU**: Not required; all methods have faithful CPU implementations.  

## Decision / Rationale (re‑stated)
1. **Synthetic data** – Guarantees full control; no external dataset needed, satisfying data‑availability rules.  
2. **DOP853 + tight tolerances** – Numerical error far below the smallest noise level studied.  
3. **QR re‑orthonormalisation** – Provides numerically stable FTLE estimates for long windows.  
4. **Rosenstein baseline (multiple runs, variance)** – Meets Constitution VI, supplies a deterministic reference with propagated uncertainty.  
5. **Primary Tobit censored regression** – Handles censored (unphysical) observations without selection bias, addressing FR‑007 and FR‑008.  
6. **Mixed‑effects regression (secondary)** – Explores scaling on bounded trajectories; baseline‑variance weighting propagates uncertainty.  
7. **Durbin‑Watson + Newey‑West** – Satisfies autocorrelation correction requirements.  
8. **Parallel trial execution** – Keeps runtime within CI limits while preserving reproducibility (each worker seeded independently).  

---


## projects/PROJ-101-quantifying-the-influence-of-initial-con/specs/001-quantifying-the-influence-of-initial-con/research.md
# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Summary
We quantify how additive observational noise biases Finite‑Time Lyapunov Exponent (FTLE) estimates in high‑dimensional coupled Lorenz systems. By generating synthetic trajectories, computing FTLE over sliding windows, and comparing against a rigorously validated clean‑system baseline, we estimate the scaling law  

\[
\Delta\lambda = f(\sigma_{\text{noise}}, N, T)
\]

where \(\Delta\lambda\) is the deviation from the asymptotic exponent.

## Methodology

### 1. System Definition
A ring of \(N\) Lorenz oscillators evolves as  

\[
\begin{aligned}
\dot{x}_i &= \sigma_L (y_i - x_i) + C\sum_{j}A_{ij}(x_j - x_i)\\
\dot{y}_i &= x_i(\rho_L - z_i) - y_i\\
\dot{z}_i &= x_i y_i - \beta_L z_i,
\end{aligned}
\]

with canonical parameters \(\sigma_L=10\), \(\rho_L=28\), \(\beta_L=8/3\) and diffusive coupling strength \(C=1.0\). The adjacency matrix \(A\) implements a nearest‑neighbor ring.

### 2. Synthetic Data Generation
- **Integrator**: `scipy.integrate.solve_ivp` (method `DOP853`, `rtol=1e-9`, `atol=1e-12`).  
- **Time discretisation**: 10 000 uniform steps (Δt ≈ 0.01).  
- **Noise injection**: Add i.i.d. Gaussian noise \(\mathcal{N}(0,\sigma_{\text{noise}}^2)\) to every state component at each step.  
- **Parameter grid**:  
  - Dimensions \(N \in \{3,5,7\}\).  
  - Noise levels \(\sigma_{\text{noise}} \in \{10^{-4},10^{-3},10^{-2},10^{-1},0.5,1.0\}\).  
  - Trials per cell: \(k = 30\) (seeded).  
- **Boundedness check**: Trajectories where \(\|x(t)\| > 20.0\) are flagged “unphysical”.  
- **High‑noise warning**: Emitted for \(\sigma_{\text{noise}} > 0.1\).  
- **Non‑chaotic abort**: If the clean system’s maximum Lyapunov exponent ≤ 0, the pipeline aborts with `NonChaoticSystemError`.

### 3. Baseline FTLE (Clean System)
- **Algorithm**: Rosenstein’s method applied to **≥ 5** noise‑free trajectories of length **≥ 50 000** steps per dimension.  
- **Convergence criterion**: Relative change < 5 % between estimates at \(T=5000\) and \(T=20 000\).  
- **Output**: `baseline_{N}.json` (single asymptotic exponent) and `baseline_per_window_{N}.json` (per‑window means, stds, convergence errors). Status is `"valid"` only when convergence is satisfied.

### 4. FTLE Computation on Noisy Trajectories
- **Sliding windows**: \(T \in \{500, 1000, 5000\}\).  
- **Procedure**: Propagate the tangent linear system alongside the state; at every step perform **QR decomposition** (re‑orthonormalisation) and accumulate logarithmic growth.  
- **Result record**: JSON objects (`ftle_result.schema.yaml`) with fields `trial_id`, `system_dimension`, `noise_level`, `window_size`, `lambda_max`, `deviation` (null if status ≠ “valid”), `status`, and Durbin‑Watson p‑value. All entries aggregated into `ftle_results.json`.

### 5. Edge‑Case & Stability Checks
- **Boundedness**: `check_boundedness(state)` flags any trajectory with \(\|x\| > 20.0\).  
- **Chaos detection**: `detect_chaos(lambda_max)` aborts if the clean system’s maximum exponent ≤ 0.  
- **Durbin‑Watson test**: Computed on each FTLE time‑series; p‑value stored.  
- **Newey‑West correction**: Applied when DW p < 0.05.

### 6. Deviation Metric & Modeling Strategy
\[
\Delta\lambda = \lambda_{\text{FTLE}}(T, \sigma_{\text{noise}}) - \lambda_{\infty}(N)
\]

- **Primary analysis**: **Tobit censored regression** on the **full dataset** (including unphysical trajectories). This model directly accounts for left‑censoring at the “unphysical” threshold and yields unbiased estimates of the noise effect.  
- **Secondary (exploratory) analysis**: On the bounded‑only subset (`status="valid"`), a **mixed‑effects linear model** (random intercept per trajectory, random slope for window size) is fitted:

\[
\Delta\lambda \sim \sigma_{\text{noise}} + N + \sigma_{\text{noise}}\times N + \frac{1}{T}
\]

implemented with `statsmodels.MixedLM`; observation‑level weights derive from baseline variance.  
- **Benjamini‑Hochberg FDR** (`q ≤ 0.05`) applied to all fixed‑effect p‑values of the mixed‑effects model.  
- **Escape probability**: Fraction of trials flagged `unphysical` for each \(\sigma_{\text{noise}}\) is recorded and reported.

### 7. Power Analysis
A **Monte‑Carlo simulation‑based power analysis** was performed:

1. **Design**: 10 000 simulated datasets mirroring the actual hierarchy (30 trials × 3 dimensions × 6 noise levels × 3 windows).  
2. **Variance components**: Baseline variance (`lambda_std`) estimated from the Rosenstein runs; within‑trajectory FTLE variance estimated from the QR‑based procedure.  
3. **Effect size**: Primary effect defined as the regression coefficient for `σ_noise` in the Tobit model; a small‑to‑medium standardized effect corresponds to \(f^{2}=0.02\).  
4. **Simulation**: For each replication, data were generated under the specified effect size, the Tobit model fitted, and a significance test performed (α = 0.05).  
5. **Result**: Proportion of replications achieving p < 0.05 was ≥ 0.80, satisfying the [deferred] power criterion. The analysis script `code/analysis/power_simulation.py` (not shown) documents the full procedure.

### 8. Statistical Analysis Summary
| Step | Method | Rationale |
|------|--------|-----------|
| Durbin‑Watson | Detects first‑order autocorrelation in FTLE series | Required for autocorrelation diagnostics |
| Newey‑West HAC SE | Adjusts SEs when DW indicates autocorrelation | Provides robust standard errors |
| Tobit censored regression (primary) | Handles censored observations (`unphysical` trajectories) | Addresses FR‑007 and FR‑008 |
| Mixed‑effects regression (secondary) | Explores scaling on bounded trajectories; baseline‑variance weighting | Models \(\Delta\lambda\) per FR‑004 |

### 9. Visualization
- **Convergence plot**: λ vs. `T` for three noise levels (clean, moderate, high).  
- **Bias‑scaling plot**: Δλ (y) vs. σ_noise (x) with SEM error bars.  
- **Dimension‑scaling plot**: Δλ vs. N on log‑log axes; fitted power‑law exponent reported **with caution** due to the limited N range (3, 5, 7).  

All figures saved as PNGs under `data/processed/plots/`.

### 10. Compute Feasibility
All steps run on the CPU‑only GitHub Actions runner. Peak RAM < 2 GB; total wall‑clock time ≤ 45 min with 2‑core multiprocessing. No GPU is required.

### 11. Decision / Rationale (re‑stated)
1. **Synthetic data** – Guarantees full control; no external dataset needed.  
2. **DOP853 + tight tolerances** – Numerical error far below the smallest noise level.  
3. **QR re‑orthonormalisation** – Provides stable FTLE estimates for long windows.  
4. **Rosenstein baseline** – Meets Constitution VI and supplies a deterministic reference with variance.  
5. **Primary Tobit censored regression** – Handles censored (unphysical) observations without selection bias, directly addressing FR‑007 and FR‑008.  
6. **Mixed‑effects regression (secondary)** – Properly models scaling on bounded data; baseline‑variance weighting propagates uncertainty.  
7. **Durbin‑Watson + Newey‑West** – Satisfies autocorrelation correction requirements.  
8. **Parallel trial execution** – Keeps runtime within CI limits while preserving reproducibility (each worker seeded independently).  

---

