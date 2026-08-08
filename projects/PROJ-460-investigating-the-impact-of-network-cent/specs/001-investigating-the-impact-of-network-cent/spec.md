# Feature Specification: Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder

**Feature Branch**: `001-investigate-asd-centrality`  
**Created**: 2025-01-10  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (US-1)

The system MUST download resting-state fMRI and diffusion MRI (dMRI) data from the ABIDE dataset, preprocess fMRI data using fMRIPrep, and output cleaned time-series data and structural adjacency matrices for each participant.

**Why this priority**: Without reliable, real-world data preprocessing, all downstream analyses (centrality metrics, mediation testing) are invalid. This is the foundational data pipeline that all other functionality depends on.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a sample of participants and verifying output files exist with expected dimensions (timepoints × ROIs for fMRI; streamline counts for dMRI) and that the pipeline completes without timeout on the GitHub Actions runner.

**Acceptance Scenarios**:

1. **Given** valid ABIDE download credentials and participant IDs, **When** the preprocessing pipeline executes on a 2‑core runner, **Then** cleaned fMRI time‑series files and structural adjacency matrices are produced for the maximum number of participants successfully retrieved, and the job completes within the allotted time limit.
2. **Given** corrupted or missing fMRI/dMRI data for a participant, **When** the preprocessing pipeline encounters it, **Then** the system logs an error, skips that participant, and continues processing remaining participants without crashing.

### User Story 2 - Multimodal Mediation Analysis (US-2) *(core hypothesis)*

The system MUST compute structural network centrality from diffusion‑weighted MRI (dMRI) data and test whether it mediates the relationship between functional connectivity strength and ASD social‑communication severity (e.g., ADOS‑2 CSS). The mediation analysis is a required component of the primary scientific question; if fewer than 30 participants have paired fMRI/dMRI data, the pipeline MUST abort with an explicit error indicating that the primary hypothesis cannot be evaluated.

**Why this priority**: This directly addresses the original scientific hypothesis that structural centrality of DMN hubs mediates the link between functional connectivity and behavioral severity.

**Independent Test**: Can be fully tested on the subset of participants with both fMRI and dMRI by verifying that (a) structural centrality metrics are computed, (b) a mediation model is fitted, (c) indirect effects are reported with bootstrapped 95 % confidence intervals and a bootstrap‑derived p‑value, and (d) all metrics are derived exclusively from the loaded dataset without any simulated or placeholder values.

**Acceptance Scenarios**:

1. **Given** participants with both functional and structural data (≥30), **When** the mediation pipeline runs, **Then** the system reports the indirect effect size, 95 % confidence interval, and a bootstrap‑derived p‑value (≤ 0.05 or > 0.05), and the output file contains the raw coefficient values calculated from the participant data.
2. **Given** insufficient structural data (<30 participants), **When** the mediation step is reached, **Then** the system logs “Insufficient structural data for mediation; analysis aborted” and terminates with a non‑zero exit status.
3. **Given** the analysis execution, **When** the results are generated, **Then** the output log explicitly confirms that all reported statistics (p‑values, effect sizes) were computed from the loaded ABIDE dataset and no simulated, hardcoded, or placeholder metrics were inserted.

### User Story 3 - Sensitivity and Confounder Control (US-3)

The system MUST perform a sensitivity analysis sweeping the functional connectivity correlation threshold over a specific set of values and control for demographic confounders (age, sex) and motion artifacts to ensure the mediation effect is robust.

**Why this priority**: To satisfy methodological soundness requirements regarding threshold justification and multiplicity, ensuring the findings are not artifacts of arbitrary parameter choices or confounding variables.

**Independent Test**: Can be fully tested by running the analysis with multiple threshold settings and verifying that the system outputs a sensitivity report showing how the indirect effect size and significance vary across the swept thresholds.

**Acceptance Scenarios**:

