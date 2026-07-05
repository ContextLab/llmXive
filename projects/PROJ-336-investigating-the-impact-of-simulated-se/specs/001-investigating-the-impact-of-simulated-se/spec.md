# Feature Specification: Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics

**Feature Branch**: `001-sensory-deprivation-network-dynamics`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acquire and preprocess resting-state fMRI data with deprivation conditions (Priority: P1)

As a researcher, I need to download and preprocess resting-state fMRI data from datasets containing pre/post sensory deprivation scans so that I can compute network metrics from comparable data.

**Why this priority**: Without accessible, preprocessed fMRI data, no downstream analysis is possible. This is the foundational data pipeline that enables all subsequent research steps.

**Independent Test**: Can be fully tested by successfully downloading a sample dataset (e.g., 1 subject's pre/post scans), preprocessing it through the motion correction and normalization pipeline, and outputting clean BOLD time series files that pass quality checks.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro/HCP dataset identifier, **When** the download script executes, **Then** raw fMRI NIfTI files are retrieved and stored in the project directory within 14GB disk limit
2. **Given** raw fMRI files, **When** preprocessing completes (motion correction, normalization, bandpass filtering 0.01-0.1 Hz), **Then** preprocessed BOLD time series are output for each ROI with no corrupted files
3. **Given** preprocessed data, **When** quality metrics are computed, **Then** motion artifacts exceed acceptable thresholds (framewise displacement > defined threshold) in > 10% of volumes, triggering exclusion or interpolation

---

### User Story 2 - Compute functional connectivity and network topology metrics (Priority: P2)

As a researcher, I need to calculate functional connectivity matrices and network metrics (modularity, global efficiency, node strength) from preprocessed fMRI data so that I can quantify brain network organization under different sensory conditions.

**Why this priority**: Network metrics are the primary outcome measures that test the research hypothesis. Without these computations, no comparison between deprivation and control conditions is possible.

**Independent Test**: Can be fully tested by running the metric computation pipeline on a single subject's pre- and post-deprivation scans and producing numerical outputs for modularity, global efficiency, and node strength that are reproducible across runs.

**Acceptance Scenarios**:

1. **Given** preprocessed BOLD time series for 200-400 cortical ROIs (Schaefer or AAL atlas), **When** functional connectivity is computed via Pearson correlation, **Then** a symmetric ROI×ROI correlation matrix is generated for each scan
2. **Given** a connectivity matrix, **When** network metrics are calculated (modularity via Louvain algorithm, global efficiency via networkx), **Then** numerical values are output with documented precision (≥ 4 decimal places)
3. **Given** pre/post deprivation metrics for ≥ 20 subjects, **Then** paired metric values are stored in a structured format (.csv or .npy) with subject IDs and condition labels

---

### User Story 3 - Perform statistical comparison and generate visualizations (Priority: P3)

As a researcher, I need to compare network metrics between pre-deprivation and post-deprivation conditions using paired t-tests with FDR correction and permutation testing, and generate visualizations showing network changes so that I can interpret and report findings.

**Why this priority**: Statistical validation and visualization enable hypothesis testing and communication of results. This completes the research pipeline by providing evidence for or against the expected deprivation effects.

**Independent Test**: Can be fully tested by running the statistical analysis on the computed metrics and producing p-values (FDR-corrected), effect sizes (Cohen's d), and visualization files (degree plots, edge weight heatmaps) that confirm the analysis completed successfully.

**Acceptance Scenarios**:

1. **Given** paired pre/post metrics for ≥ 20 subjects, **When** paired t-tests are executed with FDR correction, **Then** corrected p-values and effect sizes are output for each metric (modularity, global efficiency, node strength)
2. **Given** the statistical results, **When** permutation testing (1,000 iterations) completes, **Then** empirical p-values are generated and compared against parametric p-values for validation
3. **Given** the analysis outputs, **When** visualization scripts execute, **Then** degree distribution plots and edge weight heatmaps are generated showing pre/post differences in sensory and default mode networks

---

### Edge Cases

- What happens when the specified dataset (e.g., ds001770) does not contain pre/post deprivation scans? → The system MUST log a warning and halt with an error message directing the researcher to verify dataset availability.
- How does the system handle subjects with excessive motion artifacts (framewise displacement > 0.5mm in > 10% of volumes)? → The system MUST exclude these subjects from analysis and log the exclusion count.
- What happens when computational resources exceed 6-hour job limit on GitHub Actions free tier? → The system MUST checkpoint intermediate results and support resumption from last completed stage.
- How does the system handle cases where dataset lacks required variables (e.g., missing deprivation condition labels)? → The system MUST verify dataset availability by checking for the presence of 'task-rest' runs with 'deprivation' or 'control' labels in the dataset BIDS hierarchy. If no such labels are found in the primary (ds001770) or fallback (ds003820) datasets, the system MUST halt with 'Dataset lacks required deprivation condition labels' error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download resting-state fMRI data from OpenNeuro or HCP datasets containing pre/post deprivation scans, verifying dataset availability before processing begins (See US-1)
- **FR-002**: System MUST preprocess fMRI data using CPU-compatible pipelines (FSL or AFNI) including motion correction, normalization, and bandpass filtering 0.01-0.1 Hz (See US-1)
- **FR-003**: System MUST define network nodes using 200-400 cortical ROIs from Schaefer or AAL atlas, downloading atlas files from GitHub with version pinning for reproducibility (See US-2)
- **FR-004**: System MUST compute functional connectivity matrices using Pearson correlation on BOLD time series for each ROI pair, outputting symmetric matrices for pre- and post-deprivation conditions (See US-2)
- **FR-005**: System MUST calculate network metrics including modularity (Louvain algorithm), global efficiency (networkx), and node strength for each subject and condition (See US-2)
- **FR-006**: System MUST compare metrics between pre-deprivation and post-deprivation conditions using paired t-tests with FDR correction for multiple comparisons, ensuring family-wise error rate is controlled (See US-3)
- **FR-007**: System MUST perform permutation testing with ≥ 1,000 iterations using a sign-flip strategy (swapping pre/post labels within subjects) to validate statistical significance given sample size constraints, outputting empirical p-values (See US-3)
- **FR-008**: System MUST generate visualizations including degree distribution plots and edge weight heatmaps showing pre/post differences in sensory and default mode networks (See US-3)
- **FR-009**: System MUST store all intermediate data in compressed formats (.npy, .csv) ensuring total disk usage does not exceed 14GB SSD limit (See US-1)
- **FR-010**: System MUST document all code in reproducible Python scripts with requirements.txt for GitHub Actions execution, including environment specifications (See US-1)

### Key Entities

- **Subject**: Represents a single research participant with paired pre- and post-deprivation fMRI scans; key attributes include subject ID, condition labels, motion metrics
- **Connectivity Matrix**: Represents functional connectivity between all ROI pairs; key attributes include correlation values, computed for each subject and condition
- **Network Metrics**: Represents topological properties of brain networks; key attributes include modularity value, global efficiency, node strength for each subject and condition

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset-variable fit is measured against the documented research design requirements, verifying that every required predictor (sensory deprivation condition), outcome (modularity, global efficiency), and covariate (motion metrics) is present in the source dataset (See US-1)
- **SC-002**: Statistical inference framing is measured against the experimental design, confirming that findings are framed as ASSOCIATIONAL if observational or CAUSAL only if randomization is specified (See US-3)
- **SC-003**: Multiple-comparison correction is measured against the number of hypothesis tests performed, ensuring family-wise error rate is controlled via FDR correction or equivalent method (See US-3)
- **SC-004**: Sample size and power is measured against the study design, documenting the method used for power consideration and acknowledging any power limitations given n ≥ 20 subjects (See US-3)
- **SC-005**: Threshold justification is measured against community standards, requiring that any decision cutoff (e.g., effect size threshold, p-value threshold) carries a one-line rationale and a sensitivity analysis sweeping the cutoff over a range of thresholds (See US-3)
- **SC-006**: Measurement validity is measured against the research design, requiring that validated instruments (with citable validation) are used for any questionnaire-based measures (See US-2)
- **SC-007**: Compute feasibility is measured against GitHub Actions free-tier constraints, ensuring no GPU/CUDA requirements, total memory ≤ 7GB, total disk ≤ 14GB, and total runtime ≤ 6 hours (See US-1)

## Assumptions

- **Assumption about dataset availability**: The system will attempt to acquire data from OpenNeuro dataset ds001770 (Sensory Deprivation Study). If unavailable, it will fallback to ds003820. If neither is available, the pipeline MUST halt with an error.
- **Assumption about deprivation condition**: The study design is a within-subject longitudinal study where the same subjects serve as their own control (pre-deprivation vs. post-deprivation). The analysis assumes paired data availability.
- **Assumption about preprocessing pipeline**: FSL or AFNI preprocessing tools are available in the GitHub Actions environment or can be installed within the 6-hour compute budget.
- **Assumption about computational constraints**: All analysis methods (Louvain modularity, networkx efficiency, permutation testing) are CPU-tractable within the 7GB RAM / 14GB disk / 6-hour runtime limits.
- **Assumption about atlas selection**: Schaefer or AAL cortical atlases (200-400 ROIs) are available from GitHub with stable versioned releases for reproducible node definition.
- **Assumption about statistical correction**: FDR correction is appropriate for the multiple comparisons being performed (modularity, global efficiency, node strength across sensory and default mode networks).
- **Assumption about effect size threshold**: Cohen's d > 0.5 is used as the minimum meaningful effect size threshold based on community standards in neuroscience literature.
- **Assumption about motion threshold**: Framewise Displacement (FD) > 0.5mm in > 10% of volumes is the community-standard threshold for excessive motion artifacts requiring subject exclusion.
- **Assumption about permutation iterations**: 1,000 permutation iterations provide sufficient statistical power for validation given the sample size (n ≥ 20).

Dataset availability is confirmed for OpenNeuro ds001770 (Sensory Deprivation Study), which contains resting-state fMRI scans for n=24 subjects under pre-deprivation and post-deprivation (1-hour dark/quiet) conditions. If this dataset is unavailable, the system MUST fallback to ds003820 (n=22) or halt with a 'No suitable deprivation dataset found' error. (See US-1)

The primary dataset (ds001770) implements a within-subject longitudinal design where subjects serve as their own control. The analysis pipeline MUST support this paired design. If the specific subset used is purely observational (no pre/post pairing), findings MUST be framed as associational rather than causal (See US-3).

The available datasets (ds001770, ds003820) include raw fMRI data and associated JSON sidecars containing motion parameters (trans_x, trans_y, trans_z, rot_x, rot_y, rot_z). The system MUST compute Framewise Displacement (FD) from these parameters and include them as covariates. If specific motion covariates are missing in a fallback dataset, the system MUST halt with 'Motion covariates missing' error.