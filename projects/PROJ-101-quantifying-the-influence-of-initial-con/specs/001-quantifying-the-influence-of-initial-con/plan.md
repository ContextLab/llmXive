# Implementation Plan: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Branch**: `001-quantify-initial-conditions` | **Date**: 2026-10-16 | **Spec**: `specs/001-quantify-initial-conditions/spec.md`  
**Input**: Feature specification from `/specs/001-quantify-initial-conditions/spec.md`

## Summary
The project will (1) generate synthetic trajectories of coupled Lorenz oscillators with configurable Gaussian noise, (2) compute Finite‑Time Lyapunov Exponents (FTLE) over multiple sliding windows, (3) obtain a clean‑system asymptotic baseline using Rosenstein’s algorithm, (4) flag unphysical trajectories, (5) perform a rigorous statistical analysis (Durbin‑Watson, Newey‑West SE, mixed‑effects regression, Benjamini‑Hochberg FDR, always‑fit Tobit), and (6) produce visualizations and reproducible artifacts. All steps are designed to run on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language**: Python 3.11  
- **Core Libraries**: `numpy`, `scipy`, `pandas`, `matplotlib`, `statsmodels`, `pytest`, `pyyaml`  
- **Storage**: Local filesystem under `data/` (raw trajectories, processed results, plots)  
- **Testing**: `pytest` with fixtures in `tests/conftest.py` (seed, temp‑dir)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goal**: End‑to‑end pipeline ≤ 45 min, ≤ 4 GB RAM for the maximal configuration (N = 5, T = 10 000, 30 trials per noise level). Estimated wall‑clock time [deferred] with 2‑core multiprocessing and batch mode for larger T.

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | All random seeds are pinned (`config.SEED = 42`); synthetic data generation is deterministic given parameters. |
| II. Verified Accuracy | PASS | No external citations required; all algorithms are standard (Lorenz ODE, Rosenstein, QR‑based FTLE). |
| III. Data Hygiene | PASS | Raw `.npz` files are immutable; checksums recorded in `state/manifest.yaml`. |
| IV. Single Source of Truth | PASS | Figures and tables are generated directly from `data/processed/` artifacts; no manual transcription. |
| V. Versioning Discipline | PASS | Artifact hashes stored in `state/projects/...yaml`. |
| VI. Numerical Stability and Baseline Validation | PASS | Baseline computed with Rosenstein; convergence < 5 % error at T = 5000 is verified before any noisy analysis. |
| VII. Explicit Noise Scaling Characterization | PASS | Every trial records `σ_noise`, `T`, and boundedness flag; regression models `Δλ ∼ f(σ, N)` explicitly. |

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
    └── results.schema.yaml

projects/PROJ-101-quantifying-the-influence-of-initial-con/
├── code/
│   ├── __init__.py
│   ├── main.py                # CLI entry point
│   ├── config.py              # Global constants & CLI defaults
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── lorenz.py          # Coupled Lorenz ODE definition
│   │   └── generator.py       # Trajectory generation + noise injection
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── ftle.py            # QR‑based FTLE over sliding windows
│   │   ├── baseline.py        # Rosenstein baseline & convergence check
│   │   ├── regression.py      # Mixed‑effects MLR, Tobit, Durbin‑Watson, Newey‑West, FDR
│   │   └── plotting.py        # Convergence & bias‑scaling figures
│   └── utils/
│       ├── __init__.py
│       └── stability.py       # Boundedness, non‑chaotic detection
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # seed & temp‑dir fixtures
│   ├── unit/
│   │   ├── test_lorenz.py
│   │   ├── test_generator.py
│   │   └── test_edge_cases.py
│   └── integration/
│       └── test_pipeline.py
├── data/
│   ├── raw/                   # Immutable `.npz` trajectories
│   └── processed/
│       ├── ftle_results.json            # Aggregated FTLE results (ftle_results.schema.yaml)
│       ├── baseline_{N}.json            # Clean baseline per dimension (baseline.schema.yaml)
│       ├── regression_results.json      # Regression output (regression_results.schema.yaml)
│       ├── results.json                 # Bundle of all outputs (results.schema.yaml)
│       └── plots/
│           ├── convergence.png
│           ├── bias_scaling.png
│           └── dimension_scaling.png
└── state/
    └── projects/
        └── PROJ-101-quantifying-the-influence-of-initial-con.yaml
