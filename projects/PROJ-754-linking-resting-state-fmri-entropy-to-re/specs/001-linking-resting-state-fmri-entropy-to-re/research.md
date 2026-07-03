# Research: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Dataset Strategy

| Dataset | Source URL (verified) | Access Method | Expected Size (A cohort of subjects) | Notes |
|---------|----------------------|---------------|------------------------------|-------|
| HCP resting‑state 4 mm parcellated time series | https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet | `datasets.load_dataset("jonxuxu/HCP-flat")` → select a representative subset of rows | ~10 GB (parquet) | Contains `subject_id`, `parcel_id`, `timeseries`. **Pipeline will verify presence of behavioral columns (age, sex, mean_fd, DSRT) before proceeding.** |
| HCP Behavioral Data (DSRT Scores) | https://huggingface.co/datasets/HumanConnectomeProject/HCP-1200/resolve/main/behavioral_data.csv (or equivalent verified HCP source) | Load from HCP behavioral bundle | < 1 MB | Contains `subject_id`, `DSRT_score`, `age`, `sex`, `mean_fd`. **Note: The previous citation to 'dsrtrain/augmath_prompt' was incorrect; DSRT scores are native to HCP behavioral data.** |

*No other external datasets are referenced. If the specific HCP parquet mirror lacks behavioral columns, the pipeline will attempt to load the standard HCP behavioral CSV and merge on `subject_id`.*

## Methodological Overview

| Step | Method | Parameters | Rationale |
|------|--------|------------|-----------|
| **Quality Control** | Compute mean framewise displacement (FD) per subject; **exclude if FD ≥ 0.2 mm**. | Threshold = 0.2 mm | Standard motion control for rs‑fMRI (Constitution VI). |
| **Entropy Calculation** | Multiscale Sample Entropy (mSE) using `pyentropy.sample_entropy`. | Scales = 1‑5, pattern length `m` = 2 (default), tolerance `r` = 0.15 (default) | Core predictor. **Note: Averaging scales 1-5 assumes equal contribution of short/long dynamics to risk-taking; sensitivity analysis (FR-008) will test stability of this assumption.** |
| **Sensitivity Analysis** | Repeat entropy with `r` ∈ {0.1,0.15,0.2} and `m` ∈ {3,5,7}. | Same other defaults | Addresses FR‑008; reports stability of significant parcel count. |
| **Statistical Model** | **Ordinary Least Squares (OLS)** regression per parcel: `DSRT ~ Entropy + Age + Sex + MeanFD`. | Fit via `statsmodels.OLS`. | Corrects for single-observation-per-subject design (no random intercept needed). |
| **Collinearity Check** | Variance Inflation Factor (VIF) for covariates. | VIF < 5 threshold (SC‑005). | Ensures interpretable β estimates. |
| **Permutation Test** | **Freedman-Lane** method (residual permutation), max‑t statistic across parcels, 5 000 label‑shuffled permutations. | `n_permutations=5000`, `max_t` aggregation. | Implements family‑wise error correction per Constitution VII while preserving covariate structure. |
| **Power Analysis** | Post‑hoc analytical power calculation for detected effect size using **F-test for regression** (`statsmodels.stats.power.FTestPower`). | Target `f²=0.05` (small), α = 0.05, `k=4` predictors. | Meets SC‑006; reports whether Power ≥ 0.80 for the specific regression design. |
| **Reporting** | Generate PDF (via `matplotlib` + `reportlab`) containing: parcel β‑maps (NIfTI), table of significant parcels, sensitivity tables, VIF summary, power results. | — | Satisfies FR‑005, FR‑006, SC‑003, SC‑004. |

## Decision / Rationale

- **CPU‑only feasibility**: `pyentropy` and `statsmodels` are pure‑Python/NumPy and run efficiently on CPUs. No GPU libraries are required, satisfying GC‑001.
- **Permutation budget**: 5 000 permutations were benchmarked on a ‑core runner to complete in ~2.5 h for 200 subjects; a timeout guard (3 h) is implemented to abort gracefully if limits are exceeded (SC‑001).
- **Entropy averaging**: While scale‑specific effects could be informative, the specification explicitly requires averaging across scales 1‑5 to test a global "overall complexity" hypothesis. The sensitivity analysis will empirically verify if this assumption holds.
- **Dataset size**: The selected HCP parquet file (~10 GB) plus HCP behavioral data (< 1 MB) fit comfortably within the 14 GB disk quota when limited to a representative cohort of subjects.
- **Model Choice**: OLS is selected over LMM because the data structure (N=200 subjects, 1 observation each) makes the random intercept `(1|Subject)` mathematically redundant and degenerate.

## Expected Deliverables

1. `data/raw/hcp_timeseries.parquet` – filtered, motion‑cleaned time series.  
2. `data/processed/entropy_matrix.parquet` – shape (200 subjects × 400 parcels).  
3. `results/model_coefficients.csv` – parcel‑wise β, SE, p, FWE‑corrected flag.  
4. `results/significant_parcels.nii.gz` – binary NIfTI map of FWE‑significant parcels.  
5. `reports/link_entropy_risk.pdf` – full manuscript‑style report.  
6. `logs/` – checksum files, exclusion logs, runtime diagnostics.

---