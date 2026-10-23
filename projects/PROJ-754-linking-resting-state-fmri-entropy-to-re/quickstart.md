# Quickstart: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

This guide walks a new user through the end‑to‑end analysis on a fresh GitHub Actions runner (or local Linux environment).

## Prerequisites
- Python 3.11 installed (or use the provided `requirements.txt`).
- Access token for the HCP dataset stored in the environment variable `HCP_TOKEN`.
- Sufficient disk space (≥ 14 GB) and memory (≥ 4 GB).

## Step‑by‑Step

1. **Create a virtual environment & install dependencies**
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Run the full pipeline (small test cohort)**
 ```bash
 python -m code.src.run_pipeline --subjects 5
 ```
 - Downloads a small subset of HCP data, applies quality control, computes multiscale entropy, and writes the results to `results/`.
 - Expected artefacts:
 * `results/entropy_matrix.parquet`
 * `results/covariates.parquet`
 * Log files under `logs/` documenting each step.

3. **Run the test suite**
 ```bash
 pytest -v code/tests/
 ```
 - Confirms that all modules import correctly and that a dry‑run of the pipeline exits cleanly. [UNRESOLVED-CLAIM: c_6c969e56 — status=not_enough_info]

## Expected Runtime & Resources (CI‑friendly)

| Stage | Approx. Time | Peak RAM |
|-------|--------------|----------|
| Download & QC | ≤ 30 min | ≤ 2 GB |
| Entropy (5 subjects) | ≤ 15 min | ≤ 2 GB |
| Total | **≤ 45 min** | **≤ 2 GB** |

All steps respect the CPU‑only constraint (GC‑001) and stay within the free‑tier GitHub Actions limits. [UNRESOLVED-CLAIM: c_cb63de4f — status=not_enough_info]
