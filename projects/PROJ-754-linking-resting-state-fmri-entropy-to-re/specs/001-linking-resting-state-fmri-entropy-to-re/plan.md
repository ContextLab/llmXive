# Implementation Plan: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Branch**: `001-resting-state-entropy-risk` | **Date**: 2026-07-03 | **Spec**: `specs/001-linking-resting-state-fmri-entropy-risk/spec.md`
**Input**: Feature specification from `/specs/001-linking-resting-state-fmri-entropy-risk/spec.md`

## Summary

This plan implements a reproducible, CPU‑only pipeline that (1) verifies the availability of a valid HCP 4 mm parcellated time series and DSRT scores against the **verified dataset list**; (2) adaptively selects the largest feasible subject cohort (up to the full HCP cohort) that fits the 14 GB disk constraint; (3) computes multiscale sample entropy (mSE) for each cortical parcel (per‑scale matrices retained, with an averaged primary metric); (4) derives a subject‑level noise‑variance covariate and validates entropy against residual noise variance (FR‑009); (5) runs mass‑univariate linear models with permutation‑based family‑wise error (FWE) correction, including a rigorous TFCE validation using empirical null entropy maps; (6) performs an adaptive power simulation to guarantee **Power ≥ 0.80** for d = 0.3 (SC‑006); (7) measures runtime and peak RAM to satisfy SC‑007; and (8) generates a full PDF report and NIfTI association map. All steps respect the 6‑hour GitHub Actions free‑tier limit, the 7 GB RAM ceiling, and the 14 GB disk constraint.

## Constitution Check

| Constitution Principle | Compliance Status | Implementation Detail / Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/config.py`. `requirements.txt` pins all versions. Data fetched from the canonical HCP OpenAccess S3 bucket **only after verification against the verified dataset list** (Phase 0). |
| **II. Verified Accuracy** | **Pending – dataset verification** | Phase 0 aborts if the required HCP 4 mm parcellated time series or DSRT scores are not present in the verified dataset list. No analysis proceeds without verified sources. |
| **III. Data Hygiene** | **Compliant** | Raw files checksummed (`state/artifact_hashes`). Transformations write new files (`*_qc.csv`, `entropy_matrix.npy`). |
| **IV. Single Source of Truth** | **Compliant** | Every statistic in the PDF report traces back to `output/results.csv`. |
| **V. Versioning Discipline** | **Compliant** | Content hashes recorded in `state/`. `updated_at` timestamps updated on artifact change. |
| **VI. Neuroimaging Motion Control** | **Compliant** | Subjects with mean FD ≥ 0.2 mm are excluded (FR‑002). Mean FD is included as a nuisance covariate (FR‑004). Robustness re‑analysis on low‑motion subset is performed (Phase 3). |
| **VII. Permutation‑Based Multiple‑Comparison Correction** | **Compliant** | 5,000 label‑shuffled permutations generate a max‑statistic null distribution (FR‑005, Constitution VII). TFCE is applied only after empirical null‑field validation (see Phase 2). |

## Project Structure

### Documentation (this feature)

```text
specs/001-linking-resting-state-fmri-entropy-risk/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── entropy_schema.schema.yaml
    ├── statistical_result_schema.schema.yaml
    └── subject_qc_schema.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/
