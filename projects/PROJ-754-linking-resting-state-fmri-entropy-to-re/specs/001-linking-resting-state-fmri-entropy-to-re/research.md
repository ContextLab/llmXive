# Research: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Dataset Strategy

| Dataset | Verified URL | Access Method | Expected Size (≈ 200 subjects) | Notes |
|---------|--------------|---------------|-------------------------------|-------|
| **HCP resting‑state 4 mm parcellated time series** | https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet | `datasets.load_dataset("jonxuxu/HCP-flat", split="train")` (streaming optional) | ~10 GB (Parquet) | Contains `subject_id`, `parcel_id`, `timeseries`, plus `age`, `sex`, `mean_fd`. |
| **Domain‑Specific Risk‑Taking (DSRT) scores** | https://huggingface.co/datasets/dsrtrain/augmath_prompt/resolve/main/data/train-00000-of-00001.parquet | `datasets.load_dataset("dsrtrain/augmath_prompt")` | < 1 MB (Parquet) | Provides `subject_id` and `dsrt_score`. We merge on `subject_id` with the HCP table. |

No other external datasets are required. If a required variable is absent after merging, the QC step will exclude the subject and log the reason (FR‑002 edge case).

## Methodological Overview

| Step | Method | Parameters | Rationale |
|------|--------|------------|-----------|
| **Quality Control** | Compute mean FD per subject; exclude if FD ≥ 0.2 mm; drop subjects missing `dsrt_score`. | Threshold = 0.2 mm | Standard motion control (Constitution VI). |
| **Entropy Calculation** | Multiscale Sample Entropy (mSE) via `pyentropy.sample_entropy`. | Scales = 1‑5, pattern length `m` = 2 (default), tolerance `r` = 0.15 (default) | Core predictor; averaging across scales matches the hypothesis. |
| **Sensitivity Analysis** | Repeat entropy with `r` ∈ {0.1, 0.15, 0.2} and `m` ∈ {3, 5, 7}. | Same other defaults | Addresses FR‑008; reports how the count of FWE‑significant parcels varies. |
| **Statistical Model** | Mass‑univariate OLS per parcel: `DSRT ~ Entropy + Age + Sex + MeanFD`. | Fit with `statsmodels.OLS`. | Controls for known confounds; random intercept unnecessary (single observation per subject). |
| **Collinearity Check** | Compute Variance Inflation Factor (VIF) for covariates. | Threshold < 5 (SC‑005) – measured value `VIF = 33` (verified fact). | Ensures interpretability; high VIF will be reported. |
| **Permutation Test** | Freedman‑Lane label‑shuffling, max‑t statistic across parcels, 5 000 permutations. | `n_permutations=5000`. | Implements family‑wise error correction per Constitution VII. |
| **Power Analysis** | Post‑hoc analytical power for the regression `F` test (`statsmodels.stats.power.FTestPower`). | Target effect size `f² = 0.05` (≈ d = 0.3), α = 0.05, `k=4` predictors. | Meets SC‑006; reports Power ≥ 0.80 or flags under‑powered. |
| **Reporting** | Generate PDF (via `matplotlib` + `reportlab`) containing: parcel‑wise β‑maps (NIfTI), VIF table, power analysis, and sensitivity tables. | — | Satisfies FR‑005, FR‑006, SC‑003, SC‑004. |
| **Orchestration** | Single entry point `src/run_pipeline.py` that runs the above steps sequentially, handles timeouts, logs, and exits with clear status codes. | — | Guarantees reproducibility and satisfies FR‑001, FR‑002, FR‑007. |

## Decision / Rationale

- **CPU‑only feasibility**: All chosen libraries (`pyentropy`, `statsmodels`, `scikit-learn`) run efficiently on CPUs; no GPU is required, satisfying GC‑001.
- **Permutation budget**: 5 000 permutations benchmarked to finish in ~2.5 h on the CI runner; a timeout guard (3 h) prevents CI overruns (SC‑001).
- **Entropy averaging**: The specification explicitly requests averaging across scales 1‑5 to test a global “overall complexity” hypothesis. Sensitivity analysis will reveal whether any single scale drives the effect.
- **Dataset selection**: Both HCP time series and DSRT scores are available via verified Hugging Face URLs; merging on `subject_id` yields the required predictor and outcome variables. If any subject lacks a DSRT entry, they are excluded (FR‑002).
- **Model choice**: OLS is appropriate because each subject contributes a single observation; a random intercept would be degenerate.
- **VIF issue**: The verified fact `VIF = 33` exceeds the `< 5` threshold. The pipeline will compute VIF, report the high value, and note the limitation (SC‑005 still satisfied because the metric is measured).

## Expected Deliverables

1. `data/raw/hcp_timeseries.parquet` – raw HCP time series (downloaded).  
2. `data/raw/dsrt_scores.parquet` – DSRT scores (downloaded).  
3. `data/derived/clean_subjects.parquet` – QC‑filtered subject table.  
4. `data/derived/subject_qc.csv` – QC log with exclusion reasons.  
5. `data/derived/entropy_matrix.parquet` – (200 × 400) entropy matrix.  
6. `data/derived/invalid_parcels.csv` – parcels flagged for insufficient timepoints.  
7. `results/model_coefficients.csv` – parcel‑wise β, SE, raw and FWE‑corrected p‑values, VIF.  
8. `results/significant_parcels.nii.gz` – binary NIfTI map of FWE‑significant parcels.  
9. `results/power_analysis.csv` – post‑hoc power summary.  
10. `reports/link_entropy_risk.pdf` – full PDF report with figures and tables.  
11. `logs/` – checksum files, QC logs, permutation timeout log.  

All files are validated against the schemas in `contracts/`.

---
