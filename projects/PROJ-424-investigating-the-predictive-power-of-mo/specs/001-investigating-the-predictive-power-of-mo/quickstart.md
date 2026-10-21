# Quickstart: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Prerequisites
- Linux (Ubuntu 22.04 recommended) or macOS with Python 3.11+.  
- ~7 GB RAM, ~14 GB disk space, **no GPU** required.

## Installation

```bash
# Clone the repository
git clone <PROJECT_REPO_URL>
cd projects/PROJ-424-investigating-the-predictive-power-of-mo

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Data Preparation

The experimental reference file is generated automatically by the first pipeline step:

```bash
# Generate `nist_refs.json` and its checksum
python code/data/loader.py --generate-refs
```

You should see:

```
data/raw/nist_refs.json created (multiple entries)
data/raw/nist_refs.json.sha256 created
```

## Running the Full Workflow

```bash
# Execute the complete end‑to‑end pipeline (includes simulations, analysis, bootstrap, reporting)
python code/main.py --full-batch
```

What happens:

1. Simulations for water, ethanol, and acetone at an initial, intermediate, and extended simulation duration are launched (CPU only).  
2. MSD extraction, convergence checks, and diffusion coefficient calculation are performed.  
3. MAE bootstrap (with a sufficient number of iterations) and sensitivity analysis are run.  
4. Timescale‑accuracy curves and summary tables are written to `results/`.

## Minimal Example (single trajectory)

If you only want to test the pipeline without the full compute budget:

```bash
python code/pipeline.py --solvent water --duration 1 --seed 0
```

This runs a single brief water simulation, produces one row in `diffusion_results.csv`, and updates the bootstrap stats for that condition.

## Verification Checklist

| Check | Expected Outcome |
|-------|------------------|
| `data/raw/nist_refs.json` exists and matches its SHA‑256 checksum | `tests/test_loader.py` passes (`test_load_valid`, `test_checksum_matches`). |
| All simulation `.xtc` files are present under `data/raw/simulations/` | `tests/test_simulation.py` passes. |
| `diffusion_results.csv` contains a row with `status = "accepted"` for at least one trajectory | `tests/test_diffusion.py` passes. |
| `bootstrap_stats.json` contains entries generated over many iterations and a `paired_test` block. | `tests/test_bootstrap.py` passes. |
| `code/pipeline.py --full-batch` exits with code 0 and produces figures in `results/` | `tests/test_pipeline.py` passes. |

## Troubleshooting
- **OpenMM import error** – ensure the exact version `openmm==8.1.1` is installed (`pip install openmm==8.1.1`).  
- **R² < 0.95** – the run will be flagged `convergence_failed`; inspect `results/convergence_log.txt` for details.  
- **Wall‑clock > 5.5 h** – a warning is logged; the pipeline continues but the warning appears in `results/performance.log`.  
- **Bootstrap takes > 0.5 h** – unlikely given vectorized implementation; if it occurs, verify that the CI runner is not throttling CPU.

---
