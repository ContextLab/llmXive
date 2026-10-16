# Quantifying the Influence of Initial Conditions on Chaotic Systems

This project numerically quantifies how Finite-Time Lyapunov Exponents (FTLEs)
deviate from asymptotic predictions in high-dimensional chaotic systems
(coupled Lorenz oscillators) subject to observational noise, and derives the
scaling laws relating the FTLE bias to noise amplitude, system dimension, and
observation window length.

## Overview

The pipeline:

1. Generates synthetic trajectories of coupled Lorenz oscillators with
 injected additive Gaussian noise (`scipy.integrate.solve_ivp`, method
 `DOP853`, `rtol=1e-9`, `atol=1e-12`).
2. Computes a clean-system asymptotic Lyapunov baseline (Rosenstein-style)
 and gates the pipeline on convergence and chaoticity.
3. Sweeps FTLE over sliding windows `T ∈ {500, 1000, 5000}` with QR /
 Gram-Schmidt re-orthonormalisation of tangent vectors.
4. Fits a mixed-effects regression of the deviation
 `Δλ = λ_FTLE − λ_baseline` on `σ_noise`, `N`, their interaction and
 `1/T`, with Benjamini-Hochberg FDR correction, Durbin-Watson
 autocorrelation tests, Newey-West HAC standard errors, and an
 always-fit Tobit censored regression.
5. Produces convergence, bias-scaling, and dimension-scaling figures and a
 final scientific report.

## Environment Setup

Requirements: Python 3.11+, `git`, `pip`.

```bash
git clone <REPO_URL>
cd projects/PROJ-101-quantifying-the-influence-of-initial-con
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate
pip install -r requirements.txt
```

Verify the installation by running the test suite:

```bash
pytest -q
```

## Step 1 – Generate trajectories

Generate raw trajectories for a set of system dimensions and noise levels.
Each `(N, σ_noise, trial)` combination is integrated with `DOP853`
(`rtol=1e-9`, `atol=1e-12`) and saved as an immutable `.npz` file under
`data/raw/trajectory_N{N}_sigma{sigma}_trial{t}.npz`. Noise levels are
capped at the specification maximum `σ ≤ 1.0`, and the trial count is
`k = 50` for `σ_noise < 0.01` and `k = 30` otherwise (unless overridden
with `--trials`).

```bash
python code/main.py --mode generate \
 --N-values 3,5 \
 --noise-levels 0.0001,0.001,0.01,0.05,0.1,0.2,0.5,0.8,1.0 \
 --seed 42
```

Trajectories whose state norm exceeds 20.0 are flagged as unphysical
(`UnphysicalTrajectoryError`) and excluded; noise levels above 0.1 emit a
`HighNoiseWarning`.

## Step 2 – Compute baseline

Compute the asymptotic Lyapunov exponent for the clean (noise-free)
coupled system using a Rosenstein-style algorithm on a long trajectory
(≥ 50,000 steps). Convergence is declared when the relative change between
successive estimates at `T = 5000` is below 5 %. The result is written to
`data/processed/baseline_{N}.json` (schema `baseline.schema.yaml`).

```bash
python code/main.py --mode analyze
```

The pipeline gates on this step: if the baseline JSON does not have
`status == "valid"` or if `lambda_max ≤ 0` (non-chaotic regime, e.g.
`ρ = 20`), the run aborts with a clear error message and exit code 1
before any noisy FTLE computation is launched.

## Step 3 – FTLE sweep

For every raw trajectory, the FTLE module propagates the tangent linear
model with QR / Gram-Schmidt re-orthonormalisation and evaluates the FTLE
over sliding windows `T ∈ {500, 1000, 5000}`, enforcing the strict
constraint `T < total_length − 10`. Each result records `window_size`,
`lambda_max`, and a `status` flag (`valid`, `unphysical`, `non-chaotic`).
Aggregated results are written to `data/processed/ftle_results.json`
(schema `ftle_results.schema.yaml`).

```bash
python code/analysis/ftle.py \
 --trajectory data/raw/trajectory_N3_sigma0.01_trial0.npz \
 --baseline data/processed/baseline_3.json \
 --output data/processed/ftle_results.json
```

## Step 4 – Regression analysis

The regression module merges `ftle_results.json` with the per-window
clean baseline, computes the deviation `Δλ = λ_FTLE − λ_baseline` for
every bounded trial, and fits the mixed-effects model

```
Δλ ~ σ_noise + N + σ_noise·N + 1/T + (1|trial_id)
```

using `statsmodels`, with:

- Benjamini-Hochberg FDR correction (`q ≤ 0.05`) on all coefficients,
- Durbin-Watson tests on the FTLE time-series and Newey-West HAC
 standard errors when autocorrelation is detected (`p < 0.05`),
- an always-fit Tobit censored regression on the full dataset
 (including unphysical points) to estimate the latent bias,
- the escape probability (fraction of trials with `‖x‖ > 20.0`) as a
 function of `σ_noise`.

Outputs: `data/processed/regression_results.json` and the consolidated
bundle `data/processed/results.json`.

```bash
python code/analysis/regression.py
```

## Step 5 – Visualisation

Generate the three publication figures:

1. **Convergence plot** — FTLE λ vs. window size T for σ = 0, 0.01, 0.1
 (`data/processed/plots/convergence.png`).
2. **Bias-scaling plot** — Δλ vs. σ_noise with SEM error bars
 (`data/processed/plots/bias_scaling.png`).
3. **Dimension-scaling plot** — Δλ vs. N, annotated with the fitted
 scaling exponent (`data/processed/plots/dimension_scaling.png`).

```bash
python code/analysis/plotting.py
```

## Step 6 – Final report

The final scientific report `data/processed/final_report.md` summarises:

1. **Convergence validation (SC-001)** — baseline convergence statistics.
2. **Bias-scaling relationship (SC-002)** — regression coefficients,
 scaling law, and plots.
3. **Statistical significance (SC-003)** — p-values, effect sizes, and
 FDR-adjusted q-values.
4. **Dimension scaling** — the exponent linking system dimension to bias
 magnitude.

## Full pipeline (one command)

```bash
python code/main.py --mode full \
 --N-values 3,5 \
 --noise-levels 0.0001,0.001,0.01,0.1 \
 --trials 30 \
 --window-sizes 500,1000,5000 \
 --seed 42
```

See `quickstart.md` for the complete run-book, CLI reference, and
alternative modes (generate-only, analyze-only, benchmark, tobit-only).

## Output artifacts

| Path | Description |
|------|-------------|
| `data/raw/` | Immutable `.npz` trajectories |
| `data/processed/baseline_{N}.json` | Clean asymptotic baselines |
| `data/processed/baseline_per_window_{N}.json` | Per-window clean baselines |
| `data/processed/ftle_results.json` | Aggregated FTLE estimates with status flags |
| `data/processed/regression_results.json` | Regression coefficients, p-values, q-values |
| `data/processed/results.json` | Consolidated results bundle (incl. escape probabilities) |
| `data/processed/plots/` | Convergence, bias-scaling, dimension-scaling PNGs |
| `data/processed/final_report.md` | Final scientific report |

## Reproducibility

All random seeds are pinned (default seed 42, derived deterministically per
`(N, σ, trial)`); every result file can be regenerated by re-running the
commands above in order. Success criteria: clean FTLE converges to the
baseline within 5 % at `T = 5000` (SC-001); monotonic bias scaling with
noise for bounded trajectories (SC-002); significant σ_noise coefficient
after FDR correction (SC-003); full pipeline completes within 45 minutes
(SC-004).