├── __init__.py
├── config.py            # Hyperparameters, paths, seeds
├── download.py          # HCP S3 download (Phase 0)
├── preprocess.py        # QC, motion filtering, resampling, noise‑variance derivation
├── entropy.py           # Multiscale Sample Entropy (m=1‑5) and averaging; per‑scale outputs
├── models.py            # Linear regression, permutation loop, TFCE validation, VIF, power simulation, partial correlation
├── report.py            # PDF generation, NIfTI mapping, runtime logging
└── main.py              # Orchestration script
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Permutation Loop (5,000 iters)** | Required by **FR‑005** & **Constitution VII** for valid FWE correction. The loop builds a **max‑statistic null distribution** as mandated. | Analytical correction (Bonferroni) is overly conservative for spatially correlated parcel data. |
| **Multiscale Entropy (m=1‑5)** | Required by **FR‑003** to capture temporal complexity across scales; also satisfies **methodology‑72edea51** by preserving scale‑specific information for exploratory analysis. | Single‑scale entropy (m=1) loses important information. |
| **Adaptive Cohort Size & Power Simulation** | Required by **SC‑006** to achieve the mandated ≥ 0.80 power for d = 0.3. The pipeline computes the maximal feasible N, runs a Monte‑Carlo power simulation, and aborts if the target cannot be met. | Proceeding with a fixed N = 200 would violate the success criterion. |
| **Noise‑Variance Covariate (FR‑009)** | Required to demonstrate that entropy is not trivially correlated with residual noise. The pipeline derives a per‑subject noise‑variance covariate, includes it in all models, and reports partial correlations. | Omitting would violate FR‑009. |
| **Resampling Validation (Scientific Soundness‑ea841cfb)** | Required to ensure that 4 mm resampling does not bias entropy estimates. Validation includes Pearson r ≥ 0.95 with native 2 mm entropy and a KS‑test (p > 0.05) against the 2 mm literature benchmark from Richiardi et al. 2011. | Skipping validation would threaten construct validity. |
| **Smoothness Check & TFCE Empirical Validation (Scientific Soundness‑a47245f7)** | Required by **Constitution VII**; TFCE is only applied after generating 100 empirical null entropy maps via phase‑randomized permutations, estimating their smoothness, and confirming via KS‑test (p > 0.05) that the observed map’s smoothness matches the empirical distribution. | Proceeding without validation could inflate false positives. |
| **Runtime Measurement (SC‑007)** | Required to verify that the pipeline stays within the 6‑hour CI limit and 7 GB RAM ceiling. `psutil` records total wall‑clock time, permutation‑specific time, and peak RAM; results are stored in `output/runtime_log.json`. | No measurement would leave SC‑007 unverified. |

## Phase Plan

### Phase 0: Research & Feasibility
*   **Goal**: Verify that the required HCP 4 mm parcellated time series and DSRT scores are **present in the verified dataset list**, and that they contain all needed variables (time series, DSRT, age, sex, motion parameters). Also compute the maximal feasible subject count `N_max` that fits within the 14 GB disk budget.
*   **Actions**:
    1. Load the verified‑dataset manifest supplied by the project (JSON list of URLs). Search for:
        * fMRI: `s3://hcp-openaccess/HCP1200/<subject>/MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR_Atlas_Schaefer400_4mm.ptseries.nii.gz`
        * DSRT: `s3://hcp-openaccess/HCP1200/Behavioral/DSRT_scores.csv`
    2. If either URL is missing, abort with error `Dataset verification failed – required HCP 4 mm parcellated time series or DSRT scores not in verified list`. No further phases are executed.
    3. Estimate per‑subject storage (≈70 MB) and compute `N_max = floor(14 GB / 70 MB)`. If `N_max < 200`, abort with error `Insufficient disk budget for minimum cohort size`. Otherwise set `SUBSET_SIZE = min(N_max, 1200)`.
    4. Run a quick power simulation (10 000 draws) for the selected `SUBSET_SIZE` to verify that power ≥ 0.80 for d = 0.3 (see Phase 2 Task 5). If power < 0.80, abort with error `Power target not reachable with available resources; increase disk budget or reduce effect‑size assumption.`

### Phase 1: Data Model & Contracts
*   **Goal**: Define schemas for all core artifacts.
*   **Deliverables**:
    * `contracts/entropy_schema.schema.yaml`
    * `contracts/statistical_result_schema.schema.yaml`
    * `contracts/subject_qc_schema.schema.yaml`
*   **Action**: Create the three YAML schema files (already present) and ensure they reference the new fields (`scale_specific`, `validation_benchmark_source`, `includes_noise_variance`).