1. **Given** the primary mediation model is fitted, **When** the sensitivity analysis is triggered, **Then** the system re‑runs the mediation model with correlation thresholds of 0.5, 0.6, and 0.7, and outputs a table comparing the indirect effect sizes and p‑values for each threshold.
2. **Given** the full dataset, **When** the confounder control step executes, **Then** the system reports the mediation effect size and p‑value after regressing out age, sex, and mean framewise displacement, and compares these to the unadjusted model.

### Edge Cases

- What happens when ABIDE data contains participants with missing diagnosis labels? → System excludes these participants and logs the count.
- How does system handle participants with excessive motion (>3 mm translation)? → System excludes these participants from analysis (see FR-014).
- What happens when participants with age/sex covariate missing values? → System excludes these participants and reports exclusion count.
- What happens if the ABIDE dataset lacks sufficient participants for the planned power? → The system aborts the mediation analysis when fewer than 30 paired participants are available, logs the limitation, and proceeds only with functional‑only analyses where applicable.
- What happens if the dMRI data is present but the tractography fails to reconstruct valid streamlines for a subject? → The system excludes that subject from the structural centrality calculation and logs the specific failure reason.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST target downloading resting‑state fMRI data from ABIDE for ≥100 ASD participants; control participants are optional and not required for the primary hypothesis (See US‑1).
- **FR-002**: System MUST download diffusion‑weighted MRI (dMRI) data from ABIDE for participants where both modalities are present; at least 30 participants with paired data are required for mediation analysis (See US‑2).
- **FR-003**: System MUST preprocess fMRI data using fMRIPrep Docker container with motion correction, normalization, and nuisance regression (See US‑1).
- **FR-004**: System MUST parcellate brain into a set of regions using the Schaefer atlas (Schaefer et al.) (See US‑2).
- **FR-014**: System MUST exclude participants with motion >3 mm translation or rotation from all analyses and log the exclusion count (See US‑1).
- **FR-015**: System MUST use a functional‑connectivity correlation threshold of **0.6** (pre‑registered) for constructing adjacency graphs. If the resulting graph is disconnected, the system MUST apply a minimum spanning tree to ensure full connectivity without altering the threshold (See US‑2).
- **FR-017**: When structural dMRI data are available, System MUST compute structural centrality (eigenvector or degree) and include it in the mediation analysis (See US‑2).
- **FR-019**: System MUST check for the presence of dMRI data in the ABIDE dataset. If absent, the system MUST log a specific “dMRI_MISSING” flag and abort mediation analysis, while allowing functional‑only analyses to continue as appropriate (See US‑2).
- **FR-020**: System MUST output a `mediation_analysis_skipped.log` file containing a detailed rationale for skipping mediation analysis due to data absence (See US‑2).
- **FR-021**: System MUST perform mediation analysis testing whether structural centrality mediates the relationship between functional connectivity strength and ASD social‑communication severity, using a bootstrapped indirect‑effect with **5,000 resamples** to ensure stable estimation, and reporting effect size, 95 % CI, and a bootstrap‑derived p‑value (See US‑2).
- **FR-022**: System MUST verify that at least 30 participants have both fMRI and dMRI data; if fewer are available, the pipeline MUST abort with a clear error message indicating that the primary mediation hypothesis cannot be evaluated (See US‑2).
- **FR-023**: System MUST ensure that all statistical metrics (p‑values, effect sizes) are derived **exclusively** from the processed dataset during execution; the system MUST NOT use simulated, hardcoded, or placeholder values for any research results (See US‑2).
- **FR-024**: System MUST frame all findings regarding the relationship between structural centrality, functional connectivity, and behavioral severity as **ASSOCIATIONAL**, explicitly avoiding causal language unless randomization is present in the study design (See US‑2).
- **FR-025**: System MUST perform a power analysis or explicitly report the observed sample size and its implication for statistical power when the number of participants is below a sufficient threshold for adequate statistical power. (See US‑2).
- **FR-026**: System MUST perform a sensitivity analysis sweeping the functional connectivity correlation threshold over the set **{0.5, 0.6, 0.7}** and report the variation in the indirect effect size and significance (See US‑3).
- **FR-027**: System MUST control for age, sex, and mean framewise displacement as covariates in the mediation model to isolate the specific effect of structural centrality (See US‑3).
- **FR-028**: System MUST verify that the ABIDE dataset contains the necessary variables (fMRI time-series, dMRI streamlines, ADOS-2 scores, age, sex) and record a `[NEEDS CLARIFICATION]` flag if any required variable is missing for the majority of the cohort (See US‑2).

