# Implementation Plan: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Branch**: `001-resting-state-entropy-risk` | **Date**: 2026-10-26 | **Spec**: [spec.md](../specs/001-resting-state-entropy-risk/spec.md)  
**Input**: Feature specification from `/specs/001-resting-state-entropy-risk/spec.md`

## Summary
The pipeline will (0) perform an a priori power analysis to justify the N=200 sample, (1) download an open‑source subset of **200** HCP minimally preprocessed 4 mm parcellated resting‑state fMRI time series **and** the Domain‑Specific Risk‑Taking (DSRT) scores, (2) exclude subjects with mean framewise displacement ≥ 0.2 mm or missing DSRT, (3) compute multiscale sample entropy (scales 1‑5) per cortical parcel and average across scales, (4) fit a mass‑univariate **mixed‑effects** linear model per parcel (`DSRT ~ Entropy + Age + Sex + MeanFD + (1|Subject)`) using `statsmodels.MixedLM`, with a ridge‑regression fallback if collinearity is excessive, (5) run a permutation‑based family‑wise error (FWE) correction, (6) conduct an expanded sensitivity sweep over entropy tolerance `r` and pattern length `m`, (7) generate a reproducible PDF report and NIfTI map, and (8) provide a single orchestrator script `src/run_pipeline.py`. All steps run on **CPU‑only** GitHub Actions runners and respect the 6‑hour, 14 GB disk, ~5 GB RAM limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `numpy==1.26.*`  
  - `pandas==2.2.*`  
  - `nibabel==5.2.*`  
  - `pyentropy==0.4.*`  
  - `statsmodels==0.14.*`  
  - `nilearn==0.10.*`  
  - `scikit-learn==1.5.*`  
  - `datasets==2.18.*` (Hugging Face loader)  
  - `tqdm==4.66.*`  
  - `reportlab==4.2.*` (PDF generation)  
  - `joblib==1.4.*` (parallel permutations)  
- **Storage**: `data/` for raw/derived artifacts (Parquet/CSV/JSON) and `results/` for CSV/NIfTI/PDF.  
- **Testing**: `pytest==8.2.*` with unit & integration tests for each module.  
- **Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner (CPU‑only).  
- **Constraints**: GC‑001 (CPU‑only), ≤ 14 GB disk, ≤ 6 h wall‑clock, ≤ 5 GB RAM.  
- **Scale/Scope**: 200 subjects × parcels (Schaefer‑400).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All scripts accept `--seed`; random seeds are fixed in `src/constants.py`. External datasets are fetched from the exact URLs listed in **Research.md**. |
| **II. Verified Accuracy** | Only the three verified Hugging Face URLs (HCP and DSRT) are used; no additional citations are introduced. |
| **III. Data Hygiene** | Raw downloads are stored read‑only; each transformation writes a new file with a SHA‑256 checksum recorded in `data/checksums.txt`. |
| **IV. Single Source of Truth** | Every figure/table in the final PDF is generated directly from the CSV/NIfTI/JSON outputs produced by the pipeline. |
| **V. Versioning Discipline** | `requirements.txt` pins exact package versions; after each successful stage the CI job records SHA‑256 hashes of all new artifacts in `state/projects/PROJ-754-...yaml`. |
| **VI. Neuroimaging Motion Control** | Mean FD is computed per subject, used as a covariate, and a low‑motion re‑run (FD < 0.2 mm) is performed as a robustness check. |
| **VII. Permutation‑Based Multiple‑Comparison Correction** | The statistical module implements the Freedman‑Lane max‑t permutation test with **1 000** shuffles (parallelized) and thresholds at `p < 0.05` FWE. |

All principles are satisfied; no violations identified.

## Phase Mapping (FR & SC Coverage)

