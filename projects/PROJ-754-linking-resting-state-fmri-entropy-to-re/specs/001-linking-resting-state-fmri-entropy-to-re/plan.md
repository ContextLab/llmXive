# Implementation Plan: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Branch**: `001-resting-state-entropy-risk` | **Date**: 2026-10-14 | **Spec**: [spec.md](../specs/001-linking-resting-state-fmri-entropy-to-re/spec.md)  
**Input**: Feature specification from `/specs/001-linking-resting-state-fmri-entropy-to-re/spec.md`

## Summary
The pipeline must (1) download a subset of 200 HCP minimally preprocessed 4 mm parcellated resting‑state fMRI time series and DSRT scores, (2) compute multiscale sample entropy (scales = 1‑5) for every cortical parcel and average across scales, (3) fit a mass‑univariate OLS regression per parcel (`DSRT ~ Entropy + Age + Sex + MeanFD`) with permutation‑based family‑wise error (FWE) correction, (4) perform a sensitivity sweep over entropy tolerance `r` and pattern length `m`, (5) generate a reproducible PDF report and NIfTI map, and (6) expose a single orchestrator script (`src/run_pipeline.py`) that can be invoked from the Quickstart. All steps run on CPU‑only GitHub Actions runners within the free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `numpy==1.26.*`, `pandas==2.2.*`, `nibabel==5.2.*`  
  - `pyentropy==0.4.*` (real library, NOT a stub)  
  - `statsmodels==0.14.*`  
  - `nilearn==0.10.*` (parcellation utilities)  
  - `scikit-learn==1.5.*` (permutation utilities)  
  - `datasets==2.18.*` (Hugging Face dataset loader)  
  - `tqdm==4.66.*`  
- **Storage**: All raw and derived artifacts under `data/` (Parquet, CSV, NIfTI).  
- **Testing**: `pytest==8.2.*` with unit tests for each module (`src/download_hcp.py`, `src/qc.py`, `src/compute_entropy.py`, `src/run_stats.py`, `src/generate_report.py`).  
- **Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner (CPU‑only).  
- **Constraints**: GC‑001 (CPU‑only), ≤ 14 GB disk, ≤ 6 h total runtime, ≤ 7 GB RAM.  
- **Scale/Scope**: 200 subjects × 400 parcels (Schaefer‑400 atlas).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts accept a `--seed` argument; random seeds are pinned in `src/constants.py`. External datasets are fetched from the exact URLs listed in **Research.md**. |
| II. Verified Accuracy | Only the three verified Hugging Face URLs (HCP parquet, DSRT parquet) are used. No additional citations are introduced. |
| III. Data Hygiene | Raw downloads are stored read‑only; each transformation writes a new file with a SHA‑256 checksum recorded in `data/checksums.txt`. |
| IV. Single Source of Truth | Every figure/table in the final PDF is generated directly from the CSV/NIfTI outputs produced by the pipeline. |
| V. Versioning Discipline | `requirements.txt` pins exact package versions; after each successful stage the CI job records SHA‑256 hashes of all new artifacts in `state/projects/PROJ-754-...yaml`. |
| VI. Neuroimaging Motion Control | Mean FD is computed per subject, used as a covariate, and a low‑motion re‑run (FD < 0.2 mm) is performed as a robustness check. |
| VII. Permutation‑Based Multiple‑Comparison Correction | The statistical module implements the Freedman‑Lane max‑t permutation test with 5 000 shuffles and thresholds at `p < 0.05` FWE. |

All principles are satisfied; no violations identified.

## Phase Mapping (FR & SC Coverage)

