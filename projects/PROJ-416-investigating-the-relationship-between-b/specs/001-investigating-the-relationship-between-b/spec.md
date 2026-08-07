# Feature Specification: Investigate Brain Network Dynamics and VR Therapy Response

**Feature Branch**: `[416-brain-network-dynamics]`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Dynamics and Response to Virtual Reality Exposure Therapy"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and preprocess resting-state fMRI data (Priority: P1)

As a researcher, I need to download resting-state fMRI data from public repositories (e.g., OpenNeuro) and preprocess it with motion correction, slice timing correction, and normalization so that I have clean, standardized neuroimaging data ready for network analysis.

**Why this priority**: This is the foundational data pipeline. Without clean, preprocessed fMRI data, no network metrics can be computed and no analysis can proceed. This represents the core data acquisition and preparation workflow.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a single subject's fMRI scan and verifying output files exist with expected dimensions and quality metrics.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID for anxiety disorder patients with pre/post treatment fMRI, **When** the preprocessing pipeline executes, **Then** motion-corrected, slice-timing corrected, and normalized fMRI files are produced for each subject
2. **Given** a subject with excessive motion (>3mm translation or >3° rotation), **When** the quality check runs, **Then** that subject is flagged for exclusion and logged with the specific motion metric that exceeded the threshold
3. **Given** a dataset with clinical instruments, **When** the validation step runs, **Then** the system verifies the instrument is a validated anxiety scale (e.g., GAD-7, HAM-A) with citable documentation, or halts with an error
4. **Given** a target dataset, **When** the pre-extraction check runs, **Then** the system confirms the existence of paired pre/post treatment fMRI and clinical scores; if missing, the system halts with a fatal error and logs "Data Unavailable: Missing [variable_name]"

---

### User Story 2 - Compute resting-state brain network metrics (Priority: P2)

As a researcher, I need to compute functional connectivity matrices and derive network properties (modularity Q, global efficiency, local efficiency) using a standard parcellation atlas (AAL or Schaefer with 100-200 regions) so that I have quantitative biomarkers for the regression analysis.

**Why this priority**: This produces the predictor variables (brain network metrics) that will be tested for association with treatment response. Without these metrics, the core research question cannot be addressed.

**Independent Test**: Can be fully tested by computing network metrics on a single preprocessed subject and verifying that all three metrics (modularity, global efficiency, local efficiency) are produced with values in expected ranges.

**Acceptance Scenarios**:

1. **Given** preprocessed fMRI data and a chosen parcellation atlas (AAL or Schaefer, 100-200 regions), **When** the network computation pipeline executes, **Then** functional connectivity matrices and network metrics (modularity Q, global efficiency, local efficiency) are produced for each subject
2. **Given** two subjects with different parcellation atlases (AAL vs. Schaefer), **When** network metrics are computed, **Then** both sets of metrics are stored separately and can be compared for consistency

---

### User Story 3 - Perform statistical analysis and generate reports (Priority: P3)

As a researcher, I need to perform exploratory statistical analysis modeling Post-treatment score as the outcome with Pre-treatment score and baseline network metrics (or their principal components) as predictors, apply multiple comparison correction, and generate diagnostic plots so that I can evaluate whether brain network dynamics are associated with VR therapy responsiveness in an exploratory pilot study.

**Why this priority**: This addresses the core research question directly. While dependent on P1 and P2 outputs, this story produces the final scientific results and can be tested independently once data is available. The study is explicitly framed as exploratory due to sample size constraints.

**Independent Test**: Can be fully tested by running the ANCOVA/PCA pipeline on sample data and verifying that regression coefficients, confidence intervals, and diagnostic plots are produced.

**Acceptance Scenarios**:

