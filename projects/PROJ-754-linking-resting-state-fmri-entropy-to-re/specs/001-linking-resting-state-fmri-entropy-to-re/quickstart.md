# Quickstart: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

This guide runs the full analysis on a fresh GitHub Actions runner (or any Linux environment with Python 3.11).

## Prerequisites
1. **Python 3.11** (or use the provided virtual environment).  
2. **HCP access token** stored in the environment variable `HCP_TOKEN`.  
3. At least **14 GB** free disk space and **4 GB** RAM.  

## Step‑by‑Step

1. **Create a virtual environment & install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the orchestrated pipeline**
   ```bash
   python -m src.run_pipeline \
       --hcp-token $HCP_TOKEN \
       --subject-limit 200 \
       --fd-threshold 0.2 \
       --entropy-r 0.15 \
       --entropy-m 2 \
       --scales 1 2 3 4 5 \
       --n-permutations 5000 \
       --seed 42
   ```
   The script will:
   - Download HCP time series and DSRT scores.
   - Perform QC (motion, missing DSRT) → `clean_subjects.parquet` & `subject_qc.csv`.
   - Compute multiscale entropy → `entropy_matrix.parquet`.
   - Fit parcel‑wise OLS models, run permutations, compute VIF and power → CSV/NIfTI outputs.
   - Generate the final PDF report `reports/link_entropy_risk.pdf`.
   - Log all steps under `logs/`.

3. **Inspect the results**
   - **Statistical table**: `results/model_coefficients.csv`  
   - **Significant parcels map**: `results/significant_parcels.nii.gz`  
   - **Power summary**: `results/power_analysis.csv`  
   - **Full report**: `reports/link_entropy_risk.pdf`

4. **Run unit tests (optional)**
   ```bash
   pytest -v tests/
   ```
   The test suite checks:
   - Successful download (`tests/integration/test_download.py`).
   - QC logic and output file creation (`tests/unit/test_qc.py`).
   - Entropy computation and invalid‑parcel flagging (`tests/unit/test_entropy.py`).
   - Statistical pipeline produces the expected schema (`tests/unit/test_stats.py`).

## Expected Runtime & Resources (CI‑friendly)

| Stage | Approx. Time | Peak RAM |
|-------|--------------|----------|
| Download & QC | ≤ 30 min | ≤ 2 GB |
| Entropy (full 200) | ≤ 90 min | ≤ 4 GB |
| Modeling & Permutations | ≤ 180 min | ≤ 5 GB |
| Reporting & Sensitivity | ≤ 30 min | ≤ 2 GB |
| **Total** | **≈ 4 h** | **≤ 5 GB** |

All steps respect the CPU‑only constraint (GC‑001) and stay within the free‑tier GitHub Actions limits.

---
