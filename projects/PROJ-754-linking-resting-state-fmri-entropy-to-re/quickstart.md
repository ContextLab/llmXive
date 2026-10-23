# Quickstart: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

This guide walks a new user through the end‑to‑end analysis on a fresh
GitHub Actions runner (or any Linux environment with Python 3.11).

## Prerequisites
- Python 3.11 installed (or use the provided `requirements.txt`).
- Access token for the HCP dataset stored in the environment variable `HCP_TOKEN`.
- At least **14 GB** free disk space and **4 GB** RAM.

## Step‑by‑Step

1. **Create a virtual environment & install dependencies**
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Run the full pipeline (small test cohort)**
 ```bash
 python -m src.run_pipeline --subjects 5
 ```
 - The script will download a tiny subset of HCP data, perform QC, compute
 multiscale entropy and write the results to `results/`.
 - On success you will see the exact line:
 ```
 Pipeline completed
 ```

3. **Run the test suite**
 ```bash
 pytest -v code/tests/
 ```
 - Confirms that all modules import correctly and that a dry‑run of the
 pipeline exits cleanly.
