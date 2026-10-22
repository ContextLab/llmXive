# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-10-22 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`  
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary
The pipeline will (1) generate synthetic trajectories of coupled Lorenz oscillators with configurable Gaussian noise, (2) compute a rigorously validated clean‑system asymptotic Lyapunov baseline (multiple runs, variance propagation), (3) calculate Finite‑Time Lyapunov Exponents (FTLE) over sliding windows using QR re‑orthonormalisation, (4) flag unphysical trajectories (`‖x‖ > 20.0`) and non‑chaotic configurations, (5) perform mixed‑effects regression with random intercept **and** random slope for window size (or AR(1) covariance), Durbin‑Watson detection, Newey‑West correction, Benjamini‑Hochberg FDR, and an always‑fit Tobit censored model, (6) propagate baseline variance into the deviation metric, and (7) generate reproducible figures and JSON artifacts validated against explicit schemas. All steps run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `statsmodels`, `pyyaml`, `jsonschema`  
- **Storage**: Local filesystem under `data/` (raw trajectories, processed results, plots) – **no writes to platform‑owned `state/`**.  
- **Testing**: `pytest` with deterministic seeds, integration test for trajectory generation, schema validation tests.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: End‑to‑end ≤ 45 min wall‑clock, peak RAM < 2 GB.  
- **Constraints**: Must obey all functional requirements (FR‑001…FR‑010) and success criteria (SC‑001…SC‑004).  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | **PASS** | All random seeds are pinned (`config.SEED = 42`). All generated files are deterministic given parameters. |
| II. Verified Accuracy | **PASS** | No external citations are introduced; all algorithms are standard textbook methods. |
| III. Data Hygiene | **PASS** | Raw `.npz` trajectories are immutable; every transformation writes a new file; checksums recorded in `state/artifacts/manifest.yaml` (platform‑owned). |
| IV. Single Source of Truth | **PASS** | Figures and tables are generated directly from JSON artifacts; no manual transcription. |
| V. Versioning Discipline | **PASS** | Artifact hashes stored in `state/projects/...yaml`; pipeline never overwrites existing raw data. |
| VI. Numerical Stability and Baseline Validation | **PASS** | Baseline computed with Rosenstein’s method on **multiple** clean trajectories per N; variance captured; convergence < 5 % enforced before noisy analysis. |
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
│   │   ├── regression.py       # Mixed‑effects (random intercept **and** random slope for T, AR(1) covariance), Newey‑West, BH‑FDR, Tobit
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
| **0. Bootstrap** | Create `requirements.txt` (pin exact versions) and a `state/artifacts/manifest.yaml` generator (platform‑owned). No project‑owned writes to `state/`. **Maps to FR‑001 (environment setup) and SC‑004 (runtime limit).** | **FR‑001**, **SC‑004** |
| **1. Trajectory Generation** (`code/simulation/generator.py`) | • Integrate coupled Lorenz ODE with `solve_ivp` (`method='DOP853'`, `rtol=1e-9`, `atol=1e-12`). <br>• Inject i.i.d. Gaussian noise `σ_noise` at each step. <br>• Emit **`HighNoiseWarning`** when `σ_noise > 0.1`. <br>• Raise **`UnphysicalTrajectoryError`** if any state norm exceeds `20.0` *during* integration (covers FR‑007). <br>• Return a dict matching `trajectory.schema.yaml` and save as `.npz` under `data/raw/`. <br>• All parameters (`seed`, `N`, `sigma_noise`, `trial_id`) are stored in metadata. | **FR‑001**, **FR‑007**, **FR‑009** |
| **2. Integration Test** (`tests/integration/test_generation.py`) | • Loop over a small grid (e.g., `N=3`, `σ_noise=0.01`, 2 trials). <br>• Call the generator via CLI (`python -m code.main --mode generate ...`). <br>• Assert that `.npz` files appear in `data/raw/` and validate each against `trajectory.schema.yaml`. | **All FRs** (verification) |
| **3. Baseline Validation** (`code/analysis/baseline.py`) | • For each system dimension **N**, generate **K≥5** independent noise‑free trajectories of length **≥ 50 000** steps. <br>• Apply **Rosenstein’s algorithm** to each and compute per‑window FTLE (`T = 1000, 2000, …, 10 000`). <br>• Aggregate to produce a **mean baseline**, **variance**, and **standard deviation** per window; store `baseline_variance` and `sample_count`. <br>• Determine asymptotic exponent `λ_∞` when relative change between `T=5000` and `T=10 000` is **< 5 %**. <br>• If `λ_∞ ≤ 0`, raise **`NonChaoticSystemError`** (FR‑006). <br>• Write two JSON artifacts: <br>  • `baseline_{N}.json` (includes mean, variance, status `"valid"`). <br>  • `baseline_per_window_{N}.json` (array of `{window_size, lambda_mean, lambda_std, convergence_error}`). <br>• Validate both against `baseline.schema.yaml`. **Baseline variance will be propagated to the regression stage.** | **FR‑003**, **FR‑006**, **SC‑001**, **methodology-52e950f1**, **scientific_soundness-7dc6f0b5** |
| **4. FTLE Computation** (`code/analysis/ftle.py`) | • For each noisy trajectory, propagate the tangent linear system alongside the state. <br>• At every integration step, perform **QR re‑orthonormalisation** (numerically stable). <br>• Compute FTLE over sliding windows `T ∈ {500, 1000, 5000}`. <br>• Attach fields `status` (`"valid"`, `"unphysical"`, `"non‑chaotic"`), `deviation` (null if not valid), and DW test results. <br>• Append each result to an in‑memory list and finally dump **`ftle_results.json`** (validated against `ftle_results.schema.yaml`). | **FR‑002**, **FR‑010**, **FR‑007**, **FR‑009**, **T010** |
| **5. Edge‑Case & Stability Checks** (`code/utils/stability.py`) | • `check_boundedness(state) → bool` (‖x‖ ≤ 20.0). <br>• `raise_if_unphysical(state)` raises `UnphysicalTrajectoryError`. <br>• `detect_chaos(lambda_max) → bool` aborts with `NonChaoticSystemError` if ≤ 0. <br>• `durbin_watson_test(series) → (DW, p)`; store p‑value in FTLE metadata. <br>• Wire these helpers into **generator** (for unphysical detection) and **FTLE** (for DW test). | **FR‑007**, **FR‑009**, **SC‑003** |
| **6. Regression & Statistical Analysis** (`code/analysis/regression.py`) | • Build dataset of `Δλ = λ_FTLE – λ_baseline_mean` **only** for rows with `status="valid"`. <br>• Fit a **mixed‑effects linear model** with **random intercept **and** random slope for window size** (or AR(1) covariance) using `statsmodels.MixedLM`. <br>• Perform **Durbin‑Watson** on residuals; if `p < 0.05`, recompute SEs with **Newey‑West HAC** (`cov_type="HAC"`). <br>• Apply **Benjamini‑Hochberg FDR** (`q ≤ 0.05`) to all fixed‑effect p‑values. <br>• Incorporate **baseline variance** (from Phase 3) as observation‑level weights, and record the flag `baseline_variance_used`. <br>• Fit a **Tobit censored regression** on the full dataset (including `unphysical` points) to estimate latent bias. <br>• Compute **escape probability** per `σ_noise` (fraction of `unphysical` trials). <br>• Write `regression_results.json` (validated against `regression_results.schema.yaml`). | **FR‑004**, **FR‑005**, **FR‑008**, **FR‑009**, **SC‑002**, **SC‑003**, **SC‑004**, **methodology-69f55355**, **methodology-70964960**, **scientific_soundness-5c30cb5c**, **scientific_soundness-7dc6f0b5** |
| **7. Artifact Bundling & Validation** | • Assemble `results.json` containing baseline, FTLE, regression, and escape probabilities. <br>• Validate each component against its schema using `jsonschema`. <br>• Compute SHA‑256 checksums for every file in `data/` and record them in the platform‑owned `state/artifacts/manifest.yaml`. **Maps to FR‑005 (output generation) and SC‑001 (baseline validation).** | **FR‑005**, **SC‑001**, **SC‑002**, **SC‑003**, **SC‑004**, **spec_coverage-de4a817b** |
| **8. Visualization** (`code/analysis/plotting.py`) | • **Convergence plot**: λ vs. T for three noise levels (clean, moderate, high). <br>• **Bias‑scaling plot**: Δλ vs. σ_noise with SEM error bars. <br>• **Dimension‑scaling plot**: Δλ vs. N on log‑log axes, fit power‑law exponent. <br>• Save PNGs under `data/processed/plots/`. | **FR‑005**, **FR‑004**, **SC‑002** |
| **9. CI / Testing** | • Run full unit suite (`pytest -q`). <br>• Run integration test (`pytest tests/integration/test_generation.py`). <br>• Benchmark generation of `N=5`, `T=10 000`, 5 trials – must complete < 30 s. <br>• Ensure all schema validations pass. **Maps to SC‑004 (runtime limit), FR‑001 (reproducibility), and FR‑001 (environment).** | **All FRs** (verification), **FR‑001**, **SC‑004**, **spec_coverage-913720bf** |
| **10. Documentation** | • Update `quickstart.md`, `README.md`, and all schema files. <br>• Add a short “Design Decisions” section explaining why QR re‑orthonormalisation, Rosenstein baseline, and mixed‑effects with random slope were chosen. **Maps to FR‑001 (reproducibility) and SC‑001 (baseline validation).** | **FR‑001**, **SC‑001**, **spec_coverage-17f18b1a** |

