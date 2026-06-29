# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Response to Cognitive Training

**Feature Branch**: `[feature-branch]`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description:  
> How do individual differences in resting‑state functional connectivity patterns within frontoparietal and default mode networks relate to improvements in working memory performance following standardized cognitive training?  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Baseline Network Metrics (Priority: P1)

A researcher wants to obtain reproducible resting‑state network metrics for each participant so that they can later test predictive relationships.

**Why this priority**: Without reliable baseline metrics the core hypothesis cannot be evaluated; this is the foundational step of the project.

**Independent Test**: Run the preprocessing and metric‑extraction pipeline on a small publicly available rs‑fMRI sample (e.g., a modest number of participants). Verify that for every participant a connectivity matrix, global efficiency, modularity, and frontoparietal network strength are produced and saved in the prescribed CSV format.

**Acceptance Scenarios**:

1. **Given** a raw rs‑fMRI NIfTI file and the Schaefer‑400 parcellation, **when** the pipeline is executed, **then** a 400 × 400 Pearson correlation matrix is saved for that participant.  
2. **Given** the correlation matrix, **when** the network‑metric module runs, **then** numeric values for global efficiency, modularity (Q), and frontoparietal strength are written to `baseline_metrics.csv` with one row per participant.

---

### User Story 2 – Predict Training Response from Baseline Metrics (Priority: P2)

A researcher wants to fit a linear regression model that predicts each participant’s working‑memory gain from their baseline network metrics, controlling for age, sex, and baseline cognition.

**Why this priority**: This story directly tests the scientific hypothesis and yields the primary quantitative result.

**Independent Test**: Using the OpenNeuro dataset ds000277, run the regression script and check that the output file contains coefficient estimates, standard errors, and permutation‑test p‑values for each predictor.

**Acceptance Scenarios**:

1. **Given** `baseline_metrics.csv` and `training_response.csv` (derived from the same participant IDs in ds000277), **when** the regression script is executed, **then** a `model_summary.csv` is produced containing the estimated β for frontoparietal strength, its 95% CI, and a permutation‑derived p‑value.

---

### User Story 3 – Visualize and Report Effect Sizes (Priority: P3)

A researcher wants automatically generated figures that display effect sizes and confidence intervals for each network metric, enabling rapid assessment of results.

**Why this priority**: Clear visualization is essential for interpretation, manuscript preparation, and replication.

**Independent Test**: After a successful regression run, execute the plotting utility and verify that a PDF file `effect_sizes.pdf` contains a bar plot with error bars for frontoparietal strength, default‑mode strength, global efficiency, and modularity.

**Acceptance Scenarios**:

1. **Given** `model_summary.csv`, **when** the visualization script runs, **then** `effect_sizes.pdf` is created and each bar label matches the corresponding predictor name in the summary file.

---

### Edge Cases

