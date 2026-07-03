# Quickstart: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

This guide walks a new user through the end‑to‑end analysis on a fresh GitHub Actions runner (or local Linux environment).

## Prerequisites
- Python 3.11 installed (or use the provided `requirements.txt`).  
- Access token for the HCP dataset stored in the environment variable `HCP_TOKEN`.  
- Sufficient disk space (≥ 14 GB) and memory (≥ 4 GB).  

## Step‑by‑Step

1. **Create a virtual environment & install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Download & QC the data (Phase 1)**
   ```bash
   python -m src.download_data \
       --hcp-token $HCP_TOKEN \
       --subject-limit 200 \
       --fd-threshold 0.2 \
       --output-dir data/
   ```
   - Produces `data/raw/hcp_timeseries.parquet`, `data/raw/dsrt_scores.parquet`, and `data/derived/clean_subjects.parquet`.  
   - Logs exclusions in `logs/qc.log` and writes checksums to `data/checksums.txt`.

3. **Compute multiscale entropy (Phase 2)**
   ```bash
   python -m src.compute_entropy \
       --input data/derived/clean_subjects.parquet \
       --output data/derived/entropy_matrix.parquet \
       --scales 1 2 3 4 5 \
       --average \
       --r 0.15 \
       --m 2
   ```
   - Generates a (200 × 400) parquet matrix.  
   - For the sensitivity analysis, run the same command with `--r` in `0.1 0.15 0.2` and `--m` in `3 5 7`; results are appended to `data/derived/sensitivity.parquet`.

4. **Fit parcel‑wise models & permutation test (Phase 3)**
   ```bash
   python -m src.run_stats \
       --entropy data/derived/entropy_matrix.parquet \
       --covariates data/derived/clean_subjects.parquet \
       --n-permutations 5000 \
       --max-runtime 10800 \
       --output-dir results/
   ```
   - Produces `results/model_coefficients.csv`, `results/significant_parcels.nii.gz`, and `results/permutation_null.npy`.  
   - If the permutation step exceeds 3 h, the script aborts and writes a timeout warning to `logs/permutation_timeout.log`.

5. **Generate the final report (Phase 4)**
   ```bash
   python -m src.generate_report \
       --coeffs results/model_coefficients.csv \
       --nii results/significant_parcels.nii.gz \
       --sensitivity data/derived/sensitivity.parquet \
       --power-output results/power_analysis.csv \
       --output reports/link_entropy_risk.pdf
   ```
   - The PDF contains: methods, parcel‑wise β‑maps, sensitivity tables, VIF diagnostics, and the post‑hoc power analysis.

6. **Verify reproducibility (optional)**
   ```bash
   pytest -v tests/
   ```
   - Unit and contract tests confirm that schema validation passes and that the mini‑dataset workflow reproduces expected shapes.

## Expected Runtime & Resources (CI‑friendly)

| Stage | Approx. Time | Peak RAM |
|-------|--------------|----------|
| Download & QC | ≤ 30 min | ≤ 2 GB |
| Entropy (full 200) | ≤ 90 min | ≤ 4 GB |
| Modeling & Permutations | ≤ 180 min | ≤ 5 GB |
| Reporting | ≤ 30 min | ≤ 2 GB |
| **Total** | **≈ 4 h** | **≤ 5 GB** |

All steps respect the CPU‑only constraint (GC‑001) and stay within the free‑tier GitHub Actions limits.

---
