# Data Model: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Overview

This document defines the data structures used throughout the pipeline, from raw downloads to final statistical outputs. All data is stored in `data/` (raw/processed) and `output/`. New fields capture scale‑specific entropy, resampling validation metrics, noise‑variance, power, and runtime measurements required by FR‑009, SC‑006, and SC‑007.

## Entities

### 1. Subject
Represents a single participant in the HCP cohort.
* **ID**: `sub_XXXX` (string)
* **Age**: Integer (years)
* **Sex**: String ("M", "F")
* **MeanFD**: Float (mm) – Framewise displacement.
* **DSRT_Score**: Float – Domain‑Specific Risk‑Taking score.
* **NoiseVariance**: Float – Variance of residuals after nuisance regression (FR‑009).
* **Status**: "valid" or "excluded" (if MeanFD ≥ 0.2 mm or missing DSRT).

### 2. Parcel
Represents a cortical region (e.g., Schaefer‑400).
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
  * `scales`: List of integers `[1,2,3,4,5]`
  * `r_values`: List of floats `[0.1,0.15,0.2]`
  * `seed`: Integer
  * `includes_noise_variance`: Boolean
* **ValidationMetrics** *(optional)*:
  * `resampling_correlation`: Float – Pearson r between 2 mm and 4 mm entropy for validation subjects.
  * `ks_pvalue`: Float – KS test p‑value against literature benchmark.
  * `literature_match_flag`: Boolean – True if both validation criteria pass.

### 4. StatisticalResult
Output of the mass‑univariate analysis.
* **Parcel_ID**: Integer
* **Beta**: Float – Regression coefficient (entropy → DSRT).
* **SE**: Float – Standard error.
* **P_Value_Raw**: Float – Uncorrected p‑value.
* **P_Value_FWE**: Float – Permutation‑based FWE corrected p‑value.
* **Significant**: Boolean – True if `P_Value_FWE` < 0.05.
* **VIF**: Float – Variance Inflation Factor for covariates.
* **PartialCorr_Entropy_DSRT** *(optional)*: Float – Partial correlation controlling for NoiseVariance.

### 5. RuntimeMetrics
* **TotalSeconds**: Float – Wall‑clock time for the entire pipeline.
* **PermutationSeconds**: Float – Time spent in the permutation loop.
* **PeakRAM_GB**: Float – Peak RAM usage during execution.

### 6. PowerMetrics
* **EstimatedPower**: Float – Proportion of Monte‑Carlo simulations that yielded at least one significant parcel (target ≥ 0.80).

## Data Flow

1. **Raw**: `data/raw/hcp_<subject>_ptseries.nii.gz`, `data/raw/DSRT_scores.csv`.
2. **Processed**: `data/processed/entropy_matrix.npy`, `data/processed/entropy_scale_{m}_r{r}.npy`, `data/processed/subject_qc.csv`, `data/processed/noise_variance.npy`.
3. **Results**: `output/results.csv`, `output/association_map.nii.gz`, `output/runtime_log.json`, `output/power_metrics.json`, `output/resampling_validation.json`.

All files are version‑hashed and checksummed per the Constitution.
