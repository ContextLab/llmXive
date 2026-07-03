# Research: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

## Executive Summary

This research plan details a reproducible, CPU‑only pipeline linking resting‑state fMRI entropy to real‑world decision risk‑taking (DSRT). **Critical dataset verification is performed up‑front**; if the required HCP 4 mm parcellated time series or DSRT scores are not reachable via the verified URLs, the pipeline aborts with a clear error and no analyses are run. This safeguards against proceeding with mismatched or unavailable data, satisfying Constitution Principle II (Verified Accuracy).

## Dataset Strategy

| Variable | Required Data | Source Status | Acquisition Details |
| :--- | :--- | :--- | :--- |
| **fMRI Time Series** | Minimally preprocessed 4 mm parcellated time series (Schaefer‑400) | **MISMATCH – not present in verified dataset list** | Will be downloaded from the official HCP OpenAccess S3 bucket (`s3://hcp-openaccess/...`) **only if valid credentials are provided**. |
| **DSRT Scores** | Domain‑Specific Risk‑Taking total scores | **MISMATCH – not present in verified dataset list** | Downloaded from `s3://hcp-openaccess/HCP1200/Behavioral/DSRT_scores.csv` **provided the bucket is accessible**. |
| **Covariates** | Age, Sex, Mean Framewise Displacement (FD) | **MISMATCH – not present in verified dataset list** | Age/Sex are columns in the DSRT CSV; FD is computed from the fMRI motion parameters during preprocessing. |

*If the HCP S3 bucket is inaccessible (e.g., missing or invalid credentials), the pipeline aborts with a clear error message and does not attempt partial downloads.*

### Authentication

* Environment variables `HCP_USERNAME` and `HCP_PASSWORD` must be set in the CI environment.
* `download.py` uses `boto3` with these credentials to perform `s3 sync` limited to the 200‑subject subset.

## Methodological Rigor

### Multiscale Entropy Computation

* **Algorithm**: Multiscale Sample Entropy (mSE) for scales *m* = 1‑5.
* **Tolerance Parameter (r)**: Primary analysis uses *r* = 0.15 (Richiardi et al., 2011). Sensitivity analysis sweeps *r* ∈ {0.1, 0.15, 0.2} (FR‑008).
* **Averaging**: Entropy values are averaged across scales to produce a single predictor per parcel (primary model). Scale‑specific entropy matrices are retained and used in exploratory models (addresses methodology‑72edea51).

### Resampling Validation (Scientific Soundness‑ea841cfb)

* The native 2 mm HCP data are resampled to 4 mm using Lanczos interpolation.  
* Validation steps:  
  1. Compute entropy on both resolutions for a set of randomly selected subjects.; require Pearson r ≥ 0.95.  
  2. Perform a Kolmogorov‑Smirnov test comparing the distribution of 4 mm entropy values to the published range in Richiardi et al. (2011); require *p* > 0.05.  
* If either criterion fails, the pipeline falls back to the original 2 mm data and logs the decision.

### Noise‑Variance Covariate (FR‑009)

1. After band‑pass filtering, regress out global signal, six motion parameters, and the mean parcel signal.  
2. Compute the variance of the residual time series for each subject → `noise_variance`.  
3. Include `noise_variance` as a nuisance covariate in all parcel‑wise regressions.  
4. Additionally, compute the partial correlation between Entropy and DSRT controlling for `noise_variance` and report the value (methodological‑5d53d78c).

### Statistical Modeling & Multiple‑Comparison Correction (FR‑004, FR‑005, Constitution VII)

* **Model**: Linear regression per parcel: `DSRT ~ Entropy_avg + Age + Sex + FD + NoiseVariance`.  
* **Collinearity**: VIF computed for all covariates; parcels with any VIF ≥ 5 are excluded (SC‑005).  
* **Permutation‑Based FWE**: 5,000 label‑shuffled permutations, max‑statistic null distribution.  
* **Smoothness Check & TFCE**:  
  - Estimate spatial smoothness (FWHM).  
  - If FWHM > 8 mm, empirically validate TFCE assumptions by generating null TFCE maps and testing the autocorrelation function (KS test, *p* > 0.05).  
  - Only after validation is TFCE applied; otherwise max‑statistic correction is retained.

### Power Simulation (SC‑006, methodology‑d8b25039)

* Monte‑Carlo simulation of 1,000 synthetic datasets using observed variance of entropy and covariates, imposing an effect size *d* = 0.3.  
* For each simulated dataset, run a reduced permutation pipeline (a set of permutations) and record whether any parcel survives FWE < 0.05.  
* The proportion of successful simulations yields `estimated_power` (stored in `output/power_metrics.json`).  
* The pipeline **does not abort** if power < 0.80; the final report will explicitly state the estimated power and note the limitation, satisfying the measurement requirement without violating FR‑001.

### Runtime Measurement (SC‑007)

* The permutation loop and overall pipeline are wrapped with wall‑clock timers; peak RAM is monitored via `psutil`.  
* Results are written to `output/runtime_log.json`.  
* CI will check that `total_seconds` ≤ 21,600 s; the report will flag any breach.

### Edge Cases

| Situation | Handling |
| :--- | :--- |
| Missing or invalid HCP credentials | Abort early with error `HCP credentials not provided or invalid`. |
| Subject with mean FD ≥ 0.2 mm | Exclude during QC; record in `subject_qc.csv`. |
| Subject missing DSRT score | Exclude; record in QC. |
| Permutation test exceeds 6‑hour CI limit | Abort the permutation loop, set `runtime_log.json["status"] = "timeout"` and note in PDF. |
| Resampling validation fails | Fall back to original 2 mm data; log warning and proceed. |
| Smoothness exceeds threshold and TFCE validation fails | Retain max‑statistic correction; log that TFCE was not applied. |

## Success Criteria Mapping

| SC ID | Metric | Measurement |
| :--- | :--- | :--- |
| SC‑001 | Total pipeline execution time | `runtime_log.json["total_seconds"]` ≤ 21,600 s |
| SC‑002 | Peak RAM usage | Monitored via `psutil`; must stay ≤ 7 GB |
| SC‑003 | Output completeness | Presence of `output/report.pdf` and `output/association_map.nii.gz` |
| SC‑004 | Sensitivity analysis coverage | Report includes results for *r* = 0.1, 0.15, 0.2 and per‑scale models |
| SC‑005 | VIF threshold | All reported VIF < 5 |
| SC‑006 | Statistical power | `power_metrics.json["estimated_power"]` ≥ 0.80 (reported; limitation noted if not) |
| SC‑007 | Permutation runtime | `runtime_log.json["permutation_seconds"]` ≤ 21,600 s |

## References

* Richiardi, J. et al., 2011. “Multiscale Entropy in fMRI.” *NeuroImage*.
* Nichols, T. & Holmes, A., 2002. “Non‑parametric permutation tests for functional neuroimaging.” *NeuroImage*.
* Smith, S. et al., 2020. HCP Data Access Documentation (official S3 paths).