- **Missing rs‑fMRI data**: If a participant lacks a usable rs‑fMRI scan, the pipeline must skip that participant and log a warning without aborting the whole run.  
- **Excessive head motion**: Participants with mean framewise displacement > 3 mm are excluded; the exclusion count is reported in the final log.  
- **Absent training scores**: If a participant’s post‑training working‑memory score is missing, the regression dataset drops that case and records the reason.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the OpenNeuro dataset `ds000277` (HCP-1200 with cognitive training subset) using only HTTP/HTTPS protocols and verify file integrity via checksums.  
- **FR-002**: System MUST preprocess all rs‑fMRI scans with fMRIPrep 23.1.3 applying motion correction, spatial normalization, and nuisance regression, and MUST fail gracefully if fMRIPrep exits with a non‑zero status.  
- **FR-003**: System MUST extract ROI time series using the Schaefer 400‑region parcellation and compute a symmetric Pearson correlation matrix for each participant.  
- **FR-004**: System MUST calculate the following network metrics for every participant: (a) global efficiency, (b) modularity (Q), (c) frontoparietal network strength (average edge weight among frontoparietal ROIs), and (d) default‑mode network strength, using only CPU‑compatible libraries (e.g., NetworkX, bctpy).  
- **FR-005**: System MUST fit a multiple linear regression model predicting working‑memory gain from the four baseline metrics while controlling for age, sex, and baseline cognitive score; it MUST evaluate statistical significance with permutation testing and apply Holm‑Bonferroni family‑wise error correction across the four predictors.
- **FR-006**: System MUST generate a PDF report containing (i) a table of regression coefficients with 95% confidence intervals, (ii) permutation‑test p‑values, and (iii) effect‑size bar plots with error bars.
- **FR-007**: System MUST log summary statistics for data exclusion (motion, missing scans, missing behavioral scores) and total runtime; logs MUST be parsable as JSON.  
- **FR-008**: System MUST run entirely on a CPU‑only environment limited to ≤2 cores, ≤7 GB RAM, and ≤14 GB disk, completing the full pipeline on the subset of participants in ds000277 who possess BOTH valid rs‑fMRI scans and complete training behavioral scores (maximum N=85) within 6 hours. If the valid subset size is <30, the system MUST proceed with the available N and log a warning that statistical power may be insufficient.
- **FR-009**: System MUST parse the participant metadata from dataset `ds000277` to ensure that each participant ID in the rs‑fMRI data has a corresponding entry in the behavioral training data, and MUST raise a fatal error if any participant ID is missing from either source.

### Key Entities

- **Participant**: Unique identifier linking rs‑fMRI data, demographic covariates, and training outcome.  
- **ConnectivityMatrix**: 400 × 400 symmetric matrix of Pearson correlation coefficients.  
- **NetworkMetrics**: Record containing global efficiency, modularity, frontoparietal strength, default‑mode strength.  
- **TrainingResponse**: Numeric difference (post‑test – pre‑test) on a validated working‑memory task.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The regression coefficient for frontoparietal network strength must be statistically significant after Holm‑Bonferroni correction (adjusted *p* < 0.05) in a single dataset with N ≥ 30 (the valid intersection of ds000277 rs-fMRI and behavioral data), or via split‑sample validation (50/50 split) on the same dataset.  
- **SC-002**: The permutation test must produce a null distribution based on ≥1,000 random label shuffles, and the observed coefficient must lie outside the lower and upper percentiles of the distribution of this distribution for the frontoparietal predictor.
- **SC-003**: A priori power analysis (using a two‑tailed test, α = 0.05, desired power = 0.80) must indicate that the planned sample size (N ≥ 85, the maximum valid intersection in ds000277) provides ≥80 % power to detect an effect size of *r* = 0.30; the analysis result must be documented in `power_analysis.txt`. If N < 85, the analysis must report the achieved power for the actual N.
- **SC-004**: All generated figures must be reproducible (identical hashes) when the pipeline is re‑run on the same input data and random seeds.  
- **SC-005**: The entire pipeline must complete on a GitHub Actions free‑tier runner (2 CPU, 7 GB RAM) within 6 hours for the valid subset of ds000277 participants (N ≤ 85); runtime is recorded in `runtime.log`.  

## Assumptions

- The OpenNeuro dataset `ds000277` provides both resting‑state fMRI scans and a validated working‑memory training protocol with pre/post performance scores for a subset of participants (approximately 85 subjects).
- All required software (fMRIPrep, Python 3.11, NetworkX, bctpy, scikit‑learn, matplotlib) are available as CPU‑only wheels and can be installed in the CI environment.  
- No GPU‑accelerated libraries (e.g., CUDA, bitsandbytes) will be used; all computations rely on CPU‑compatible implementations.  
- Participants’ demographic covariates (age, sex) and baseline cognitive scores are present and complete for every subject included in the regression analysis.  
- The Schaefer 400‑region parcellation adequately captures frontoparietal and default‑mode network boundaries for the purpose of computing network strength.  
- Motion exclusion threshold (mean FD > 3 mm) is sufficient to mitigate motion artefacts without excessively reducing sample size below the minimum viable N=30.