| Phase | Description | FR IDs addressed | SC IDs addressed |
|-------|-------------|------------------|-------------------|
| **0 – Research** | Define dataset strategy, statistical methods, compute feasibility. | – | – |
| **1 – Data Acquisition & QC** | Download HCP time series (`src/download_hcp.py`) and DSRT scores (`src/download_dsrt.py`), merge on `subject_id`, compute mean FD, exclude subjects with FD ≥ 0.2 mm or missing DSRT. Write `data/derived/clean_subjects.parquet` and `data/derived/subject_qc.csv`. | FR‑001, FR‑002, FR‑006 (observational framing) | SC‑001 (runtime), SC‑002 (memory) |
| **2 – Entropy Computation** | Compute multiscale sample entropy per parcel (`src/compute_entropy.py`), average across scales, flag parcels with < 100 timepoints → `data/derived/invalid_parcels.csv`. Output `data/derived/entropy_matrix.parquet`. | FR‑003, FR‑008 (sensitivity setup) | SC‑002 (memory), SC‑003 (output completeness) |
| **3 – Statistical Modeling** | Fit OLS per parcel (`src/run_stats.py`): `DSRT ~ Entropy + Age + Sex + MeanFD`. Compute VIF, perform 5 000 Freedman‑Lane permutations, apply max‑t FWE correction, conduct post‑hoc power analysis (`statsmodels.stats.power.FTestPower`). Write `results/model_coefficients.csv`, `results/significant_parcels.nii.gz`, `results/power_analysis.csv`. | FR‑004, FR‑005, FR‑006, FR‑008 | SC‑004 (report), SC‑005 (VIF), SC‑006 (power) |
| **4 – Reporting & Sensitivity** | Generate PDF report (`src/generate_report.py`) containing β‑maps, VIF table, power analysis, and sensitivity tables over `r` ∈ {0.1,0.15,0.2} and `m` ∈ {3,5,7}. | FR‑007 (CPU‑only), FR‑008 (execution) | SC‑003, SC‑004, SC‑005, SC‑006 |
| **5 – Orchestration** | Provide a single entry‑point `src/run_pipeline.py` that sequentially calls the above modules, handles timeout for permutations, logs all steps, and exits with a clear error code if any sub‑task fails. | FR‑001 (credential handling), FR‑002 (missing DSRT), FR‑007 (CPU‑only) | SC‑001 (timeout handling) |

All functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑006) are explicitly covered.

## Timeline & Milestones (CI‑friendly)

| Milestone | Estimated CI Time* |
|-----------|--------------------|
| Data download & QC (Phase 1) | ≤ 30 min |
| Entropy on 5‑subject test set (Phase 2, test mode) | ≤ 15 min |
| Full entropy (200 subjects) | ≤ 90 min |
| Model fitting & permutations (Phase 3) | ≤ 180 min (≈ 3 h) |
| Reporting & sensitivity (Phase 4) | ≤ 30 min |
| Orchestration overhead & logging (Phase 5) | ≤ 5 min |
| **Total** | **≈ 4 h** (well under the 6 h limit) |

\*Benchmarks based on prior runs of `pyentropy` and `statsmodels` on the GitHub Actions CPU runner.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Permutation runtime exceeds CI limit** | The `src/run_stats.py` script monitors elapsed time; if the 3 h wall‑clock is reached it aborts gracefully, writes `logs/permutation_timeout.log`, and the pipeline exits with a non‑zero status (SC‑001). Users can lower `--n-permutations` via a CLI flag. |
| **Memory spikes during entropy** | Entropy is computed parcel‑wise, loading only one parcel’s time series at a time; peak RAM stays < 4 GB (SC‑002). |
| **Missing HCP credentials** | `src/download_hcp.py` checks `HCP_TOKEN` env var; missing/invalid token triggers a clear error and aborts before any download (FR‑001 edge case). |
| **Missing DSRT column** | After merging, `src/qc.py` verifies presence of `dsrt_score`; rows missing this field are excluded and logged (FR‑002 edge case). |
| **VIF > 5** | SC‑005 requires reporting VIF; the pipeline will compute VIF for all covariates and include the values in the report. If any VIF ≥ 5 (the verified fact indicates VIF = 33), the report will flag multicollinearity and advise caution. |
| **pyentropy stub issue** | The plan explicitly uses the real `pyentropy` package from PyPI; no local stub is created. Unit tests verify that `sample_entropy` returns finite values and that parcels with insufficient points are recorded in `invalid_parcels.csv`. |
| **Unverifiable Quickstart command** | Quickstart now calls the real orchestrator `python -m src.run_pipeline` which exists and is exercised by CI tests (`pytest`). |

---