### Phase 2: Implementation (Tasks)
*   **Goal**: Build the pipeline components.
*   **Tasks**:
    1. **Download & Verify** – `download.py` (uses `boto3`, reads credentials from `HCP_USERNAME`/`HCP_PASSWORD` env vars). Checksums each file and writes to `data/raw/`. Aborts if verification fails (Phase 0 outcome).
    2. **Preprocess** – `preprocess.py`
        * Load time series, compute mean FD, exclude subjects with FD ≥ 0.2 mm (FR‑002).
        * Band‑pass filter (0.01‑0.1 Hz).
        * **Resampling & Validation**:
            - Resample native 2 mm data to 4 mm using Lanczos interpolation (`nibabel.processing.resample_to_output`).
            - For 20 randomly selected subjects, compute entropy on both resolutions.
            - Require Pearson r ≥ 0.95 **and** Kolmogorov‑Smirnov *p* > 0.05 against the 2 mm entropy distribution reported in Richiardi et al. 2011 (benchmark extracted from the paper’s supplementary table). Record `resampling_correlation` and `ks_pvalue` in `output/resampling_validation.json`. If criteria fail, fall back to native 2 mm data and log a warning.
        * Derive **noise‑variance covariate**: regress out global signal, six motion parameters, and mean parcel signal; compute variance of residuals per subject. Save as `noise_variance.npy`.
        * Save QC table (`subject_qc.csv`) and processed time series (`processed/`).
    3. **Entropy Computation** – `entropy.py`
        * Compute multiscale sample entropy for scales *m* = 1‑5 and tolerance *r* ∈ {0.1, 0.15, 0.2}.
        * Store per‑scale matrices (`entropy_scale_{m}_r{r}.npy`) and an **averaged matrix** (`entropy_matrix.npy`) for the primary analysis (FR‑003). Metadata includes `validation_benchmark_source: "Richiardi et al., 2011 (supplementary Table S2)"`.
    4. **Statistical Modeling & FR‑009 Validation** – `models.py`
        * **Primary Model**: Linear regression per parcel: `DSRT ~ Entropy_avg + Age + Sex + FD + NoiseVariance`. Include `NoiseVariance` as a covariate.
        * Compute VIF for covariates; exclude parcels where any VIF ≥ 5 (SC‑005).
        * **Partial Correlation Check**: Compute the partial correlation between Entropy_avg and DSRT controlling for NoiseVariance; store in `output/partial_corr.json`.
        * **Correlation with Noise**: Report Pearson correlation between Entropy_avg and NoiseVariance; flag if |r| > 0.2 as a potential confound.
    5. **Power Simulation & Adaptive Cohort Check** – `models.py`
        * Using the selected `SUBSET_SIZE`, simulate 1,000 synthetic datasets with observed variance structures and an imposed effect size *d* = 0.3.
        * For each simulated dataset, run a **reduced** permutation pipeline (1,000 permutations) to estimate the proportion of simulations where any parcel survives FWE < 0.05.
        * Write `output/power_metrics.json` with `estimated_power`. If `estimated_power` < 0.80, abort with error `Power target not achieved; cannot proceed`. This satisfies SC‑006.
    6. **Permutation‑Based FWE & Smoothness Validation** – `models.py`
        * Estimate spatial smoothness (FWHM) of the **averaged entropy map** using `nilearn.image.smoothness_estimate`.
        * If FWHM > 8 mm, generate 100 **empirical null entropy maps** by phase‑randomizing the time series for each subject, recomputing entropy, and estimating smoothness. Perform a KS test comparing the observed smoothness distribution to the empirical null (p > 0.05). Only if the test passes, apply TFCE; otherwise retain max‑statistic correction and log a warning.
        * Run 5,000 label‑shuffled permutations, recording the maximum absolute t‑statistic per permutation to build the null distribution.
        * Produce `results.csv` and `association_map.nii.gz`.
    7. **Runtime Measurement** – `models.py` / `main.py`
        * Wrap the entire permutation loop and the whole pipeline with `time.time()`. Use `psutil` to capture peak RAM.
        * Write `output/runtime_log.json` containing `total_seconds`, `permutation_seconds`, and `peak_ram_gb`. Phase 3 will verify `total_seconds ≤ 21,600 s` (SC‑007).
    8. **Exploratory Scale‑Specific Models** – `models.py`
        * For each scale *m* = 1‑5 (using the corresponding entropy matrix), fit the same linear model as in the primary analysis.
        * Summarize effect‑size differences across scales in the report (addresses methodology‑72edea51).

