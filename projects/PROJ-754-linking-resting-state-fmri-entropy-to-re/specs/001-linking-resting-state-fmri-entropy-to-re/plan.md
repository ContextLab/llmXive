# Implementation Plan: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Branch**: `001-resting-state-entropy-risk` | **Date**: 2026-07-03 | **Spec**: [spec.md](../specs/001-linking-resting-state-fmri-entropy-to-re/spec.md)  
**Input**: Feature specification from `/specs/001-linking-resting-state-fmri-entropy-to-re/spec.md`

## Summary
The project must () download a subset of 200 HCP minimally preprocessed 4 mm parcellated resting‑state fMRI time series together with Domain‑Specific Risk‑Taking (DSRT) scores, (2) compute multiscale sample entropy (mSE) for each cortical parcel (across multiple scales, averaged), and (3) fit a mass‑univariate **Ordinary Least Squares (OLS)** regression per parcel predicting DSRT from entropy while controlling for age, sex, and mean framewise displacement (FD). Results require permutation‑based family‑wise error (FWE) correction (using the Freedman-Lane method) and a sensitivity analysis over entropy tolerance `r` and pattern length `m`. All steps must run on a CPU‑only GitHub Actions runner within the free‑tier resource limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `numpy==1.26.*`, `pandas==2.2.*`, `nibabel==5.2.*` (for NIfTI handling)  
  - `pyentropy==0.4.*` (multiscale sample entropy)  
  - `statsmodels==0.14.*` (OLS regression, F-test power analysis)  
  - `nilearn==0.10.*` (parcellation utilities)  
  - `scikit-learn==1.5.*` (permutation utilities)  
  - `tqdm==4.66.*` (progress bars)  
- **Storage**: All raw and derived files under `data/` (parquet, NIfTI, CSV).  
- **Testing**: `pytest==8.2.*` with fixtures for a 5‑subject mini‑dataset.  
- **Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner.  
- **Project Type**: Research library/CLI.  
- **Constraints**: CPU‑only (GC‑001), ≤14 GB disk, ≤6 h runtime, ≤7 GB RAM.  
- **Scale/Scope**: 200 subjects × 400 parcels (Schaefer‑400) → ~80 k entropy values.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic (random seeds pinned). External datasets are fetched from the exact URLs listed in the "Verified datasets" block. |
| II. Verified Accuracy | Citations limited to the three verified dataset URLs; no unverified references are introduced. |
| III. Data Hygiene | Raw downloads are stored read‑only; each transformation writes a new file with a checksum recorded in `data/checksums.txt`. |
| IV. Single Source of Truth | Every figure/table in the final PDF is generated directly from the CSV/NIfTI outputs produced by the pipeline. |
| V. Versioning Discipline | `requirements.txt` pins exact package versions. **Post-processing script updates `state/projects/PROJ-754-...yaml` with SHA-256 hashes of all artifacts upon successful completion.** Git LFS stores large data artifacts. |
| VI. Neuroimaging Motion Control | Mean FD is computed per subject, used as a covariate, and low‑motion subset (FD < 0.2 mm) is re‑run as a robustness check. |
| VII. Permutation‑Based Multiple‑Comparison Correction | The statistical module implements max‑t permutation testing (5 000 shuffles, Freedman-Lane method) and thresholds at p < 0.05 FWE. |

All principles are satisfied; no violations identified.

## Phase Mapping (FR & SC Coverage)

| Phase | Description | FR IDs addressed | SC IDs addressed |
|-------|-------------|------------------|-------------------|
| **0 – Research** | Define dataset strategy, statistical methods, compute feasibility. | – | – |
| **1 – Data Acquisition** | Download HCP time series (200 subjects) and DSRT scores; **verify presence of required columns (subject_id, DSRT, age, sex, mean_fd)**; **exclude subjects with mean FD ≥ 0.2 mm**; exclude missing DSRT. | FR‑001, FR‑002, FR‑006 (observational framing) | SC‑001 (runtime), SC‑002 (memory) |
| **2 – Entropy Computation** | Compute multiscale sample entropy (scales 1‑5) per parcel; average across scales; flag parcels with insufficient points. | FR‑003, FR‑008 (sensitivity setup) | SC‑002 (memory), SC‑003 (output completeness) |
| **3 – Statistical Modeling** | Fit **OLS** model per parcel: `DSRT ~ Entropy + Age + Sex + MeanFD`. Compute VIF for covariates. Perform a sufficient number of **Freedman-Lane** permutations to build a max‑t null distribution. Apply FWE correction (p < 0.05). **Conduct post-hoc power analysis (F-test)**. | FR‑004, FR‑005, FR‑006, FR‑008 | SC‑004 (report), SC‑005 (VIF), SC‑006 (power) |
| **4 – Reporting & Sensitivity** | Produce PDF report, parcel‑wise NIfTI map of significant clusters, power analysis, and sensitivity tables over `r` ∈ {low, medium, high} and `m` ∈ {3,5,7}. | FR‑007 (CPU‑only), FR‑008 (execution) | SC‑003, SC‑004, SC‑005, SC‑006 |
| **5 – Quality Assurance** | Verify checksums, log exclusions, enforce graceful failure for missing credentials or timeout of permutation testing. | FR‑001 (credential handling), FR‑002 (missing DSRT), FR‑007 (CPU‑only) | SC‑001 (timeout handling) |

Each functional requirement (FR‑001 – FR‑008) and success criterion (SC‑001 – SC‑006) is explicitly mapped to a concrete phase or step.

## Timeline & Milestones (approximate, CI‑friendly)

| Milestone | Estimated CI Time* |
|-----------|--------------------|
| Data download & QC (Phase 1) | ≤30 min |
| Entropy computation on 5‑subject test set (Phase 2) | ≤15 min |
| Full entropy computation (200 subjects) | ≤90 min |
| Model fitting & permutation (Phase 3) | ≤180 min (≈3 h) |
| Reporting & sensitivity (Phase 4) | ≤30 min |
| **Total** | ≤4 h (comfortably under 6 h limit) |

\*Times are based on prior benchmarks of `pyentropy` on a multi-core CI runner.

## Risks & Mitigations
- **Permutation runtime**: If 5 000 permutations exceed 3 h, the script will monitor elapsed time and abort with a clear timeout error (SC‑001). Users can optionally reduce permutations via a CLI flag.
- **Memory spikes during entropy**: Computation proceeds parcel‑wise, loading one parcel's time series at a time to keep peak RAM < 4 GB (SC‑002).
- **Missing HCP credentials**: The download script checks for `HCP_TOKEN` env var; absent or invalid token triggers a graceful exit with an informative message (FR‑001 edge case).
- **Missing Data Columns**: The pipeline will explicitly check for required behavioral columns in the HCP dataset and fail gracefully if DSRT or covariates are absent.

---