### Key Entities *(include if feature involves data)*

- **Participant**: Individual with fMRI scan and diagnosis label (ASD or control), key attributes: age, sex, diagnosis, motion parameters, ADOS-2 score.
- **TimeSeries**: Preprocessed fMRI signal for each ROI, attributes: timepoints × parcels (e.g., 400 parcels × 300 timepoints).
- **ConnectivityMatrix**: Pearson correlation matrix between all ROIs, attributes: symmetric matrix with values ∈ [-1, 1].
- **StructuralCentralityMetrics**: Network topology measures derived from dMRI tractography (when available).
- **MediationResult**: Statistical output containing direct effect, indirect effect, total effect, confidence intervals, and p-values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data‑preprocessing success rate is measured against the requirement that ≥90 % of successfully retrieved participants produce valid output (See US‑1). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-002**: Structural‑centrality‑completeness is measured against the requirement that structural centrality values are computed for ≥95 % of participants with paired data (See US‑2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-003**: Mediation‑analysis significance is measured against the requirement that the bootstrapped indirect effect yields a 95 % confidence interval and a bootstrap‑derived p‑value (≤ 0.05 or > 0.05) (See US‑2). All metrics are derived from real ABIDE data; values are computed from the actual dataset during execution.
- **SC-004**: Sensitivity‑analysis coverage is measured against the requirement that the indirect effect size is reported for all thresholds in the set {0.5, 0.6, 0.7} (See US‑3).
- **SC-005**: Confounder‑control validity is measured against the requirement that the mediation model explicitly includes age, sex, and motion as covariates and reports the adjusted effect size (See US‑3).
- **SC-006**: Data‑feasibility is measured against the requirement that the system explicitly logs the availability status of dMRI data (See FR‑019).  
- **SC-007**: Mediation‑analysis reporting is measured against the requirement that effect size, confidence interval, and p‑value are output for the primary model and the sensitivity sweep (See FR‑021, FR‑026).

## Assumptions

- ABIDE dataset contains the required variables: fMRI time‑series data, diagnosis labels (ASD/control), age, sex, motion parameters, and clinical severity scores (e.g., ADOS) for a variable subset of participants.
- ABIDE provides diffusion‑weighted MRI (dMRI) data for a subset of participants; at least 30 participants with paired fMRI/dMRI are expected, enabling mediation analysis. **If fewer than 30 paired participants are available, the study cannot address the core hypothesis and will abort (see FR‑022).**
- fMRIPrep Docker container is accessible within GitHub Actions free‑tier environment (CPU‑only, no GPU).
- Schaefer high‑resolution atlas is publicly available and compatible with ABIDE preprocessing pipeline.
- The analysis is observational (no random assignment); therefore all findings are framed as **ASSOCIATIONAL**, not causal.
- Multiple‑comparison correction is required because structural centrality is evaluated across ≥400 ROIs (total tests > 400); the system will apply False Discovery Rate (FDR) correction where appropriate.
- Sample size/power is determined by available data; the analysis will proceed with available ABIDE participants and report power limitations if sample is <50 per group.
- All methods are CPU‑tractable: NetworkX centrality computation, statsmodels mediation analysis with 5,000 bootstraps, and Nilearn visualization run within 6 hours on 2 CPU cores, 7 GB RAM.
- ABIDE data download is permitted under the project's research use license; no commercial use is required.
- Clinical severity scores (e.g., ADOS‑2) are available for a variable subset of participants; if fewer than 30 participants have scores, the correlation analysis will be reported as exploratory with appropriate caveats.
- All statistical results (p‑values, effect sizes) are computed directly from the processed dataset during execution; no hardcoded, simulated, or placeholder values are inserted into the final results.

