# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

**Feature Branch**: `[359-investigating-relationship]`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description:  
> How do individual differences in resting‑state functional connectivity patterns within frontoparietal and default mode networks relate to baseline working memory performance? (Reframed to cross-sectional baseline analysis using ds000277 HCP data, as the original 'training response' idea was not supported by the available dataset).

## User Scenarios & Testing *(mandatory)*

### User Story 0 – Data Validation & Preprocessing Integrity (Priority: P0)

A researcher needs to ensure that the input data is valid, complete, and meets quality standards (motion, ID matching) before any analysis begins, to prevent silent failures in downstream steps.

**Why this priority**: Without valid data and correct ID matching, all subsequent metrics and regression results are meaningless. This is the gatekeeper for the entire pipeline.

**Independent Test**: Run the validation script on a small sample with intentional mismatches (missing IDs, high motion). Verify that the system aborts with exit code 1 and logs the specific error message, or skips high-motion subjects as defined.

**Acceptance Scenarios**:

1. **Given** a dataset where one participant ID exists in rs-fMRI but not in behavioral data, **when** the validation script runs, **then** the system exits with code 1 and logs `ID_VALIDATION: FAIL` with the missing ID list.
2. **Given** a participant with mean framewise displacement (FD) > 3.0 mm, **when** the preprocessing step runs, **then** that participant is excluded from the metric extraction and the exclusion count is logged in the JSON log.
3. **Given** a valid dataset with N ≥ 30, **when** the power analysis script runs, **then** a file `data/results/power_analysis.txt` is generated containing the calculated power for the actual N.

---

### User Story 1 – Compute Baseline Network Metrics (Priority: P1)

A researcher wants to obtain reproducible resting‑state network metrics for each participant so that they can later test predictive relationships.

**Why this priority**: Without reliable baseline metrics the core hypothesis cannot be evaluated; this is the foundational step of the project.

**Independent Test**: Run the preprocessing and metric‑extraction pipeline on a small publicly available rs‑fMRI sample (e.g., N=20). Verify that for every participant a connectivity matrix, global efficiency, modularity, and frontoparietal network strength are produced and saved in the prescribed CSV format.

**Acceptance Scenarios**:

1. **Given** a raw rs‑fMRI NIfTI file and the Schaefer‑400 parcellation, **when** the pipeline is executed, **then** a 400 × 400 Pearson correlation matrix is saved for that participant in `data/preprocessed/`.
2. **Given** the correlation matrix, **when** the network‑metric module runs, **then** numeric values for global efficiency, modularity (Q), and frontoparietal strength are written to `baseline_metrics.csv` with one row per participant.
3. **Given** a JSON log file, **when** the pipeline completes, **then** the log contains keys `exclusion_motion`, `exclusion_missing_wm`, `exclusion_missing_id`, `total_runtime_seconds`, and `pipeline_status` with valid values.

---

### User Story 2 – Associate Baseline Metrics with Baseline Cognition (Priority: P2)

A researcher wants to fit a linear regression model that predicts each participant’s baseline working‑memory score from their baseline network metrics, controlling for age and sex.

**Why this priority**: This story directly tests the scientific hypothesis (cross-sectional association) and yields the primary quantitative result.

**Independent Test**: Using the OpenNeuro dataset ds000277, run the regression script on the valid subset (N ≥ 30) and check that the output file contains coefficient estimates, standard errors, and permutation‑test p‑values for each predictor.

**Acceptance Scenarios**:

1. **Given** `baseline_metrics.csv` and `baseline_wm_scores.csv` (derived from the same participant IDs in ds000277), **when** the regression script is executed, **then** a `model_summary.csv` is produced containing the estimated β for frontoparietal strength, its 95% CI, and a permutation‑derived p‑value.
2. **Given** a valid model run, **when** the system applies Holm‑Bonferroni correction, **then** the corrected p-values are written to the output file.

---

