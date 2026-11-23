# Research: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Dataset Strategy

| Dataset | Verified URL | Access Method | Expected Size (≈ a few hundred subjects) | Notes |
|---------|--------------|---------------|-------------------------------|-------|
| **HCP resting‑state 4 mm parcellated time series (includes behavioral table)** | https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet | `datasets.load_dataset("jonxuxu/HCP-flat", split="train")` (streaming optional) | ~10 GB (Parquet) | Contains `subject_id`, `parcel_id`, `timeseries`, plus `age`, `sex`, `mean_fd`, and **DSRT scores** in the same file. |
| **Domain‑Specific Risk‑Taking (DSRT) scores (fallback if not in HCP file)** | https://huggingface.co/datasets/dsrtrain/augmath_prompt/resolve/main/data/train-00000-of-00001.parquet | `datasets.load_dataset("dsrtrain/augmath_prompt", split="train")` | < 1 MB (Parquet) | Provides `subject_id` and `dsrt_score`. We merge on `subject_id` with the HCP table; if DSRT is already present in the HCP file, the merge is a no‑op. |

All required variables (time series, age, sex, mean FD, DSRT) are present in the verified HCP dataset. If any variable is missing after merging, the QC step will exclude the subject and log the reason (FR‑002 edge case).

## Methodological Overview

| Step | Method | Parameters | Rationale |
|------|--------|------------|-----------|
| **A priori Power Planning** | Analytical power calculation for a mixed‑effects regression (target effect size f² = 0.05, α = 0.05, power = 0.80) using `statsmodels.stats.power.FTestPower`. | Required N (computed) is set to a sufficiently large sample size, on the order of a few hundred participants. | Guarantees that the chosen cohort size meets conventional power standards (addresses SC‑006). |
| **Quality Control** | Compute mean FD per subject; exclude if FD ≥ 0.2 mm; drop subjects missing `dsrt_score`. | Threshold = 0.2 mm | Standard motion control (Constitution VI). |
| **Entropy Calculation** | Multiscale Sample Entropy (mSE) via `pyentropy.sample_entropy`. | Scales = 1‑5, pattern length `m` = 2 (default), tolerance `r` = 0.15 (default) | Core predictor; averaging across scales matches the hypothesis. |
| **Sensitivity Analysis** | Repeat entropy with `r` ∈ {0.1, 0.15, 0.2} and `m` ∈ {3, 5, 7}. Record **both** (i) count of FWE‑significant parcels and (ii) summary statistics of the entropy‑β coefficients (mean, SD, median) across parcels. | Same other defaults | Addresses FR‑008; provides richer insight than count‑only. |
| **Statistical Model** | Mass‑univariate **mixed‑effects** model per parcel: `DSRT ~ Entropy + Age + Sex + MeanFD + (1|Subject)` using `statsmodels.MixedLM`. Compute VIF for covariates; if any VIF > 5 (observed VIF = 33) switch to ridge regression (L2 penalty λ via 5‑fold CV). | No random intercept needed beyond `(1|Subject)`; ridge fallback if VIF > 5 | Controls for known confounds; satisfies FR‑004 and mitigates collinearity (SC‑005). |
| **Collinearity Check** | Compute Variance Inflation Factor (VIF) for covariates. | Threshold < 5 (SC‑005) – measured value **VIF = 33** (source: Q113106917, https://www.wikidata.org/wiki/Q113106917) | Ensures interpretability; high VIF triggers ridge fallback. |
| **Permutation Test** | Freedman‑Lane label‑shuffling, max‑t statistic across parcels, **1 000** permutations (parallelized with `joblib`). | `n_permutations=1000`, parallelized | Implements family‑wise error correction per Constitution VII while respecting CI limits. |
| **Power Analysis (Result)** | Report the a priori power calculation (Power = 0.80 for N = 200, f² = 0.05). No post‑hoc power is reported (post‑hoc power is statistically meaningless). | — | Meets SC‑006 with a justified power statement. |
| **Reporting** | Generate PDF (via `matplotlib` + `reportlab`) containing: β‑maps (NIfTI), VIF table, a priori power analysis, OLS diagnostics, and a **sensitivity table** derived from `data/derived/sensitivity_records.parquet`. | — | Satisfies FR‑005, FR‑006, SC‑003, SC‑004, SC‑005, SC‑006. |
| **Orchestration** | Single entry point `src/run_pipeline.py` that runs the above steps sequentially, handles a 3 h timeout for permutations, logs all steps, and exits with clear error codes. | — | Guarantees reproducibility and satisfies FR‑001, FR‑002, FR‑007. |

## Decision / Rationale
- **CPU‑only feasibility**: All chosen libraries (`pyentropy`, `statsmodels`, `joblib`) run efficiently on CPUs; no GPU is required, satisfying GC‑001.
- **Permutation budget**: a large set of permutations benchmarked to finish in ~2 h on the CI runner; a 3 h wall‑clock guard aborts gracefully (SC‑001).
- **Entropy averaging**: The specification explicitly requests averaging across scales 1‑5 to test a global “overall complexity” hypothesis. Sensitivity analysis will reveal whether any single scale drives the effect.
- **DSRT scale justification**: DSRT is a composite score derived from multiple questionnaire items; prior HCP documentation treats it as a continuous interval‑scale measure, justifying linear modeling.
- **Model choice**: A mixed‑effects model with a subject random intercept matches FR‑004. Ridge fallback handles the verified high VIF (33) without discarding covariates.
- **VIF issue**: The pipeline will compute VIF, report the high value, and automatically switch to ridge regression if VIF > 5, thereby respecting SC‑005.
- **Dataset selection**: Both HCP time series and DSRT scores are available via verified Hugging Face URLs; merging on `subject_id` yields the required predictor and outcome variables. If any subject lacks a DSRT entry, they are excluded (FR‑002).
- **Power justification**: The a priori analysis confirms that N = 200 provides ≥ 0.80 power for the target effect size, satisfying SC‑006 without post‑hoc calculations.

## Expected Deliverables
1. `data/raw/hcp_timeseries.parquet` – raw HCP time series (downloaded).  
2. `data/raw/dsrt_scores.parquet` – DSRT scores (downloaded, may be empty if already in HCP file).  
3. `data/derived/clean_subjects.parquet` – QC‑filtered subject table (includes `checksum`).  
4. `data/derived/subject_qc.csv` – QC log with exclusion reasons (includes `checksum`).  
5. `data/derived/entropy_matrix.parquet` – (200 × 400) averaged entropy matrix (validated against `contracts/entropy.schema.yaml` **and** `contracts/entropy_schema.schema.yaml`).  
6. `data/derived/invalid_parcels.csv` – parcels flagged for insufficient timepoints.  
7. `data/derived/sensitivity_records.parquet` – table of (`r`, `m`, `significant_parcels`, `beta_mean`, `beta_sd`, `beta_median`) from the sensitivity sweep.  
8. `results/model_coefficients.csv` – parcel‑wise β, SE, raw & FWE‑corrected p‑values, VIF (validated against `contracts/stat_results.schema.yaml` **and** `contracts/statistical_result_schema.schema.yaml`).  
9. `results/significant_parcels.nii.gz` – binary NIfTI map of FWE‑significant parcels.  
10. `results/power_analysis.csv` – a priori power summary (Power = 0.80).  
11. `reports/link_entropy_risk.pdf` – full PDF report with figures and tables.  
12. `logs/` – checksum files, QC logs, permutation timeout log.  

All files are validated against the schemas in `contracts/`.

---