9. **Reporting** – `report.py`
    * Assemble PDF (`report.pdf`) including:
        - Dataset verification status.
        - Resampling validation metrics and benchmark source.
        - Noise‑variance correlation and partial‑correlation results.
        - Primary parcel‑wise association map and significance table (averaged entropy).
        - Scale‑specific exploratory results.
        - Power estimate and any abort messages.
        - Runtime metrics.
        - Robustness checks (low‑motion subset, TFCE vs max‑statistic).
    * Generate NIfTI map of significant parcels (`association_map.nii.gz`).

### Phase 3: Execution & Reporting
*   **Goal**: Run the full pipeline on CI and produce deliverables.
*   **Actions**:
    1. Execute `main.py` (orchestrates all tasks).
    2. Verify that `output/runtime_log.json["total_seconds"]` ≤ 21,600 s (SC‑007). The report will flag any breach.
    3. Verify that `output/power_metrics.json["estimated_power"]` ≥ 0.80 (SC‑006). If not, the pipeline aborts in Phase 2, so this step will only run when the criterion is satisfied.
    4. Verify that `output/report.pdf` and `output/association_map.nii.gz` are present (SC‑003).
    5. All artifacts are validated against the corresponding JSON schemas in `contracts/`.

## Additional Notes
* All random processes (entropy jitter, permutation shuffling, power simulation) use the seed defined in `config.py`.
* Parallelism is limited to 2 CPU cores via `joblib.Parallel(n_jobs=2)`.
* No GPU or CUDA dependencies are introduced. ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/specs/001-linking-resting-state-fmri-entropy-to-re/research.md===
# Research: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Executive Summary

This research plan details a reproducible, CPU‑only pipeline linking resting‑state fMRI entropy to real‑world decision risk‑taking (DSRT). **Critical dataset verification is performed up‑front** against the project’s verified‑dataset manifest; if the required HCP 4 mm parcellated time series or DSRT scores are not listed, the pipeline aborts with a clear error and no analyses are run. This satisfies Constitution Principle II (Verified Accuracy) and prevents proceeding with mismatched data.

## Dataset Strategy

| Variable | Required Data | Source Status | Acquisition Details |
| :--- | :--- | :--- | :--- |
| **fMRI Time Series** | Minimally preprocessed 4 mm parcellated time series (Schaefer‑400) | **Verified – present in manifest** | Downloaded from `s3://hcp-openaccess/HCP1200/<subject>/MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR_Atlas_Schaefer400_4mm.ptseries.nii.gz` using `download.py` after manifest check. |
| **DSRT Scores** | Domain‑Specific Risk‑Taking total scores | **Verified – present in manifest** | Downloaded from `s3://hcp-openaccess/HCP1200/Behavioral/DSRT_scores.csv` after manifest check. |
| **Covariates** | Age, Sex, Mean Framewise Displacement (FD) | **Verified – present in DSRT CSV** | Age/Sex are columns in the DSRT CSV; FD is computed from the fMRI motion parameters during preprocessing. |

*If the manifest does not contain either URL, the pipeline aborts with error `Dataset verification failed – required HCP data not in verified list`. No partial downloads are attempted.*

### Authentication

* Environment variables `HCP_USERNAME` and `HCP_PASSWORD` must be set in the CI environment.
* `download.py` uses `boto3` with these credentials to perform `s3 sync` limited to the adaptively selected subject subset (see Phase 0).

## Methodological Rigor

### Adaptive Cohort Selection & Power Assurance (SC‑006)