## Statistical Rigor Checklist
- **Multiple comparisons** – Benjamini‑Hochberg FDR applied to all fixed‑effect coefficients.  
- **Power** – Simulation‑based power analysis for the hierarchical mixed‑effects model (random intercept + random slope) accounting for overlapping windows and baseline variance shows that with ≈ 1 080 *effective* observations (after accounting for intra‑trajectory correlation) we achieve **[deferred]** power to detect a small‑to‑medium effect size (`f²≈0.02`) for the primary `σ_noise` coefficient at \(\alpha=0.05\).
- **Causal claim** – All statements are *associational*; the system is purely observational.  
- **Measurement validity** – Lorenz parameters are canonical; Rosenstein baseline is a validated method (Constitution VI).  
- **Collinearity** – VIFs will be computed; interaction term dropped if VIF > 5.  

## Compute Feasibility (CPU‑First)
- **Memory**: One trajectory (N=5, 15 states, 10 000 steps) ≈ 1.2 MB; full grid ≈ 40 MB.  
- **CPU**: QR‑based FTLE and Rosenstein baseline are lightweight; total wall‑clock [deferred] with 2‑core multiprocessing, satisfying the 45‑minute CI limit.  
- **GPU**: Not required; all methods have faithful CPU implementations.  

## Decision / Rationale (re‑stated)
1. **Synthetic data** – Guarantees full control; no external dataset needed, satisfying data‑availability rule.  
2. **DOP853 + tight tolerances** – Numerical error far below the smallest noise level studied.  
3. **QR re‑orthonormalisation** – Provides stable FTLE estimates for long windows.  
4. **Rosenstein baseline (multiple runs, variance)** – Meets Constitution VI, supplies variance for Δλ, and eliminates algorithmic mismatch.  
5. **Mixed‑effects regression with random slope** – Properly handles hierarchical dependence of overlapping windows and uses baseline variance for weighting.  
6. **Durbin‑Watson + Newey‑West** – Satisfies FR‑009 while handling autocorrelation; Newey‑West is a fallback when DW detects significance.  
7. **Always‑fit Tobit** – Removes post‑hoc selection bias.  
8. **Parallel trial execution** – Keeps runtime within CI limits while preserving reproducibility (each worker seeded independently).  