### User Story 3 – Visualize and Report Effect Sizes (Priority: P3)

A researcher wants automatically generated figures that display effect sizes and confidence intervals for each network metric, enabling rapid assessment of results. The figures must be deterministically reproducible.

**Why this priority**: Clear visualization is essential for interpretation, manuscript preparation, and replication. Deterministic reproducibility ensures that results can be independently verified.

**Independent Test**: After a successful regression run, execute the plotting utility twice with the same random seed and verify that the output PDF files have identical hashes.

**Acceptance Scenarios**:

1. **Given** `model_summary.csv`, **when** the visualization script runs, **then** `effect_sizes.pdf` is created and each bar label matches the corresponding predictor name in the summary file.
2. **Given** two consecutive runs with the same seed, **when** the visualization script runs, **then** the resulting PDF files have identical SHA-256 hashes.

---

### Edge Cases

- **Missing rs‑fMRI data**: If a participant lacks a usable rs‑fMRI scan, the pipeline must skip that participant and log a warning without aborting the whole run.  
- **Excessive head motion**: Participants with mean framewise displacement > 3.0 mm are excluded; the exclusion count is reported in the final log under the field `exclusion_motion`.  
- **Absent baseline scores**: If a participant’s baseline working‑memory score is missing, the regression dataset drops that case and records the reason in `exclusion_missing_wm`.
- **Missing IDs**: If a participant ID is present in one source but missing in the other, the system MUST abort with exit code 1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the OpenNeuro dataset `ds000277` (HCP-1200, cross-sectional release) using only HTTP/HTTPS protocols and verify file integrity via checksums.
- **FR-002**: System MUST preprocess all rs‑fMRI scans with fMRIPrep 23.1.3 applying motion correction, spatial normalization, and nuisance regression, and MUST fail gracefully if fMRIPrep exits with a non‑zero status. Participants with mean framewise displacement > 3.0 mm MUST be excluded from further analysis. Intermediate preprocessed artifacts (cleaned NIfTI, confounds TSV) MUST be stored in `data/preprocessed/`.
- **FR-003**: System MUST extract ROI time series using the Schaefer 400‑region parcellation and compute a symmetric Pearson correlation matrix for each participant.
- **FR-004**: System MUST calculate the following network metrics for every participant: (a) global efficiency, (b) modularity (Q), (c) frontoparietal network strength (average edge weight among frontoparietal ROIs), and (d) default‑mode network strength, using only CPU‑compatible libraries (e.g., NetworkX, bctpy).
- **FR-005**: System MUST fit a multiple linear regression model predicting baseline working‑memory performance from the four baseline metrics while controlling for age and sex; it MUST evaluate statistical significance with permutation testing and apply Holm‑Bonferroni family‑wise error correction across the four predictors. The system MUST verify the existence of the `baseline_wm_score` column in the behavioral data before attempting the regression. (See US-2)
- **FR-006**: System MUST generate a PDF report containing (i) a table of regression coefficients with 95% confidence intervals, (ii) permutation‑test p‑values, and (iii) effect‑size bar plots with error bars. (See US-3)
- **FR-007**: System MUST log summary statistics for data exclusion (motion, missing scans, missing behavioral scores) and total runtime; logs MUST be parsable as JSON and MUST contain the keys `exclusion_motion` (int), `exclusion_missing_wm` (int), `exclusion_missing_id` (int), `total_runtime_seconds` (float), and `pipeline_status` (string: 'SUCCESS' or 'FAIL').
- **FR-008**: System MUST run entirely on a CPU‑only environment limited to ≤2 cores, ≤7 GB RAM, and ≤14 GB disk. The system MUST process a subset of participants (N ≥ 30) from ds000277 who possess BOTH valid rs‑fMRI scans and complete baseline behavioral scores. If the valid subset size is <30, the system MUST abort with a warning that statistical power is insufficient and log `pipeline_status: FAIL`. The full pipeline on the valid subset (N ≥ 30) MUST complete within 24 hours. (See US-1, US-2)
- **FR-009**: System MUST parse the participant metadata from dataset `ds000277` to ensure that each participant ID in the rs‑fMRI data has a corresponding entry in the behavioral data, and MUST raise a fatal error (exit code 1) if any participant ID is missing from either source. Upon successful validation, the system MUST log "ID_VALIDATION: PASS" to the JSON log. (See US-0)
- **FR-010**: System MUST execute a power analysis script (using `pwr` or `statsmodels`) with a two‑tailed test, α = 0.05, desired power = 0.80, and the actual sample size N, and MUST write the output to `data/results/power_analysis.txt` before running the regression. (See US-0)
- **FR-011**: System MUST seed all random number generators (regression permutation, plotting) with a fixed integer (default 42) configurable via the `RANDOM_SEED` environment variable to ensure deterministic reproducibility. (See US-3)
- **FR-012**: System MUST verify the presence of the required behavioral column (e.g., `nback_dprime` or `wm_accuracy`) in the dataset's phenotypic TSV before analysis and MUST raise a fatal error if the column is missing. (See US-0)

