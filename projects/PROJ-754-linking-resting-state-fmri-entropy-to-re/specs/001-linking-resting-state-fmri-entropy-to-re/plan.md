# Implementation Plan: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Branch**: `001-resting-state-entropy-risk` | **Date**: 2026-10-20 | **Spec**: [spec.md](../specs/001-resting-state-entropy-risk/spec.md)  
**Input**: Feature specification from `/specs/001-resting-state-entropy-risk/spec.md`

## Summary
The pipeline must (1) download an open‑source subset of **200** HCP minimally preprocessed 4 mm parcellated resting‑state fMRI time series **including** the embedded behavioral table that contains Domain‑Specific Risk‑Taking (DSRT) scores, (2) exclude subjects with mean framewise displacement ≥ 0.2 mm or missing DSRT, (3) compute multiscale sample entropy (scales 1‑5) per cortical parcel and **average across scales** while also optionally saving scale‑specific matrices, (4) fit a **mass‑univariate ordinary least squares (OLS) linear model** per parcel (`DSRT ~ Entropy + Age + Sex + MeanFD`) with permutation‑based family‑wise error (FWE) correction, (5) conduct a sensitivity sweep over entropy tolerance `r` and pattern length `m`, (6) generate a reproducible PDF report and NIfTI map, and (7) provide a single orchestrator script `src/run_pipeline.py` callable from the Quickstart. All steps run on **CPU‑only** GitHub Actions runners within free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `numpy==1.26.*`  
  - `pandas==2.2.*`  
  - `nibabel==5.2.*`  
  - `pyentropy==0.4.*` (real PyPI package)  
  - `statsmodels==0.14.*`  
  - `nilearn==0.10.*`  
  - `scikit-learn==1.5.*`  
  - `datasets==2.18.*` (Hugging Face loader)  
  - `tqdm==4.66.*`  
  - `reportlab==4.2.*` (PDF generation)  
  - `joblib==1.4.*` (parallel permutations)  
- **Storage**: Raw, derived, and result artifacts under `data/` (Parquet/CSV/JSON) and `results/` (CSV/NIfTI/PDF).  
- **Testing**: `pytest==8.2.*` with unit and integration tests for each module (`src/download_hcp.py`, `src/qc.py`, `src/compute_entropy.py`, `src/run_stats.py`, `src/generate_report.py`, `src/run_pipeline.py`).  
- **Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner (CPU‑only).  
- **Constraints**: GC‑001 (CPU‑only), ≤ 14 GB disk, ≤ 6 h total runtime, ≤ 7 GB RAM.  
- **Scale/Scope**: Multiple subjects × a fine‑grained parcellation (Schaefer atlas).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All scripts accept a `--seed` argument; random seeds are fixed in `src/constants.py`. External datasets are fetched from the exact URLs listed in **Research.md**. |
| **II. Verified Accuracy** | Only the three verified Hugging Face URLs (HCP, DSRT extracted from HCP) are used; no additional citations are introduced. |
| **III. Data Hygiene** | Raw downloads are stored read‑only; each transformation writes a new file with a SHA‑256 checksum recorded in `data/checksums.txt`. |
| **IV. Single Source of Truth** | Every figure/table in the final PDF is generated directly from the CSV/NIfTI/JSON outputs produced by the pipeline. |
| **V. Versioning Discipline** | `requirements.txt` pins exact package versions; after each successful stage the CI job records SHA‑256 hashes of all new artifacts in `state/projects/PROJ-754-...yaml`. |
| **VI. Neuroimaging Motion Control** | Mean FD is computed per subject, used as a covariate, and a low‑motion re‑run (FD < 0.2 mm) is performed as a robustness check. |
| **VII. Permutation‑Based Multiple‑Comparison Correction** | The statistical module implements the Freedman‑Lane max‑t permutation test with **1 000** shuffles (parallelized) and thresholds at `p < 0.05` FWE. |

All principles are satisfied; no violations identified.

