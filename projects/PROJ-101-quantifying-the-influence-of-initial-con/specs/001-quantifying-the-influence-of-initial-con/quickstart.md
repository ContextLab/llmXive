# Quickstart: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Prerequisites
- Python 3.11 or newer  
- `git`  
- `pip` (preferably inside a virtual environment)

## Installation

```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd projects/PROJ-101-quantifying-the-influence-of-initial-con

# 2️⃣ Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Verify the Test Suite

```bash
pytest -q
# All tests should pass on the CI runner.
```

## Running the Full Analysis (Recommended)

```bash
# Example grid: N = 3, 5, 7 and 6 noise levels, 30 trials each, 3 window sizes
python -m code.main \
    --N-values 3,5,7 \
    --noise-levels 0.0001,0.001,0.01,0.1,0.5,1.0 \
    --trials 30 \
    --window-sizes 500,1000,5000 \
    --seed 42
```

The command performs, in order:
1. **Trajectory generation** (raw files under `data/raw/`).  
2. **Baseline validation** (creates `baseline_{N}.json` and `baseline_per_window_{N}.json`).  
3. **FTLE calculation** for each window size.  
4. **Statistical analysis** (primary Tobit censored regression, secondary mixed‑effects on bounded data, Durbin‑Watson, Newey‑West, BH‑FDR, escape probability).  
5. **Visualization** (plots saved under `data/processed/plots/`).  
6. **Artifact packaging** (`ftle_results.json`, `regression_results.json`, `results.json`) with schema validation.

### Alternative Modes

| Mode | Description | Command |
|------|-------------|---------|
| **Generation only** | Produce raw trajectories without downstream analysis. | `python -m code.main --mode generate --N 5 --sigma 0.01 --steps 10000 --trials 10` |
| **Analysis only** | Use existing raw data to run baseline, FTLE, and regression. | `python -m code.main --mode analyze` |
| **Benchmark** | Run a reduced benchmark (5 trials per config) to verify runtime limits. | `python -m code.main --mode benchmark --trials 5` |
| **Tobit only** | Fit only the censored regression on the full dataset. | `python -m code.main --mode tobit` |

## Configuration

Key parameters can be edited in `code/config.py` or overridden via CLI:

| CLI flag | Meaning |
|----------|---------|
| `--N-values` | Comma‑separated list of oscillator counts (e.g., `3,5,7`). |
| `--noise-levels` | Comma‑separated list of σ_noise values (e.g., `0.0001,0.001,0.01`). |
| `--trials` | Number of independent runs per configuration (default = 30). |
| `--window-sizes` | Sliding‑window lengths for FTLE (default = `500,1000,5000`). |
| `--seed` | Global seed for reproducibility (default = 42). |
| `--fit-tobit` | Flag to run Tobit regression (enabled by default). |

## Output Overview

- `data/raw/` – Immutable `.npz` trajectories.  
- `data/processed/baseline_{N}.json` – Clean asymptotic exponent (includes variance).  
- `data/processed/baseline_per_window_{N}.json` – Per‑window baseline estimates (mean, std, convergence error).  
- `data/processed/ftle_results.json` – Aggregated FTLE estimates and status flags.  
- `data/processed/regression_results.json` – Mixed‑effects coefficients, Tobit summary, escape probabilities, **baseline_variance_used** flag.  
- `data/processed/results.json` – Bundle containing all above plus metadata.  
- `data/processed/plots/` – PNG figures for convergence, bias scaling, and dimension scaling.  

## Validation

After a successful run, execute:

```bash
python -m code.utils.validate --check-all
```

The validator:
1. Verifies SHA‑256 checksums (`state/artifacts/manifest.yaml`).  
2. Confirms baseline convergence (< 5 % error at `T=5000`).  
3. Validates `ftle_results.json` against `contracts/ftle_results.schema.yaml`.  
4. Validates `regression_results.json` against `contracts/regression_results.schema.yaml`.  
5. Validates `results.json` against `contracts/results.schema.yaml`.  

Any failure aborts with a non‑zero exit status, causing CI to fail.

---