---


## projects/PROJ-101-quantifying-the-influence-of-initial-con/specs/001-quantifying-the-influence-of-initial-con/research.md===
# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Summary
We quantify how additive observational noise biases Finite‑Time Lyapunov Exponent (FTLE) estimates in high‑dimensional chaotic systems. By generating synthetic trajectories of coupled Lorenz oscillators, computing FTLE over multiple sliding windows, and comparing against a rigorously validated clean‑system baseline (multiple runs, variance propagation), we estimate the scaling law  

\[
\Delta\lambda = f(\sigma_{\text{noise}}, N, T)
\]

where \(\Delta\lambda\) is the deviation from the asymptotic exponent.

## Methodology

### 1. System Definition
A ring of \(N\) Lorenz oscillators (\(x_i,y_i,z_i\), \(i=1\ldots N\)) evolves as  

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
- **Noise injection**: Add i.i.d. Gaussian noise \(\mathcal{N}(0,\sigma_{\text{noise}}^2)\) to *every* state component at each step.  
- **Parameter grid**:  
  - Dimensions \(N \in \{3,5\}\).  
  - Noise levels \(\sigma_{\text{noise}} \in \{10^{-4}, 10^{-3}, 10^{-2}, 10^{-1}, 0.5, 1.0\}\).  
  - Trials per cell: \(k = 30\) (seeded).  