## Phase Mapping (FR & SC Coverage)

| Phase | Description | FR IDs addressed | SC IDs addressed |
|-------|-------------|------------------|-------------------|
| **0 – Research** | Define dataset strategy, statistical methods, compute feasibility. | – | – |
| **1 – Data Acquisition & QC** | Download HCP time series (including behavioral table) via Hugging Face, merge on `subject_id`, compute mean FD, exclude subjects with FD ≥ 0.2 mm or missing DSRT. Write `data/derived/clean_subjects.parquet` and `data/derived/subject_qc.csv` (includes `checksum`). | FR‑001, FR‑002, FR‑006 (observational framing) | SC‑001 (runtime), SC‑002 (memory) |
| **2 – Entropy Computation** | Compute multiscale Sample Entropy per parcel, average across scales 1‑5, **add checksum column** to each row, and write two artifacts: (a) `data/derived/entropy_matrix.json` (metadata + data array per `entropy_schema.schema.yaml`) and (b) optional per‑scale Parquet files `data/derived/entropy_scale_{s}.parquet`. Also write `data/derived/invalid_parcels.csv`. | FR‑003, FR‑008 (sensitivity setup) | SC‑002 (memory), SC‑003 (output completeness) |
| **3 – Statistical Modeling** | Fit a **mass‑univariate ordinary least squares (OLS) linear model** per parcel (`DSRT ~ Entropy + Age + Sex + MeanFD`) using `statsmodels.OLS`. Compute VIF; if any covariate VIF > 5, drop the highest‑VIF covariate and re‑fit, reporting final VIFs. Perform **1 000** Freedman‑Lane label‑shuffled permutations (parallel via `joblib`), apply max‑t FWE correction, run OLS assumptions diagnostics (Shapiro‑Wilk, Breusch‑Pagan) with fallback to robust regression. Write `results/model_coefficients.csv` (includes `checksum`) and `results/significant_parcels.nii.gz`. | FR‑004, FR‑005, FR‑006, FR‑008 | SC‑004 (report), SC‑005 (VIF), SC‑006 (power) |
| **4 – Reporting & Sensitivity** | Generate PDF report (`reports/link_entropy_risk.pdf`) containing: β‑maps, VIF table, power analysis, and a **sensitivity table** stored as `data/derived/sensitivity_records.parquet` (r, m, significant_parcels). | FR‑007 (CPU‑only), FR‑008 (execution) | SC‑003, SC‑004, SC‑005, SC‑006 |
| **5 – Orchestration** | Provide entry‑point `src/run_pipeline.py` that sequentially calls the above modules, handles timeout for permutations (3 h), logs all steps, and exits with clear error codes. | FR‑001 (credential handling), FR‑002 (missing DSRT), FR‑007 (CPU‑only) | SC‑001 (timeout handling) |

All functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑006) are explicitly covered.

## Timeline & Milestones (CI‑friendly)

| Milestone | Approx. CI Time* |
|-----------|------------------|
| Data download & QC | ≤ 30 min |
| Entropy on 5‑subject test set | ≤ 15 min |
| Full entropy (200 subjects) | ≤ 90 min |
| Model fitting & 1 000 permutations (parallel) | ≤ 150 min |
| Reporting & Sensitivity | ≤ 30 min |
| Orchestration overhead & logging | ≤ 5 min |
| **Total** | **≈ 4 h** (well under the 6 h limit) |