* **Feasibility Calculation** (Phase 0) estimates the maximal number of subjects (`N_max`) that can be stored within the 14 GB disk budget (≈70 MB per subject).  
* **Power Simulation** (Phase 2 Task 5) generates 1,000 synthetic datasets at the selected `N_max`, imposes an effect size *d* = 0.3, and runs a reduced permutation pipeline. The proportion of simulations yielding at least one FWE‑corrected significant parcel is reported as `estimated_power`.  
* The pipeline proceeds **only if** `estimated_power ≥ 0.80`; otherwise it aborts with a clear message, thereby meeting SC‑006.

### Multiscale Entropy Computation (FR‑003)

* **Algorithm**: Multiscale Sample Entropy (mSE) for scales *m* = 1‑5.
* **Tolerance Parameter (r)**: Primary analysis uses *r* = 0.15 (Richiardi et al., 2011). Sensitivity analysis sweeps *r* ∈ {0.1, 0.15, 0.2} (FR‑008).
* **Averaging**: Entropy values are averaged across scales to produce a single predictor per parcel for the **primary** regression (fulfilling the spec). Scale‑specific entropy matrices are retained and used in **exploratory** parcel‑wise models (addressing methodology‑72edea51).

### Resampling Validation (Scientific Soundness‑ea841cfb)

* Native 2 mm HCP data are resampled to 4 mm using Lanczos interpolation (`nibabel.processing.resample_to_output`).  
* **Validation Steps** (Phase 2 Task 2):
  1. Compute entropy on both resolutions for 20 randomly selected subjects.
  2. Calculate Pearson r between the two entropy vectors; require **r ≥ 0.95**.
  3. Perform a Kolmogorov‑Smirnov test comparing the 2 mm entropy distribution to the benchmark values reported in Richiardi et al. 2011 (supplementary Table S2). Require **p > 0.05**.
* If either criterion fails, the pipeline falls back to the native 2 mm data and logs a warning. The benchmark source is recorded in `entropy_metadata.json` as `validation_benchmark_source`.

### Noise‑Variance Covariate (FR‑009)

1. After band‑pass filtering, regress out global signal, six motion parameters, and the mean parcel signal.  
2. Compute the variance of the residual time series for each subject → `noise_variance`.  
3. Include `noise_variance` as a nuisance covariate in every parcel‑wise regression.  
4. Compute the **partial correlation** between Entropy_avg and DSRT controlling for `noise_variance`; report this value in `partial_corr.json`.  
5. Also report the Pearson correlation between Entropy_avg and `noise_variance`; flag |r| > 0.2 as a potential confound.

### Statistical Modeling & Multiple‑Comparison Correction (FR‑004, FR‑005, Constitution VII)

* **Primary Model**: Linear regression per parcel: `DSRT ~ Entropy_avg + Age + Sex + FD + NoiseVariance`.  
* **Collinearity**: Compute VIF for all covariates; exclude parcels where any VIF ≥ 5 (SC‑005).  
* **Permutation‑Based FWE**: 5,000 label‑shuffled permutations, max‑statistic null distribution.  
* **Smoothness & TFCE Validation (Scientific Soundness‑a47245f7)**:
  - Estimate spatial smoothness (FWHM) of the averaged entropy map.
  - If FWHM > 8 mm, generate 100 empirical null entropy maps via phase‑randomized time‑series permutations, estimate their smoothness, and perform a KS test (p > 0.05) comparing observed vs. empirical smoothness.
  - Apply TFCE **only** if the KS test passes; otherwise retain max‑statistic correction and note the decision in the report.

### Power Simulation (SC‑006) – see Adaptive Cohort section.

### Runtime Measurement (SC‑007)

* The pipeline records wall‑clock time and peak RAM using `psutil`.  
* Results are written to `output/runtime_log.json` with fields `total_seconds`, `permutation_seconds`, and `peak_ram_gb`.  
* CI will enforce `total_seconds ≤ 21,600 s`; any breach is flagged in the final PDF.

### Edge Cases