### Key Entities

- **Participant**: Unique identifier linking rs‑fMRI data, demographic covariates, and baseline cognitive scores.  
- **PreprocessedData**: Intermediate output of fMRIPrep (cleaned NIfTI, confounds TSV) stored in `data/preprocessed/`.
- **ConnectivityMatrix**: 400 × 400 symmetric matrix of Pearson correlation coefficients.  
- **NetworkMetrics**: Record containing global efficiency, modularity, frontoparietal strength, default‑mode strength.  
- **BaselineWM**: Numeric score on a validated working‑memory task (baseline only, derived from N-back performance).  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system MUST correctly calculate p-values and apply Holm‑Bonferroni correction across the four predictors in the regression model. (See US-2)
- **SC-002**: The permutation test MUST produce a null distribution based on ≥1,000 random label shuffles, and the system MUST correctly determine if the observed coefficient lies outside the 2.5th and 97.5th percentiles of the null distribution. (See US-2)
- **SC-003**: The system MUST generate a power analysis file `data/results/power_analysis.txt` using the actual sample size N and the specified parameters (α=0.05, power=0.80), documenting the achieved power. (See US-0)
- **SC-004**: All generated figures MUST be reproducible (identical SHA-256 hashes) when the pipeline is re‑run on the same input data and the same random seed. (See US-3)
- **SC-005**: The entire pipeline MUST complete on a GitHub Actions free‑tier runner (2 CPU, 7 GB RAM) within 24 hours for the valid subset of ds000277 participants (N ≥ 30); runtime is recorded in `runtime.log`. (See US-1, US-2)

## Assumptions

- The OpenNeuro dataset provides resting‑state fMRI scans and baseline behavioral task scores (specifically the N-back task performance, e.g., `nback_dprime` or `wm_accuracy`) for a subset of participants (approximately 85 subjects). It does NOT contain a longitudinal cognitive training intervention or pre/post scores.
- All required software (fMRIPrep, Python 3.11, NetworkX, bctpy, scikit‑learn, matplotlib) are available as CPU‑only wheels and can be installed in the CI environment.  
- No GPU‑accelerated libraries (e.g., CUDA, bitsandbytes) will be used; all computations rely on CPU‑compatible implementations.  
- Participants’ demographic covariates (age, sex) and baseline cognitive scores are present and complete for every subject included in the regression analysis. If the specific behavioral column is missing, the system will abort (FR-012).
- The Schaefer 400‑region parcellation adequately captures frontoparietal and default‑mode network boundaries for the purpose of computing network strength.  
- Motion exclusion threshold (mean FD > 3.0 mm) is sufficient to mitigate motion artefacts while retaining a viable sample size (N ≥ 30) for the regression analysis, in compliance with Constitution Principle VII.