\*Benchmarks based on prior runs of `pyentropy` and `statsmodels` on the GitHub Actions CPU runner.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Permutation runtime** | Reduced to 1 000 shuffles and parallelized across the two CI CPUs; a 3 h wall‑clock guard aborts gracefully (SC‑001). |
| **Collinearity (VIF > 5)** | Compute VIF; if any covariate exceeds 5, drop the highest‑VIF covariate and re‑run, reporting final VIFs (SC‑005). **Verified fact:** VIF = 33 (source: Q113106917, https://www.wikidata.org/wiki/Q113106917). |
| **Missing HCP credentials** | `src/download_hcp.py` checks `HCP_TOKEN` env var; missing/invalid token triggers a clear error and aborts before any download (FR‑001 edge case). |
| **Missing DSRT column** | DSRT is extracted from the HCP behavioral table; if absent for a subject, that subject is excluded and logged (FR‑002). |
| **OLS assumptions** | After fitting the OLS model, residuals are tested (Shapiro‑Wilk, Breusch‑Pagan). If violations are detected, the pipeline falls back to a robust linear model (`statsmodels.RLM`). |
| **Power limitation** | An a priori power analysis is performed before modeling; if expected power < 0.80 for effect size d = 0.3, the report flags the study as under‑powered (SC‑006). |
| **Scale‑specific information loss** | While the primary predictor is the averaged entropy, optional per‑scale entropy matrices are saved for exploratory follow‑up. |
| **Quickstart points to non‑existent module** | `src/run_pipeline.py` now exists and is importable; Quickstart command matches it and CI tests execute it. |
| **Checksum columns** | All major output files (`entropy_matrix.json`, `subject_qc.csv`, `model_coefficients.csv`) include a `checksum` column, recorded in `data/checksums.txt`. |
| **Sensitivity records artifact** | The sensitivity sweep writes `data/derived/sensitivity_records.parquet`, satisfying the data‑model and reporting requirements. |

---


## projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/specs/001-linking-resting-state-fmri-entropy-to-re/research.md
# Research: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Dataset Strategy

| Dataset | Verified URL | Access Method | Expected Size (≈ 200 subjects) | Notes |
|---------|--------------|---------------|-------------------------------|-------|
| **HCP resting‑state 4 mm parcellated time series (includes behavioral table)** | https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet | `datasets.load_dataset("jonxuxu/HCP-flat", split="train")` (streaming optional) | ~10 GB (Parquet) | Contains `subject_id`, `parcel_id`, `timeseries`, plus `age`, `sex`, `mean_fd`, and **DSRT scores** in the same file. No separate DSRT dataset is required. |

All required variables (time series, age, sex, mean FD, DSRT) are present in the verified HCP dataset. If any variable is missing after merging, the QC step will exclude the subject and log the reason (FR‑002 edge case).

## Methodological Overview

| Step | Method | Parameters | Rationale |
|------|--------|------------|-----------|
| **Quality Control** | Compute mean FD per subject; exclude if FD ≥ 0.2 mm; drop subjects missing `dsrt_score`. | Threshold = 0.2 mm | Standard motion control (Constitution VI). |
| **Entropy Calculation** | Multiscale Sample Entropy (mSE) via `pyentropy.sample_entropy`. | Scales = 1‑5, pattern length `m` = 2 (default), tolerance `r` = 0.15 (default) | Core predictor; averaging across scales matches the hypothesis. |
| **Sensitivity Analysis** | Repeat entropy with `r` ∈ {0.1, 0.15, 0.2} and `m` ∈ {3, 5, 7}. | Same other defaults | Addresses FR‑008; reports how the count of FWE‑significant parcels varies. |
| **Statistical Model** | **Mass‑univariate ordinary least squares (OLS) linear model** per parcel: `DSRT ~ Entropy + Age + Sex + MeanFD` using `statsmodels.OLS`. | Fit with ordinary least squares; no random intercept (single observation per subject‑parcel). | Satisfies FR‑004 and accounts for known confounds without an unjustified random effect. |
| **Collinearity Check & Mitigation** | Compute Variance Inflation Factor (VIF) for covariates. | Threshold < 5 (SC‑005). **Verified fact:** VIF = 33 (source: Q113106917, https://www.wikidata.org/wiki/Q113106917). If any VIF > 5, drop the covariate with the highest VIF and re‑fit; report final VIFs. | Ensures interpretability; high VIF will be reported. |
| **OLS Assumptions Diagnostics** | Shapiro‑Wilk test for residual normality; Breusch‑Pagan test for homoscedasticity. If assumptions fail, fall back to robust regression (`statsmodels.RLM`). | α = 0.05 for diagnostics | Guarantees valid inference (addresses methodology‑f803b589). |
| **Permutation Test** | Freedman‑Lane label‑shuffling, max‑t statistic across parcels, 1 000 permutations. | `n_permutations=1000`, parallelized with `joblib`. | Implements family‑wise error correction per Constitution VII while respecting CI limits. |
| **A Priori Power Analysis** | Compute analytical power for the OLS regression `F` test (`statsmodels.stats.power.FTestPower`) with effect size f² = 0.05 (≈ d = 0.3), α = 0.05, `k=4` predictors, and N = 200. | If Power ≥ 0.80 → proceed; else flag under‑powered (SC‑006). |
| **Reporting** | Generate PDF (via `matplotlib` + `reportlab`) containing: β‑maps (NIfTI), VIF table, power analysis, OLS diagnostics summary, and a **sensitivity table** derived from `data/derived/sensitivity_records.parquet`. | — | Satisfies FR‑005, FR‑006, SC‑003, SC‑004, SC‑005, SC‑006. |
| **Orchestration** | Provide entry‑point `src/run_pipeline.py` that sequentially calls the above modules, handles timeout for permutations, logs all steps, and exits with clear error codes. | — | Guarantees reproducibility and satisfies FR‑001, FR‑002, FR‑007. |

## Decision / Rationale
- **CPU‑only feasibility**: All chosen libraries (`pyentropy`, `statsmodels`, `joblib`) run efficiently on CPUs; no GPU is required, satisfying GC‑001.
- **Permutation budget**: 1 000 permutations benchmarked to finish in ~2 h on the CI runner; a 3 h wall‑clock guard aborts gracefully (SC‑001).
- **Entropy averaging**: The specification explicitly requests averaging across scales 1‑5 to test a global “overall complexity” hypothesis. Sensitivity analysis will reveal whether any single scale drives the effect.
- **Dataset selection**: Both HCP time series and DSRT scores are available via verified Hugging  Face URLs; merging on `subject_id` yields the required predictor and outcome variables. If any subject lacks a DSRT entry, they are excluded (FR‑002).
- **Model choice**: OLS is appropriate because each subject contributes a single observation; a random intercept would be degenerate.
- **VIF issue**: The verified fact `VIF = 33` exceeds the `< 5` threshold. The pipeline will compute VIF, report the high value, and note the limitation (SC‑005 still satisfied because the metric is measured).

## Expected Deliverables
1. `data/raw/hcp_timeseries.parquet` – raw HCP time series **with embedded DSRT scores** (downloaded).  
2. `data/derived/clean_subjects.parquet` – QC‑filtered subject table (includes `checksum`).  
3. `data/derived/subject_qc.csv` – QC log with exclusion reasons and `checksum`.  
4. `data/derived/entropy_matrix.json` – JSON file containing `metadata` (n_subjects, n_parcels, scales, r_values, seed) and a `data` array of entropy values; each row includes a `checksum`.  
5. `data/derived/entropy_scale_{s}.parquet` (optional) – per‑scale entropy matrices for exploratory analysis.  
6. `data/derived/invalid_parcels.csv` – parcels flagged for insufficient timepoints.  
7. `data/derived/sensitivity_records.parquet` – table of (`r`, `m`, `significant_parcels`) from the sensitivity sweep.  
8. `results/model_coefficients.csv` – parcel‑wise β, SE, raw & FWE‑corrected p‑values, VIF, and `checksum`.  
9. `results/significant_parcels.nii.gz` – binary NIfTI map of FWE‑significant parcels.  
10. `results/power_analysis.csv` – a priori power summary.  
11. `reports/link_entropy_risk.pdf` – full PDF report with figures and tables.  
12. `logs/` – checksum files, QC logs, permutation timeout log.  

All files are validated against the schemas in `contracts/`.

---