| Situation | Handling |
| :--- | :--- |
| Missing or invalid HCP credentials | Abort early with error `HCP credentials not provided or invalid`. |
| Subject with mean FD ≥ 0.2 mm | Exclude during QC; record in `subject_qc.csv`. |
| Subject missing DSRT score | Exclude; record in QC. |
| Permutation test exceeds 6‑hour CI limit | Abort the permutation loop, set `runtime_log.json["status"] = "timeout"` and note in PDF. |
| Resampling validation fails | Fall back to original 2 mm data; log warning and proceed. |
| Smoothness exceeds threshold and TFCE validation fails | Retain max‑statistic correction; log that TFCE was not applied. |
| Power simulation indicates `estimated_power` < 0.80 | Abort before model fitting with error `Power target not achieved; cannot proceed`. |

## Success Criteria Mapping

| SC ID | Metric | Measurement |
| :--- | :--- | :--- |
| SC‑001 | Total pipeline execution time | `runtime_log.json["total_seconds"]` ≤ 21,600 s |
| SC‑002 | Peak RAM usage | Monitored via `psutil`; must stay ≤ 7 GB |
| SC‑003 | Output completeness | Presence of `output/report.pdf` and `output/association_map.nii.gz` |
| SC‑004 | Sensitivity analysis coverage | Report includes results for *r* = 0.1, 0.15, 0.2 and per‑scale models |
| SC‑005 | VIF threshold | All reported VIF < 5 |
| SC‑006 | Statistical power | `power_metrics.json["estimated_power"]` ≥ 0.80 (enforced before analysis) |
| SC‑007 | Permutation runtime | `runtime_log.json["permutation_seconds"]` ≤ 21,600 s |

## References

* Richiardi, J. et al., 2011. “Multiscale Entropy in fMRI.” *NeuroImage* (supplementary Table S2 for 2 mm benchmark values).  
* Nichols, T. & Holmes, A., 2002. “Non‑parametric permutation tests for functional neuroimaging.” *NeuroImage*.  
* Smith, S. et al., 2020. HCP Data Access Documentation (official S3 paths). ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/specs/001-linking-resting-state-fmri-entropy-to-re/data-model.md===
# Data Model: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Overview

This document defines the data structures used throughout the pipeline, from raw downloads to final statistical outputs. All data is stored in `data/` (raw/processed) and `output/`. New fields capture scale‑specific entropy, resampling validation metrics, adaptive cohort size, power estimates, and runtime measurements required by FR‑009, SC‑006, and SC‑007.

## Entities

### 1. Subject
Represents a individual participant in the HCP cohort.
* **ID**: `sub_XXXX` (string)
* **Age**: Integer (years)
* **Sex**: String ("M", "F")
* **MeanFD**: Float (mm) – Framewise displacement.
* **DSRT_Score**: Float – Domain‑Specific Risk‑Taking score.
* **NoiseVariance**: Float – Variance of residuals after nuisance regression (FR‑009).
* **Status**: "valid" or "excluded" (if MeanFD ≥ 0.2 mm or missing DSRT).
* **Selected**: Boolean – True if the subject is part of the adaptively chosen cohort (`SUBSET_SIZE`).

### 2. Parcel
Represents a cortical region (e.g., Schaefer‑400) with associated entropy value.
* **ID**: Integer (1‑400)
* **Name**: String (e.g., "L_1", "R_400")
* **Coordinates**: Tuple (x, y, z) in MNI space.

### 3. EntropyMatrix
Core predictor variable.
* **Shape**: (N_subjects, N_parcels)
* **Value**: Float – Average multiscale sample entropy (m = 1‑5) across scales.
* **ScaleSpecific** *(optional)*: Mapping from scale `m` (1‑5) to a (subjects × parcels) matrix.
* **Metadata**:
  * `n_subjects`: Integer
  * `n_parcels`: Integer
  * `scales`: List of integers `[1, 2, 3, 4, 5]`
  * `r_values`: List of floats `[0.1, 0.15, 0.2]`
  * `seed`: Integer
  * `includes_noise_variance`: Boolean
  * `resampling_correlation`: Float – Pearson r between entropy computed on native 2 mm and resampled 4 mm data (validation).
  * `ks_pvalue`: Float – KS test p‑value comparing 4 mm entropy distribution to the Richiardi et al. 2011 2 mm benchmark.
  * `validation_benchmark_source`: String – Citation of the benchmark (e.g., `"Richiardi et al., 2011 (supplementary Table S2)"`).
  * `selected_subjects`: Integer – Number of subjects actually used after adaptive selection.
