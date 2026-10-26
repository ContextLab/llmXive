# Quickstart: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

Run the full analysis on a fresh GitHub Actions runner (or any Linux environment with Python 3.11).

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
       --subject-limit <maximum_subjects> \
       --fd-threshold 0.2 \
       --entropy-r 0.15 \
       --entropy-m 2 \
       --scales 1 2 3 4 5 \
       --n-permutations 1000 \
       --seed 42
   ```
   The script will:
   - **Download** HCP minimally preprocessed 4 mm parcellated time series **including** DSRT scores (verified URLs).
   - **Perform QC** (motion threshold, missing DSRT) and write `data/derived/clean_subjects.parquet` **and** `data/derived/subject_qc.csv` (validated against `contracts/subject_qc.schema.yaml`).
   - **Compute** multiscale entropy (averaged across scales 1‑5) and write `data/derived/entropy_matrix.parquet` (validated against both `contracts/entropy.schema.yaml` **and** `contracts/entropy_schema.schema.yaml`).
   - **Fit** a **mixed‑effects** linear model per parcel (`DSRT ~ Entropy + Age + Sex + MeanFD + (1|Subject)`) using `statsmodels.MixedLM`. If the VIF for covariates exceeds 5 (the verified VIF = 33), the pipeline automatically switches to ridge regression with cross‑validated L2 penalty.
   - **Run** 1 000 Freedman‑Lane label‑shuffled permutations (parallelized) and apply max‑t FWE correction.
   - **Conduct** a sensitivity sweep over `r` (0.1, 0.15, 0.2) and `m` (3, 5, 7), recording both the count of significant parcels **and** summary statistics of the entropy‑β coefficients.
   - **Generate** the final PDF report `reports/link_entropy_risk.pdf` and NIfTI map `results/significant_parcels.nii.gz`.
   - **Log** all steps under `logs/` (including permutation timeout logs) and exit with clear error codes if any step fails.

3. **Inspect the results**
   - **Statistical table**: `results/model_coefficients.csv` (includes `checksum`).
   - **Significant parcels map**: `results/significant_parcels.nii.gz`  
   - **Power analysis**: `results/power_analysis.csv` (shows a priori power = 0.80 for N = 200).  
   - **Sensitivity table**: `data/derived/sensitivity_records.parquet` (also summarised in the PDF).  
   - **Full report**: `reports/link_entropy_risk.pdf`

4. **Run unit tests (optional)**
   ```bash
   pytest -v tests/
   ```
   The test suite checks:
   - Successful download of the HCP dataset.
   - QC logic and output file creation.
   - Entropy computation and invalid‑parcel flagging.
   - Statistical pipeline produces the expected schema‑conforming outputs.

## Expected Runtime & Resources (CI‑friendly)

| Stage | Approx. Time | Peak RAM |
|-------|--------------|----------|
| Download & QC | ≤ 30 min | ≤ 2 GB |
| Entropy (full 200) | ≤ 90 min | ≤ 4 GB |
| Modeling & 1 000 permutations (parallel) | ≤ 150 min | ≤ 5 GB |
| Reporting & Sensitivity | ≤ 30 min | ≤ 2 GB |
| **Total** | **≈ 4 h** | **≤ 5 GB** |

All steps respect the CPU‑only constraint (GC‑001) and stay within the free‑tier GitHub Actions limits.

---

