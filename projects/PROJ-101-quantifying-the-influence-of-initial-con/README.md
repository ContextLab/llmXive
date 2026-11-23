# Quantifying the Influence of Initial Conditions on Chaotic Systems

This repository provides a reproducible pipeline for generating synthetic chaotic trajectories, computing finite‑time Lyapunov exponents (FTLE), establishing clean‑system baselines, performing statistical analysis, and producing the final figures and report.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Step 1 – Generate trajectories](#step-1--generate-trajectories)
3. [Step 2 – Compute baseline](#step-2--compute-baseline)
4. [Step 3 – FTLE sweep](#step-3--ftle-sweep)
5. [Step 4 – Statistical analysis](#step-4--statistical-analysis)
6. [Step 5 – Figures](#step-5--figures)
7. [Full pipeline command](#full-pipeline-command)
8. [Validation](#validation)

## Environment Setup

```bash
# Clone the repository
git clone <REPO_URL>
cd projects/PROJ-101-quantifying-the-influence-of-initial-con

# Create a virtual environment
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

The project relies only on the standard scientific Python stack (`numpy`, `scipy`, `pandas`, `matplotlib`, `statsmodels`, `seaborn`, `pytest`, `PyYAML`, `jsonschema`). No external data files are required – all trajectories are generated synthetically.

## Step 1 – Generate trajectories

The trajectory generator integrates a coupled Lorenz system using `scipy.integrate.solve_ivp` with the **DOP853** method (`rtol=1e-9`, `atol=1e-12`). Additive Gaussian noise of standard deviation `σ_noise` is injected at each time step.

```bash
python -m code.main --mode generate \
 --N-values 3,5,7 \
 --noise-levels 0.0001,0.001,0.01,0.05,0.1,0.2,0.5,0.8,1.0 \
 --trials 30 \
 --seed 42
```

This command writes immutable `.npz` files to `data/raw/` with the naming pattern:

```
data/raw/trajectory_N{N}_sigma{σ}_trial{t}.npz
```

*High‑noise warnings* are emitted for `σ_noise > 0.1`; trajectories where any state norm exceeds `20.0` raise `UnphysicalTrajectoryError` and are skipped.

## Step 2 – Compute baseline

For each system dimension `N`, the pipeline generates ≥ 5 noise‑free trajectories of length ≥ 50 000 steps and computes the asymptotic Lyapunov exponent using Rosenstein’s method. The baseline is considered **valid** only when:

- Relative error between the estimates at `T=5000` and `T=20 000` ≤ 1 %
- 95 % confidence‑interval width ≤ 0.01

The results are written to:

- `data/processed/baseline_{N}.json` (single asymptotic exponent, `status: "valid"`)
- `data/processed/baseline_per_window_{N}.json` (array of per‑window statistics)

```bash
python -m code.main --mode analyze --step baseline --N-values 3,5,7
```

## Step 3 – FTLE sweep

Using the clean baseline, the FTLE module propagates the tangent linear system alongside each trajectory, performs QR re‑orthonormalisation at every integration step, and evaluates FTLE over sliding windows `T ∈ {500, 1000, 5000}` (ensuring `T < total_length – 10`). Results are aggregated into:

- `data/processed/ftle_results.json` (conforms to `contracts/ftle_results.schema.yaml`)

```bash
python -m code.main --mode analyze --step ftle --window-sizes 500,1000,5000
```

## Step 4 – Statistical analysis

The regression module merges FTLE results with the per‑window baseline, computes the deviation Δλ, and fits:

1. **Primary** Tobit censored regression on the full dataset (including unphysical trials)
2. **Secondary** mixed‑effects linear model on the bounded‑only subset

The analysis also:

- Computes Pearson correlation between `|Δλ|` and `σ_noise` (asserting `r ≥ 0.8, p < 0.05`)
- Applies Benjamini‑Hochberg FDR correction (`q ≤ 0.05`) to fixed‑effect p‑values
- Performs Durbin‑Watson tests and, when autocorrelation is detected, recomputes standard errors with Newey‑West HAC
- Uses baseline variance as observation‑level weights
- Records escape probability per noise level

Outputs:

- `data/processed/regression_results.json`
- `data/processed/regression_stats.json`
- Updated `data/processed/results.json` (bundles all artifacts)

```bash
python -m code.main --mode analyze --step regression
```

## Step 5 – Figures

The plotting module creates three PNG figures under `data/processed/plots/`:

1. **Convergence plot** – λ vs. window size `T` for σ = 0, 0.01, 0.1
2. **Bias‑scaling plot** – Δλ vs. σ_noise with SEM error bars
3. **Dimension‑scaling plot** – Δλ vs. system dimension `N` (log‑log) with fitted power‑law exponent

```bash
python -m code.main --mode analyze --step plotting
```

The figures are:

- `data/processed/plots/convergence.png`
- `data/processed/plots/bias_scaling.png`
- `data/processed/plots/dimension_scaling.png`

## Full pipeline command

The following single command runs **all** steps in the correct order, respecting gating logic and parallelisation:

```bash
python -m code.main run-all \
 --N-values 3,5,7 \
 --noise-levels 0.0001,0.001,0.01,0.05,0.1,0.2,0.5,0.8,1.0 \
 --trials 30 \
 --window-sizes 500,1000,5000 \
 --seed 42
```

This will:

1. Generate trajectories (`data/raw/…`)
2. Compute clean baselines (`data/processed/baseline_*.json`)
3. Perform FTLE sweeps (`ftle_results.json`)
4. Run regression and statistical checks (`regression_results.json`, `regression_stats.json`)
5. Produce the three summary figures (`plots/…`)
6. Assemble `data/processed/results.json` bundling all artifacts

## Validation

After a successful run, verify everything with the built‑in validator:

```bash
python -m code.utils.validate --check-all
```

The validator checks:

- SHA‑256 checksums (`state/artifacts/manifest.yaml`)
- Baseline convergence criteria
- JSON schema compliance for `ftle_results.json`, `regression_results.json`, and `results.json`

Any failure aborts with a non‑zero exit status, causing CI to fail.