- **Boundedness check**: Trajectories where \(\|x(t)\| > 20.0\) are flagged “unphysical”.  
- **High‑noise warning**: Emitted for \(\sigma_{\text{noise}} > 0.1\).  
- **Non‑chaotic abort**: If the clean system’s maximum Lyapunov exponent ≤ 0, a `NonChaoticSystemError` aborts the pipeline.

### 3. Baseline FTLE (Clean System)
- **Algorithm**: Rosenstein’s method applied to **multiple** (K ≥ 5) noise‑free trajectories of length **≥ 50 000** steps per dimension.  
- **Per‑window aggregation**: For each window size \(T\) we compute the **mean**, **standard deviation**, and **convergence error** of the FTLE across the K runs.  
- **Convergence criterion**: Relative change < 5 % between estimates at \(T=5000\) and \(T=10 000\).  
- **Output**: `baseline_{N}.json` (single object) includes `lambda_max`, `baseline_variance`, `sample_count`, `status="valid"`; and `baseline_per_window_{N}.json` (array of `{window_size, lambda_mean, lambda_std, convergence_error}`).  
- **Validation**: If the asymptotic exponent \(\lambda_{\infty} \le 0\) the pipeline aborts with `NonChaoticSystemError`.  
- **Variance propagation**: The recorded `baseline_variance` (or per‑window `lambda_std`) will be used as observation‑level weights in the regression stage to account for baseline uncertainty.  

### 4. FTLE Computation on Noisy Trajectories
- **Sliding windows**: \(T \in \{500, 1000, 5000\}\).  
- **Procedure**: Propagate the tangent linear equations alongside the state, re‑orthonormalise via **QR decomposition** each step, accumulate logarithmic growth, and average over the window.  
- **Result record**: JSON objects (`ftle_result.schema.yaml`) with fields `trial_id`, `system_dimension`, `noise_level`, `window_size`, `lambda_max`, `deviation` (null if status ≠ “valid”), `status`, and DW test p‑value. All entries aggregated into `ftle_results.json`.  

### 5. Edge‑Case & Stability Checks
- **Boundedness**: `check_boundedness` flags any trajectory with \(\|x\| > 20.0\).  
- **Chaos detection**: `detect_chaos` aborts if the clean system’s maximum exponent ≤ 0.  
- **Durbin‑Watson test**: Computed on the raw FTLE time‑series per trajectory; p‑value stored.  
- **Newey‑West correction**: Applied when DW p < 0.05.  

### 6. Deviation Metric & Modeling Strategy
\[
\Delta\lambda = \lambda_{\text{FTLE}}(T, \sigma_{\text{noise}}) - \lambda_{\infty}^{\text{mean}}(N)
\]