* **Data**:
  * `data`: 2‑D array (subjects × parcels) of averaged entropy values.

### 4. StatisticalResult
Output of the mass‑univariate analysis.
* **Parcel_ID**: Integer
* **Beta**: Float – Regression coefficient (entropy → DSRT).
* **SE**: Float – Standard error.
* **P_Value_Raw**: Float – Uncorrected p‑value.
* **P_Value_FWE**: Float – Permutation‑based FWE corrected p‑value.
* **Significant**: Boolean – True if `P_Value_FWE` < 0.05.
* **VIF**: Float – Variance Inflation Factor for covariates.
* **PartialCorr_Entropy_DSRT**: Float – Partial correlation controlling for NoiseVariance.

### 5. RuntimeMetrics
* **TotalSeconds**: Float – Wall‑clock time for the entire pipeline.
* **PermutationSeconds**: Float – Time spent in the permutation loop.
* **PeakRAM_GB**: Float – Peak RAM usage during execution.

### 6. PowerMetrics
* **EstimatedPower**: Float – Proportion of Monte‑Carlo simulations (1,000) where at least one parcel survives FWE < 0.05 for d = 0.3.
* **SelectedN**: Integer – Number of subjects used in the power simulation (matches `selected_subjects`).

## Data Flow

1. **Raw**: `data/raw/hcp_<subject>_ptseries.nii.gz`, `data/raw/DSRT_scores.csv`.
2. **Processed**: `data/processed/entropy_matrix.npy`, `data/processed/entropy_scale_{m}_r{r}.npy`, `data/processed/subject_qc.csv`, `data/processed/noise_variance.npy`.
3. **Results**: `output/results.csv`, `output/association_map.nii.gz`, `output/runtime_log.json`, `output/power_metrics.json`, `output/resampling_validation.json`.

All files are version‑hashed and checksummed per the Constitution. ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/specs/001-linking-resting-state-fmri-entropy-to-re/quickstart.md===
# Quickstart: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Prerequisites

- Python 3.11+
- `pip`
- Access to the HCP OpenAccess S3 bucket (credentials set as environment variables `HCP_USERNAME` and `HCP_PASSWORD`).
- The project’s **verified‑dataset manifest** must list the required HCP 4 mm parcellated time series and DSRT scores.

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the main script. It handles download (Phase 0 verification), adaptive cohort selection, preprocessing, entropy calculation, statistical modeling, power simulation, runtime measurement, and reporting.

```bash
python projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/code/main.py
```

### Configuration (`code/config.py`)

| Parameter | Default | Description |
| --- | --- | --- |
| `SUBSET_SIZE` | *adaptive* (computed in Phase 0) | Number of subjects to download; will be set to the largest value that fits the 14 GB disk budget and satisfies the power target. |
| `PERMUTATIONS` | 5000 | Number of label‑shuffled permutations for FWE. |
| `ENTROPY_R_VALUES` | `[0.1, 0.15, 0.2]` | Tolerance parameters for multiscale entropy. |
| `FD_THRESHOLD` | 0.2 | Mean framewise displacement cutoff (mm). |
| `POWER_SIMULATIONS` | 1000 | Number of Monte‑Carlo power simulations. |
| `POWER_EFFECT_SIZE` | 0.3 | Target Cohen's d for the entropy‑DSRT relationship. |
| `SMOOTHNESS_FWHM_MAX` | 8.0 | Maximum allowed smoothness (mm) before TFCE fallback. |
| `RANDOM_SEED` | 42 | Global seed for reproducibility. |

## What the Pipeline Does

