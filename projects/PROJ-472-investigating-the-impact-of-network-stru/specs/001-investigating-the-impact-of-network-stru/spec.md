# Feature Specification: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Feature Branch**: `001-network-structure-avalanche-dynamics`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "How do anatomical brain network properties (node degree distribution, clustering coefficient from diffusion‑mri structural connectomes) relate to neural avalanche statistics (size, duration) measured from human resting‑state EEG?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline Integration (Priority: P1)

As a researcher, I need to acquire and preprocess diffusion‑MRI structural connectomes and resting‑state EEG recordings from the OpenNeuro HCP-Aging dataset so that I can compute network metrics and avalanche statistics from the same participants.

**Why this priority**: Without successfully integrating both data modalities, no analysis can proceed. This is the foundational data infrastructure that enables all downstream research.

**Independent Test**: Can be fully tested by successfully downloading, preprocessing, and storing a subset of dMRI and EEG data from OpenNeuro ds004230/31 in a unified participant‑indexed format.

**Acceptance Scenarios**:

1. **Given** access to OpenNeuro ds004230/31 (HCP-Aging), **When** the pipeline downloads and processes data for at least 50 participants (or all available if < 50), **Then** both modalities are stored in participant‑indexed format with matching subject identifiers.
2. **Given** raw dMRI and EEG files from OpenNeuro, **When** preprocessing completes, **Then** structural connectivity matrices (multiple parcels) and cleaned EEG time series (1–40 Hz, 250 Hz) are available for each participant.
3. **Given** a participant ID, **When** querying the data store, **Then** both the structural graph and EEG recording for that participant can be retrieved without error.

---

### User Story 2 - Network and Avalanche Metric Computation (Priority: P2)

As a researcher, I need to compute canonical structural network metrics (degree, clustering coefficient, rich‑club coefficient) and neural avalanche statistics (size, duration, power‑law exponents) so that I can test for associations between anatomy and dynamics.

**Why this priority**: This delivers the core analytical output of the project. Even without the full statistical association, having computed metrics enables exploratory analysis and validation of the pipeline.

**Independent Test**: Can be fully tested by computing metrics for a subset of participants and verifying that the output values are within expected ranges for human brain networks and neural avalanches.

**Acceptance Scenarios**:

1. **Given** a preprocessed structural connectivity matrix, **When** computing graph metrics, **Then** mean degree, mean clustering coefficient, and rich‑club coefficient are output for each participant.
2. **Given** a preprocessed EEG time series, **When** detecting avalanches using the 75th percentile threshold, **Then** avalanche size and duration distributions are output with fitted power‑law scaling exponents.
3. **Given** computed metrics for all participants, **When** exporting to CSV, **Then** each row contains one participant's structural metrics and avalanche statistics with no missing values.

---

### User Story 3 - Statistical Association and Robustness Testing (Priority: P3)

As a researcher, I need to test for statistically robust associations between structural metrics and avalanche exponents, with correction for multiple comparisons and threshold sensitivity analysis, so that I can draw defensible conclusions about structure‑function relationships.

**Why this priority**: This delivers the primary scientific finding. Without rigorous statistical validation, the computed metrics alone cannot support scientific claims.

**Independent Test**: Can be fully tested by running the association analysis on a subset of participants and verifying that correlation coefficients, p‑values, and sensitivity sweep results are reproducible.

**Acceptance Scenarios**:

1. **Given** participant‑level structural and avalanche metrics, **When** computing Spearman rank correlations, **Then** correlation coefficients, p‑values, and collinearity diagnostics (VIF) are output for each metric pair.
2. **Given** correlation results, **When** running permutation tests (1000 shuffles), **Then** corrected p‑values accounting for multiple comparisons are output.
3. **Given** the 75th percentile avalanche threshold, **When** running sensitivity analysis across thresholds {0.70, 0.75, 0.80}, **Then** correlation coefficients and p‑values are output for each threshold setting to assess robustness.
4. **Given** structural metrics used as predictors, **When** running collinearity diagnostics, **Then** Variance Inflation Factor (VIF) values are output for degree and clustering coefficient.

---

### Edge Cases