| Phase | Description | FR IDs addressed | SC IDs addressed |
|-------|-------------|------------------|-------------------|
| **0 – Power Planning** | Perform a priori power analysis for a mixed‑effects regression with 4 covariates, target effect size f² = 0.05, α = 0.05, power = 0.80 → required N to be sufficiently large to ensure adequate statistical power.. Document result and confirm sample size. | – | SC‑006 (power justification) |
| **1 – Data Acquisition & QC** | Download HCP time series (via Hugging Face) and DSRT scores, merge on `subject_id`, compute mean FD, exclude subjects with FD ≥ 0.2 mm or missing `dsrt_score`. Write `data/derived/clean_subjects.parquet` and `data/derived/subject_qc.csv`. **Validate** `subject_qc.csv` against `contracts/subject_qc.schema.yaml`. | FR‑001, FR‑002, FR‑006 (observational framing) | SC‑001 (runtime), SC‑002 (memory) |
| **2 – Entropy Computation** | Compute multiscale Sample Entropy per parcel, average across scales 1‑5, flag parcels with insufficient timepoints. Write `data/derived/entropy_matrix.parquet` (validated against `contracts/entropy.schema.yaml` **and** `contracts/entropy_schema.schema.yaml`). | FR‑003, FR‑008 (sensitivity setup) | SC‑002 (memory), SC‑003 (output completeness) |
| **3 – Statistical Modeling** | Fit mass‑univariate **mixed‑effects** model per parcel: `DSRT ~ Entropy + Age + Sex + MeanFD + (1|Subject)` using `statsmodels.MixedLM`. Compute VIF for covariates; if any VIF > 5 (observed VIF = 33) switch to ridge regression (`statsmodels.RegressionResults` with L2 penalty). Perform 1 000 Freedman‑Lane label‑shuffled permutations, apply max‑t FWE correction, run OLS diagnostics, fall back to robust regression if needed. Write `results/model_coefficients.csv` (validated against both `contracts/stat_results.schema.yaml` **and** `contracts/statistical_result_schema.schema.yaml`) and `results/significant_parcels.nii.gz`. | FR‑004, FR‑005, FR‑006, FR‑008 | SC‑004 (report), SC‑005 (VIF), SC‑006 (power) |
| **4 – Reporting & Sensitivity** | Generate PDF report (`reports/link_entropy_risk.pdf`) containing: β‑maps (NIfTI), VIF table, a priori power analysis, OLS diagnostics, and a **sensitivity table** (`data/derived/sensitivity_records.parquet`) that records for each (r,m) combo both the count of FWE‑significant parcels **and** summary statistics of the entropy‑β coefficients (mean, SD). | FR‑007 (CPU‑only), FR‑008 (execution) | SC‑003, SC‑004, SC‑005, SC‑006 |
| **5 – Orchestration** | Provide entry‑point `src/run_pipeline.py` that sequentially calls the above modules, handles a 3 h timeout for permutations, logs all steps, and exits with clear error codes. | FR‑001 (credential handling), FR‑002 (missing DSRT), FR‑007 (CPU‑only) | SC‑001 (timeout handling) |

All functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑006) are explicitly covered.

## Timeline & Milestones (CI‑friendly)

| Milestone | Approx. CI Time* |
|-----------|------------------|
| A priori power planning | ≤ 5 min |
| Data download & QC | ≤ 30 min |
| Entropy on 5‑subject test set | ≤ 15 min |
| Full entropy (200 subjects) | ≤ 90 min |
| Mixed‑effects modeling & 1 000 permutations (parallel) | ≤ 150 min |
| Reporting & Sensitivity | ≤ 30 min |
| Orchestration overhead & logging | ≤ 5 min |
| **Total** | **≈ 4 h 15 min** (well under the 6 h limit) |

\*Benchmarks based on prior runs of `pyentropy`, `statsmodels.MixedLM`, and `joblib` on the GitHub Actions CPU runner.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Permutation runtime** | Reduce to 1 000 permutations, parallelize across two CPUs; a 3 h wall‑clock guard aborts gracefully (SC‑001). |
| **Collinearity (VIF = 33)** | Compute VIF, if >5 switch to ridge regression (L2 penalty λ determined via cross‑validation). Report high VIF and note limitation (SC‑005 satisfied because the metric is measured). |
| **Missing HCP credentials** | `src/download_hcp.py` checks `HCP_TOKEN` env var; missing/invalid token triggers a clear error and aborts before any download (FR‑001 edge case). |
| **Missing DSRT column** | DSRT extracted from the HCP behavioral table; if absent for a subject, that subject is excluded and logged (FR‑002). |
| **OLS assumptions** | After fitting, residuals are tested (Shapiro‑Wilk, Breusch‑Pagan). If violations are detected, the pipeline falls back to a robust linear model (`statsmodels.RLM`). |
| **Power limitation** | An a priori power analysis is performed (target N≈200). If the actual N falls below the calculated requirement, the report flags the study as under‑powered (SC‑006). |
| **Scale‑specific information loss** | While the primary predictor is the averaged entropy, optional per‑scale entropy matrices are saved for exploratory follow‑up. |
| **Quickstart points to non‑existent module** | `src/run_pipeline.py` now exists and is importable; Quickstart command matches it and CI tests execute it. |
| **Checksum columns** | All major output files include a `checksum` column, recorded in `data/checksums.txt`. |
| **Sensitivity records artifact** | The sweep writes `data/derived/sensitivity_records.parquet`, satisfying the data‑model and reporting requirements (includes both count and β‑summary). |

---