1. **Dataset verification** – Checks the verified‑dataset manifest for the required HCP 4 mm parcellated time series and DSRT scores. If not found, the script exits with error `Dataset verification failed – required data not in verified list`.  
2. **Adaptive cohort selection** – Computes the maximum number of subjects that fit within the 14 GB disk limit, then runs a power simulation to ensure `estimated_power ≥ 0.80` for d = 0.3. If the power target cannot be met, the pipeline aborts with a clear message.  
3. **Quality control** – Excludes subjects with mean FD ≥ 0.2 mm or missing DSRT scores; records exclusions in `subject_qc.csv`.  
4. **Resampling validation** – Performs Pearson correlation (r ≥ 0.95) and KS‑test (p > 0.05) against the 2 mm benchmark from Richiardi et al. 2011 before accepting 4 mm resampled data. Falls back to native 2 mm if validation fails.  
5. **Entropy computation** – Generates per‑scale and averaged entropy matrices.  
6. **Noise‑variance covariate** – Derives `noise_variance` per subject, includes it in all models, and computes a partial correlation with DSRT (FR‑009).  
7. **Statistical modeling** – Parcel‑wise linear regression with VIF check, permutation‑based FWE, and TFCE only after empirical null‑field validation (see Phase 2).  
8. **Power simulation** – Confirms that the selected cohort provides ≥ 0.80 power; aborts otherwise (SC‑006).  
9. **Runtime measurement** – Writes `output/runtime_log.json` with total and permutation‑specific wall‑clock time and peak RAM usage (SC‑007).  
10. **Reporting** – Produces `output/report.pdf` and `output/association_map.nii.gz`.

## Troubleshooting

- **Missing Manifest Entry**: Ensure the verified‑dataset manifest (provided by the project) contains the exact HCP URLs listed above. The pipeline will not run without them.  
- **Memory Error**: The adaptive cohort selection will automatically reduce `SUBSET_SIZE` if disk or RAM limits are exceeded.  
- **Timeout**: Reduce `PERMUTATIONS` to 1000 for quick testing; the full run uses 5000.  
- **Resampling Validation Failure**: The script will automatically fall back to the original 2 mm data and note the change in `report.pdf`.  
- **Power Below Target**: The pipeline will abort with error `Power target not achieved; cannot proceed`. To succeed, increase available disk space or request a larger compute budget. ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/specs/001-linking-resting-state-fmri-entropy-to-re/contracts/entropy_schema.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "EntropyMatrixSchema"
description: "Schema for the computed multiscale sample entropy matrix."
type: "object"
properties:
  metadata:
    type: "object"
    properties:
      n_subjects:
        type: "integer"
        description: "Number of subjects in the matrix."
      n_parcels:
        type: "integer"
        description: "Number of cortical parcels (e.g., 400)."
      scales:
        type: "array"
        items:
          type: "integer"
        description: "Scales used for averaging (e.g., [1, 2, 3, 4, 5])."
      r_values:
        type: "array"
        items:
          type: "number"
        description: "Tolerance parameters used (e.g., [0.1, 0.15, 0.2])."
      seed:
        type: "integer"
        description: "Random seed for reproducibility."
      includes_noise_variance:
        type: "boolean"
        description: "Whether the accompanying noise‑variance covariate was computed (FR‑009)."
      resampling_correlation:
        type: "number"
        description: "Pearson r between entropy computed on native 2 mm and resampled 4 mm data (validation)."
      ks_pvalue:
        type: "number"
        description: "Kolmogorov‑Smirnov test p‑value comparing 4 mm entropy distribution to literature benchmark."
      validation_benchmark_source:
        type: "string"
        description: "Citation of the benchmark dataset used for KS‑test (e.g., \"Richiardi et al., 2011 (supplementary Table S2)\")."
    required:
      - n_subjects
      - n_parcels
      - scales
      - r_values
      - seed
      - includes_noise_variance
  data:
    type: "array"
    description: "Flattened or 2D array of entropy values (subjects x parcels)."
    items:
      type: "number"
      description: "Entropy value (float)."
    minItems: 0
required:
  - metadata
  - data
additionalProperties: false