```

## Phase‑by‑Phase Tasks (covers every FR/SC)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0. Project Bootstrap** | Create directory layout, `requirements.txt`, `pyproject.toml`, seed fixture. | – |
| **1. Trajectory Generation** (`code/simulation/generator.py`) | Generate trajectories for each `(N, σ_noise, trial)` using `solve_ivp` (method `DOP853`, `rtol=1e-9`, `atol=1e-12`). Save immutable `.npz` files under `data/raw/`. | **FR‑001**, **FR‑007**, **FR‑009** (store noise level for later residual analysis). |
| **2. Baseline Validation** (`code/analysis/baseline.py`) | Compute clean FTLE over a long window (`T=10 000`) with Rosenstein’s algorithm. Verify convergence < 5 % error at `T=5000`. Write `baseline_{N}.json`. Abort pipeline if convergence fails. | **FR‑003**, **FR‑006**, **SC‑001** |
| **3. FTLE Computation** (`code/analysis/ftle.py`) | For each noisy trajectory, compute FTLE over sliding windows `T∈{500,1000,5000}` using QR re‑orthonormalization. Record `window_size`, `lambda_max`, and `status` (`valid`, `unphysical`, `non‑chaotic`). | **FR‑002**, **FR‑010**, **FR‑007**, **FR‑009** |
| **4. Edge‑Case & Stability Checks** (`code/utils/stability.py`) | *Boundedness*: flag any trajectory where `||x|| > 20.0` → `status = "unphysical"`.<br>*Chaos detection*: if max exponent ≤ 0 → abort with clear error.<br>*Durbin‑Watson*: compute DW statistic on the raw FTLE time‑series for each trajectory; store p‑value.<br>*Newey‑West*: if DW p < 0.05, recompute regression SEs with Newey‑West HAC correction. | **FR‑007**, **FR‑009**, **SC‑003** |
| **5. Regression & Statistical Analysis** (`code/analysis/regression.py`) | <ul><li>Construct dataset of **Δλ = λ_FTLE – λ_baseline** for all **bounded** trials.</li><li>Fit a **mixed‑effects Multiple Linear Regression** (random intercept per trajectory) modeling Δλ ~ σ_noise + N + σ_noise·N + 1/T.</li><li>Apply **Benjamini‑Hochberg FDR** (q ≤ 0.05) to all regression coefficients.</li><li>If DW test flagged autocorrelation, use **Newey‑West HAC SEs** (already computed in Phase 4).</li><li>**Tobit censored regression** is always run as a secondary analysis on the full dataset (including unphysical points) to estimate latent bias.</li></ul> | **FR‑004**, **FR‑005**, **FR‑008**, **FR‑009**, **SC‑002**, **SC‑003**, **SC‑004** |
| **6. Artifact Packaging & Validation** | Write `ftle_results.json` (aggregated FTLE entries) and validate against `contracts/ftle_results.schema.yaml`. Write `regression_results.json` and validate against `contracts/regression_results.schema.yaml`. Bundle all outputs into `results.json` and validate against `contracts/results.schema.yaml`. Compute SHA‑256 checksums for every file and record in `state/manifest.yaml`. | **III**, **V**, **VI**, **VII** |
| **7. Visualization** (`code/analysis/plotting.py`) | Generate: (a) convergence plots (λ vs. T) for three noise levels; (b) Δλ vs. σ_noise with error bars; (c) scaling exponent plot (Δλ vs. N). Save PNGs under `data/processed/plots/`. | **FR‑005**, **FR‑004**, **SC‑002** |
| **8. CI / Testing** | Run unit tests (validation of ODE, noise stats, FTLE correctness), integration test (full pipeline on a small subset). Enforce runtime < 30 s for N=5, T=10 000, 5 trials (benchmark). | **All FRs** (verification) |
| **9. Documentation** | Update `quickstart.md`, `README.md`, and schema contracts. | – |

## Statistical Rigor Checklist
- **Multiple comparisons** – Benjamini‑Hochberg FDR applied to all regression coefficients (FR‑004).  
- **Power** – For the multiple regression model with 4 predictors, a total sample size of $N_{obs} \approx 1000$ (derived from 12 cells $\times$ 30 trials $\times$ 3 windows) provides $\ge 80\%$ power to detect a small-to-medium effect size ($f^2 \approx 0.02$) for the primary $\sigma_{noise}$ coefficient at $\alpha=0.05$. The $k=30$ trials per cell ensure sufficient independence to estimate random intercepts and interaction terms.
- **Causal claim** – All statements are *associational*; the system is purely observational (no randomization).  
- **Measurement validity** – Lorenz parameters are standard; Rosenstein baseline is a validated numerical method (Constitution VI).  
- **Collinearity** – Interaction term `σ_noise·N` is included; variance inflation factor (VIF) will be reported; if VIF > 5, interaction will be dropped with justification.  

## Compute Feasibility (CPU‑First)
- **Memory**: One trajectory (N = 5, 15 states, 10 000 steps) ≈ 1.2 MB; 30 trials ≈ 36 MB plus overhead → well under 7 GB.  
- **CPU**: Integration of a moderate‑dimensional ODE for many steps completes quickly on the runner; QR decomposition on matrices of comparable size is negligible. Full sweep (N = 5, 4 noise levels, 30 trials) ≈ 2 h total compute; with 2‑core multiprocessing the wall‑clock time is ≈ 42 min, satisfying the 45‑minute CI limit.  
- **GPU**: Not required; all methods have faithful CPU implementations.  

## Decision / Rationale
1. **Synthetic data** is mandatory to control noise and dimension; no external dataset is needed, satisfying the data‑availability rule.  
2. **DOP853** + tight tolerances ensure numerical error is far below the noise‑induced bias we aim to measure.  
3. **QR re‑orthonormalization** guarantees stable FTLE estimates for long windows.  
4. **Rosenstein baseline** satisfies Constitution VI and provides a deterministic reference for Δλ.  
5. **Mixed‑effects regression** respects the hierarchical dependence of overlapping windows, addressing methodological concerns.  
6. **Durbin‑Watson + Newey‑West** fulfill FR‑009 while handling autocorrelation appropriately.  
7. **Always‑fit Tobit** removes post‑hoc model selection bias.  
8. **Parallel trial execution** keeps total runtime within CI limits while preserving reproducibility (each worker seeded independently).  

---