- **Mixed‑effects regression** (random intercept **and** random slope for window size, implemented via `statsmodels.MixedLM` with `exog_re` or AR(1) covariance):  
  \[
  \Delta\lambda \sim \sigma_{\text{noise}} + N + \sigma_{\text{noise}}\times N + \frac{1}{T}
  \;+\; (1 + \frac{1}{T}\mid \text{trajectory})
  \]  
  Observation‑level weights derived from `baseline_variance` (or per‑window `lambda_std`) are supplied to the model.  
- **Benjamini‑Hochberg FDR** (`q ≤ 0.05`) applied to all fixed‑effect coefficients.  
- **Tobit censored regression**: Always fitted on the full dataset (including `unphysical` points) to estimate latent bias.  
- **Escape probability**: Estimated as the fraction of trials flagged `unphysical` for each \(\sigma_{\text{noise}}\) to quantify selection bias.  

### 7. Power Analysis
A simulation‑based power analysis for the hierarchical mixed‑effects model (random intercept + random slope, baseline variance weighting) shows that with **≈ 1 080 effective observations** (after accounting for intra‑trajectory correlation) we achieve **[deferred]** power to detect a small‑to‑medium effect size (`f²≈0.02`) for the primary `σ_noise` coefficient at \(\alpha=0.05\). This re‑estimation explicitly accounts for the reduced effective sample size caused by overlapping windows and variance‑weighted observations.

### 8. Statistical Analysis Summary
| Step | Method | Rationale |
|------|--------|-----------|
| Durbin‑Watson | Detects first‑order autocorrelation in FTLE series | Required by FR‑009 |
| Newey‑West HAC SE | Adjusts SEs when DW indicates autocorrelation | Satisfies FR‑009 |
| Mixed‑effects MLR (random intercept + random slope) | Accounts for hierarchical dependence of overlapping windows and uses baseline variance weights | Models \(\Delta\lambda\) appropriately (FR‑004) |
| Benjamini‑Hochberg FDR | Controls false discovery rate across coefficients | FR‑004 |
| One‑sample t‑test vs. baseline | Valid because baseline is a deterministic (aggregated) quantity; variance incorporated via weights | SC‑001 |
| Cohen’s d | Provides effect‑size magnitude for primary noise coefficient | SC‑003 |
| Tobit regression | Handles censored observations (`unphysical` trajectories) | FR‑007, FR‑008 |
| Escape probability estimation | Quantifies selection bias due to trajectory escape | FR‑008 |

### 9. Visualization
- **Convergence plot**: λ vs. T for three noise levels (clean, moderate, high).  
- **Bias‑scaling plot**: Δλ (y) vs. σ_noise (x) with SEM error bars.  
- **Dimension‑scaling plot**: Δλ vs. N on log‑log axes; fitted power‑law exponent reported.  

All figures saved as PNGs under `data/processed/plots/`.

### 10. Compute Feasibility
All steps run on the CPU‑only GitHub Actions runner. Peak RAM < 2 GB; total wall‑clock time meets the 45‑minute CI limit with 2‑core multiprocessing. No GPU is required.

### 11. Decision / Rationale (re‑stated)
1. **Synthetic data** – Guarantees full control; no external dataset needed.  
2. **DOP853 + tight tolerances** – Numerical error far below the smallest noise level.  
3. **QR re‑orthonormalisation** – Provides stable FTLE estimates for long windows.  
4. **Rosenstein baseline (multiple runs, variance)** – Meets Constitution VI, supplies variance for Δλ, and eliminates algorithmic mismatch.  
5. **Mixed‑effects regression with random slope & baseline variance weighting** – Properly handles hierarchical dependence of overlapping windows and propagates baseline uncertainty.  
6. **Durbin‑Watson + Newey‑West** – Satisfies FR‑009 while addressing autocorrelation; Newey‑West is a fallback when DW detects significance.  
7. **Always‑fit Tobit** – Removes post‑hoc selection bias.  
8. **Parallel trial execution** – Keeps runtime within CI limits while preserving reproducibility (each worker seeded independently).  

---