1. **Given** baseline network metrics and corresponding Pre/Post treatment scores, **When** the ANCOVA analysis executes, **Then** regression coefficients, p-values (with multiple comparison correction), and effect sizes (Cohen's d) with 95% confidence intervals are produced for each network metric tested, controlling for baseline severity
2. **Given** multiple hypothesis tests (e.g., modularity + global efficiency + local efficiency), **When** correction is applied, **Then** Bonferroni or FDR-corrected p-values are reported alongside uncorrected values
3. **Given** significant associations (p<0.05), **When** diagnostic plots are generated, **Then** scatter plots with regression lines and residual diagnostics are produced and saved
4. **Given** decision cutoffs (motion threshold, p-value), **When** the sensitivity analysis executes, **Then** the system sweeps cutoffs over a concrete set (motion: {2.0, 3.0} mm; p-value: {0.01, 0.05, 0.1}) and reports variation in effect size estimates and confidence intervals

---

### Edge Cases

- **Missing Variables**: If the public dataset lacks required clinical outcome variables (anxiety scale scores) or pre/post scans, the system MUST halt with a fatal error and log "Missing required variable: [variable_name]".
- **Incomplete Scans**: If a subject has incomplete pre/post treatment scans, the system MUST exclude that subject from the analysis and log the exclusion reason.
- **NaN Metrics**: If network metrics are undefined (e.g., connectivity matrix has NaN values due to preprocessing artifacts), the system MUST exclude that metric for that subject and log the event.
- **Collinearity**: If collinearity between network metrics (e.g., global efficiency and modularity) is detected (Variance Inflation Factor > 5), the system MUST compute principal components (PC1, PC2, etc.) of the metrics and use those as predictors; if the PCA fails or fewer than 2 components explain >90% variance, the system MUST halt with a "Collinearity Unresolvable" error.
- **Insufficient Power**: If the dataset contains fewer subjects than required for adequate statistical power (based on G*Power calculation with α=0.05, power≥0.8, effect size f²=0.15), the system MUST write a warning "WARNING: Underpowered for hypothesis testing (Power < 0.8)" to the report log if 5 ≤ N < 10; if N < 5, the system MUST halt the regression analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data from OpenNeuro or equivalent public repository (defined as containing resting-state fMRI, pre/post clinical scores, and metadata fields `study_design` and `randomized`) and store it locally with metadata preserved (See US-1)
- **FR-002**: System MUST preprocess fMRI data with motion correction, slice timing correction, and spatial normalization; the full preprocessing batch for the selected subset of up to N=20 subjects MUST complete within a 6-hour wall-clock window on the specified hardware (2 cores, 7GB RAM), with a per-subject target of ≤30 minutes; the system MUST use streaming/chunking to ensure memory usage never exceeds 7GB (See US-1)
- **FR-003**: System MUST compute functional connectivity matrices using Pearson correlation between ROI time series from a standard parcellation atlas (AAL or Schaefer, 100-200 regions) (See US-2)
- **FR-004**: System MUST calculate network properties including modularity (Q), global efficiency, and local efficiency using Brain Connectivity Toolbox or equivalent (See US-2)
- **FR-005**: System MUST perform ANCOVA analysis modeling Post-treatment score as the outcome with Pre-treatment score and baseline network metrics as predictors; if collinearity is detected (VIF > 5), the system MUST compute principal components of the network metrics and use those as predictors; if the PCA fails or fewer than 2 components explain >90% variance, the system MUST halt with a "Collinearity Unresolvable" error (See US-3)
- **FR-006**: System MUST apply multiple comparison correction (Bonferroni or FDR) when testing >1 network metric hypothesis (See US-3)
- **FR-007**: System MUST generate diagnostic plots including scatter plots with regression lines and residual diagnostics (See US-3)
- **FR-008**: System MUST frame all findings as ASSOCIATIONAL when dataset is observational (no random assignment); the system MUST check `metadata.study_design` for the string 'randomized' OR `metadata.randomized` for boolean true; if neither exists, findings are framed as ASSOCIATIONAL (See US-3)
- **FR-009**: System MUST require validated anxiety assessment instruments with citable validation documentation (e.g., GAD-7, HAM-A); if the instrument is not validated, the system MUST halt (See US-1)
- **FR-010**: System MUST perform sensitivity analysis sweeping specific decision cutoffs (motion threshold: {2.0, 3.0} mm; p-value: {0.01, 0.05, 0.1}) and report variation in effect size estimates and confidence intervals (See US-3)
- **FR-011**: System MUST verify the existence of paired pre/post treatment fMRI and clinical scores in the target dataset before execution; specifically, the system MUST check for metadata keys `pre_treatment_score`, `post_treatment_score`, and `anxiety_instrument`; if missing, the system MUST halt with a fatal error (See US-1)
- **FR-012**: System MUST include known confounders (medication status, age, comorbidities) as covariates in the ANCOVA model if data is available; if data is missing for a specific confounder, the system MUST exclude that confounder from the model and log the exclusion; if >50% of subjects lack a specific confounder, that confounder is dropped entirely (See US-3)
- **FR-013**: System MUST attempt to aggregate data from multiple public repositories if a single source lacks the required paired data; if no longitudinal dataset with pre/post scores is found after checking at least 3 sources, the system MUST halt with "Data Unavailable: No longitudinal dataset found" (See US-1)

### Key Entities *(include if feature involves data)*

- **Subject**: Represents an individual participant with pre/post treatment fMRI scans and clinical outcome measures
- **Network Metric**: Represents computed brain network properties (modularity, global efficiency, local efficiency) with subject ID, atlas type, and value
- **Treatment Response**: Represents clinical outcome (Post-treatment score) with subject ID, pre-treatment score, post-treatment score, and assessment instrument name

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset-variable fit is measured against a binary check: the pipeline halts if required variables (resting-state fMRI, pre-treatment anxiety score, post-treatment anxiety score) are absent from dataset metadata (See US-1)
- **SC-002**: Preprocessing quality is measured against motion threshold criteria (>3mm translation or >3° rotation triggers exclusion) (See US-1)
- **SC-003**: Network metric computation is measured against mathematical bounds: Modularity Q must be non-negative.; Global/Local Efficiency must be ≥ 0 and finite. Any NaN or out-of-bound value triggers exclusion (See US-2)
- **SC-004**: Statistical power is measured against a G*Power (or equivalent) calculation with α=0.05, effect size f²=0.15, and target power ≥ 0.8; the report MUST include the calculated minimum N required and a warning if the actual N is insufficient for hypothesis testing; the study is explicitly framed as exploratory (See US-3)
- **SC-005**: Association framing is measured against the dataset metadata JSON: the system checks `metadata.study_design` for the string 'randomized' OR `metadata.randomized` for boolean true; if neither exists, findings are framed as ASSOCIATIONAL (See US-3)
- **SC-006**: Threshold sensitivity is measured against variation in effect size estimates and confidence intervals across swept cutoff values (motion: {2.0, 3.0} mm; p-value: {0.01, 0.05, 0.1}) (See US-3)

## Assumptions

- Public dataset (e.g., OpenNeuro) contains both resting-state fMRI data AND accompanying clinical anxiety scale scores for pre/post treatment measurement. **Verification**: FR-011 ensures this is checked before execution; if not found, the pipeline halts.
- **High Risk Acknowledgement**: Longitudinal clinical trial data with paired pre/post VR therapy scores is rare in open repositories. The system implements FR-013 to aggregate across multiple sources; if no such data is found, the project halts with "Data Unavailable".
- Analysis runs on CPU-only hardware (2 cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h per job)
- No GPU/CUDA/accelerators required; no 8-bit or 4-bit quantization, no device_map="cuda", no mixed-precision/GPU training
- Data is sampled/subset to fit within typical RAM and disk constraints.; the 6-hour window applies to the processed subset, not the entire raw dataset. Streaming/chunking is used to stay within 7GB RAM.
- Classical statistics (linear regression, correlation) and scikit-learn on modest data are used; no deep neural network training from scratch
- Any decision cutoffs introduced (e.g., inconsistency tolerance, classification boundary) carry both a one-line justification naming community-standard basis AND a sensitivity analysis requirement
- Predictor collinearity (e.g., if two network metrics are definitionally related) is handled via Principal Component Analysis (PCA) to ensure orthogonality; Ridge regression and univariate fallbacks are NOT used as they do not resolve the fundamental issue of testing independent effects of definitionally linked variables.
- Validated anxiety assessment instruments with citable validation are used (e.g., GAD-7, HAM-A)
- If the design is observational (no random assignment), all findings are framed as ASSOCIATIONAL, not causal
- Multiple comparison correction (Bonferroni or FDR) is applied when >1 hypothesis test is run
- Sample size/power consideration is documented with method stated (G*Power, α=0.05, effect size f²=0.15, power≥0.8) or explicit acknowledgement of power limitation. The study is explicitly framed as exploratory/pilot if N < required for power ≥ 0.8. If N < 5, the analysis halts.