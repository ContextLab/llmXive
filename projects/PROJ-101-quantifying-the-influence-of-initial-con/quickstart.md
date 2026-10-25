# Quickstart: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Prerequisites

- Python 3.11 or newer
- `git` and `pip` (preferably inside a virtual environment)

## Installation

```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd projects/PROJ-101-quantifying-the-influence-of-initial-con

# 2️⃣ Create a virtual environment
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Verify the Test Suite

```bash
pytest -q
# All tests should pass on the CI runner. [UNRESOLVED-CLAIM: c_95f4e2fd — status=not_enough_info]
```

## Running the Full Pipeline

The command‑line entry point is `code/main.py`. It accepts the following key arguments (all other parameters have sensible defaults):

| CLI flag | Meaning |
|-----------------|---------|
| `--N-values` | Comma‑separated list of system dimensions (number of coupled Lorenz oscillators). Example: `3,5,7` |
| `--noise-levels`| Comma‑separated list of Gaussian noise standard deviations (`σ_noise`). Example: `0.0001,0.001,0.01,0.1` |
| `--trials` | Number of independent trials per configuration (default = 30). |
| `--window-sizes`| Sliding‑window lengths for FTLE (default = `500,1000,5000`). |
| `--seed` | Global random seed for reproducibility (default = 42). |

### Minimal “run‑the‑pipeline” example

```bash
python -m code.main run-all \
 --N-values 3,5,7 \
 --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0 \
 --trials 30 \
 --window-sizes 500,1000,5000 \
 --seed 42
```

This single command performs the complete workflow:

1. **Trajectory generation** – raw `.npz` files are written to `data/raw/`.
2. **Baseline validation** – creates `data/processed/baseline_{N}.json` and per‑window baseline files.
3. **FTLE computation** – evaluates FTLE for each trajectory and window size.
4. **Statistical analysis** – runs the mixed‑effects and Tobit regressions, Durbin‑Watson tests, Newey‑West corrections, and Benjamini‑Hochberg FDR adjustments.
5. **Visualization** – PNG figures are saved under `data/processed/plots/`.
6. **Artifact packaging** – JSON results (`ftle_results.json`, `regression_results.json`, `results.json`) are written and validated against the contracts.

## Alternative Modes

| Mode | Description | Command |
|--------------------|-----------------------------------------------|---------|
| **Generation only**| Produce raw trajectories without downstream analysis. | `python -m code.main generate --N-values 5 --noise-levels 0.01,0.1 --trials 10` |
| **Analysis only** | Run baseline, FTLE, and regression on existing raw data. | `python -m code.main analyze` |
| **Benchmark** | Quick benchmark (e.g., 5 trials per config) to verify runtime limits. | `python -m code.main benchmark --trials 5` |
| **Tobit only** | Execute only the censored regression step. | `python -m code.main tobit` |

## Output Overview

- `data/raw/` – Immutable `.npz` trajectories.
- `data/processed/baseline_{N}.json` – Clean asymptotic Lyapunov exponent (includes variance).
- `data/processed/baseline_per_window_{N}.json` – Per‑window baseline estimates (mean, std, convergence error).
- `data/processed/ftle_results.json` – Aggregated FTLE estimates with status flags.
- `data/processed/regression_results.json` – Regression coefficients, p‑values, q‑values, Newey‑West flag, Tobit summary, and escape probabilities.
- `data/processed/results.json` – Consolidated results bundle (includes all of the above plus metadata).
- `data/processed/plots/` – PNG figures for convergence, bias scaling, and dimension scaling.

## Validation

After a successful run, you can verify all artifacts with the built‑in validator:

```bash
python -m code.utils.validate --check-all
```

The validator checks:

1. SHA‑256 checksums (`state/artifacts/manifest.yaml`).
2. Baseline convergence (< 5 % error at `T = 5000`).
3. JSON schema compliance for `ftle_results.json`, `regression_results.json`, and `results.json`.

Any failure aborts with a non‑zero exit status, causing CI to fail.