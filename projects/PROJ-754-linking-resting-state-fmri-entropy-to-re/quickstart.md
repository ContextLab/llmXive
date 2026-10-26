# Quickstart: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

Run the full analysis on a fresh GitHub Actions runner (or any Linux environment with Python 3.11).

## Prerequisites
1. **Python 3.11** (or use the provided virtual environment).
2. **HCP access token** stored in the environment variable `HCP_TOKEN`.
3. At least **14 GB** free disk space and **4 GB** RAM.

## Step‑by‑Step

1. **Create a virtual environment & install dependencies**
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Run the orchestrated pipeline**
 ```bash
 python -m code.src.run_pipeline --subjects 5
 ```
 - The script will download a tiny subset of HCP data, perform QC, compute multiscale entropy and write the results to `results/`.
 - On success you will see the exact line:
 ```
 Pipeline completed (dry-run)
 ```
 - To execute a full run (non‑dry‑run) provide the `--dry-run` flag set to `false` or omit it:
 ```bash
 python -m code.src.run_pipeline --subjects 5
 ```

3. **Run the test suite**
 ```bash
 pytest -v tests/
 ```
 - Confirms that all modules import correctly and that a dry‑run of the pipeline exits cleanly.

## Optional flags
- `--dry-run` – skips all heavy processing and instantly prints “Pipeline completed (dry‑run)”.
- `--subjects N` – number of subjects to process (default 5 for quick tests).

## Expected Runtime & Resources (CI‑friendly)

| Stage | Approx. Time | Peak RAM |
|-------|--------------|----------|
| Download & QC | ≤ 30 min | ≤ 2 GB |
| Entropy (full 200) | ≤ 90 min | ≤ 4 GB |
| Modeling & 1 000 permutations (parallel) | ≤ 150 min | ≤ 5 GB |
| Reporting & Sensitivity | ≤ 30 min | ≤ 2 GB |
| **Total** | **≈ 4 h** | **≤ 5 GB** |

All steps respect the CPU‑only constraint (GC‑001) and stay within the free‑tier GitHub Actions limits.