- How does system handle participants with insufficient EEG data quality (e.g., excessive artifact after ICA)?
- How does system handle participants with sparse structural connectivity (e.g., low streamline counts leading to disconnected graphs)?
- What happens when power‑law fitting fails to converge for a participant's avalanche distribution?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess diffusion‑MRI structural connectomes from OpenNeuro ds004230 (HCP-Aging) using MRtrix with HCP multimodal parcellation (360 parcels) (See US-1)
- **FR-002**: System MUST preprocess resting‑state EEG recordings from OpenNeuro ds004231 with band‑pass filter 1–40 Hz, down‑sample to 250 Hz, and remove ocular/muscle artifacts via ICA using MNE‑Python (See US-1)
- **FR-003**: System MUST compute node‑wise degree, mean clustering coefficient, and rich‑club coefficient for each subject's structural graph using NetworkX (See US-2)
- **FR-004**: System MUST detect neural avalanches by first applying z-score normalization (global mean and standard deviation) to the EEG signal, then thresholding at the 75th percentile amplitude (calculated per-participant over the entire resting-state recording) to identify contiguous spatiotemporal events across channels (See US-2)
- **FR-005**: System MUST fit power‑law models to avalanche size and duration distributions using the `powerlaw` Python package and extract scaling exponents (See US-2)
- **FR-006**: System MUST perform Spearman rank correlation between structural metrics and avalanche exponents across subjects, reporting results for each metric pair individually (See US-3)
- **FR-007**: System MUST validate significance with non‑parametric permutation test (shuffle subject labels 1000 times) and apply multiple‑comparison correction for family‑wise error (See US-3)
- **FR-008**: System MUST run sensitivity analysis on avalanche threshold by sweeping thresholds {70%, 75%, 80%} and report how correlation rates vary across thresholds (See US-3)
- **FR-009**: System MUST perform collinearity diagnostics (Variance Inflation Factor) when degree and clustering coefficient are used together as predictors; if VIF ≥ 5, the system MUST flag the result as 'high collinearity' and not claim independent predictive effects (See US-3)
- **FR-010**: System MUST frame all findings as associational (not causal) given the observational design without random assignment (See US-3)
- **FR-011**: System MUST perform model comparison (likelihood ratio test) between power-law, exponential, and log-normal distributions for avalanche size/duration; only extract and report the power-law exponent if the power-law model is statistically preferred (See US-2)

### Key Entities

- **Participant**: Research subject with matched dMRI and EEG data; key attributes: subject_id, structural_metrics, avalanche_metrics
- **StructuralConnectome**: Weighted graph from dMRI tractography; key attributes: adjacency_matrix, node_degree, clustering_coefficient, rich_club_coefficient
- **AvalancheRecord**: Detected neural event; key attributes: size, duration, time_bins, participant_id
- **CorrelationResult**: Statistical association between metrics; key attributes: metric_pair, spearman_rho, p_value, corrected_p_value, vif_score

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Correlation coefficients between structural metrics and avalanche exponents are measured against Spearman rank correlation with permutation‑based significance (See US-3)
- **SC-002**: Threshold sensitivity is measured by comparing correlation stability across the {[deferred], [deferred], [deferred]} sweep (See US-3)
- **SC-003**: Multiple‑comparison correction is measured by family‑wise error rate control via 1000‑shuffle permutation test (See US-3)
- **SC-004**: Data quality is measured by the proportion of participants with complete dMRI and EEG preprocessing pipelines (See US-1)
- **SC-005**: Collinearity is measured by variance inflation factor (VIF) for degree and clustering coefficient when jointly modeled (See US-3)
- **SC-006**: Compute feasibility is measured by total runtime ≤ 6 hours on a pinned ubuntu-latest runner with 2 vCPU and 7 GB RAM (See US-1)

## Assumptions

- **Dataset integration**: The project relies exclusively on matched dMRI and resting-state EEG data from the same participants. Public repositories such as HCP 1200 do not contain matched EEG/dMRI for the same subjects. The project will utilize the HCP-YA (Young Adult) combined dataset or the OpenNeuro 'ds004503' (HCP-MMP) which provides matched dMRI and resting-state fMRI/EEG proxies, or the 'Human Connectome Project - Lifespan' dataset if EEG is available. If no single public repository offers matched dMRI+EEG for ≥50 participants, the study proceeds with the available matched subset, acknowledging the reduced sample size in the final report. Cross-dataset registration is NOT permitted as it invalidates the structure-function coupling research question.
- **Compute constraints**: Assumes all analysis runs on CPU‑only GitHub Actions free‑tier runner (2 cores, ~7 GB RAM, ~14 GB disk, ≤6 h total runtime); no GPU/CUDA required.
- **Threshold justification**: The 75th percentile amplitude threshold for avalanche detection follows community convention for binary activity raster generation; sensitivity analysis will sweep {[deferred], [deferred], [deferred]} to assess robustness.
- **Observational design**: All statistical associations are framed as correlational/associational, not causal, given the lack of random assignment in the naturalistic data.
- **Sample size**: Power analysis for correlation detection is [deferred] to the research phase; the analysis will proceed with available participants and acknowledge power limitations in reporting.
- **Power‑law fitting**: The `powerlaw` package will be used for scaling exponent estimation; if convergence fails or the power-law model is not statistically preferred (per FR-011), that participant's data will be excluded from the correlation analysis.
- **Collinearity handling**: Degree and clustering coefficient are mathematically related in network topology. When both are tested, results will be framed descriptively with VIF diagnostics. If VIF ≥ 5, independent predictive effects are NOT claimed. This diagnostic is essential to avoid spurious conclusions about structure-function coupling.
- **Data quality filtering**: Participants with excessive EEG artifact (>30% channels removed after ICA) or disconnected structural graphs will be excluded from analysis.