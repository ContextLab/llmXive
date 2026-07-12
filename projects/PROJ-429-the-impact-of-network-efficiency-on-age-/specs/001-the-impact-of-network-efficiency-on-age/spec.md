# Feature Specification: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Feature Branch**: `001-network-efficiency-aging`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How does resting-state brain network efficiency, as measured by graph-theoretical metrics from EEG, change with age, and does reduced network efficiency predict cognitive performance in older adults?"

## User Scenarios & Testing

### User Story 1 - Compute Graph-Theoretical Network Efficiency Metrics (Priority: P1)

As a data scientist, I need to compute graph-theoretical metrics (characteristic path length, clustering coefficient, global/local efficiency, modularity) from preprocessed resting-state EEG data for each participant, so that I can quantify the topological organization of brain networks.

**Why this priority**: This is the foundational data generation step. Without accurate, reproducible network metrics, no correlation analysis with age or cognition is possible. It represents the core "measurement" capability of the system.

**Independent Test**: Can be fully tested by running the preprocessing and graph construction pipeline on a small, fixed subset of PhysioNet data and verifying that the output CSV contains the expected metric columns with non-NaN values for all valid epochs.

**Acceptance Scenarios**:

1. **Given** a preprocessed EEG dataset with artifact-removed epochs, **When** the graph construction module runs using coherence between 10-20 system electrodes, **Then** the output file must contain exactly one row per participant with columns for path length, clustering, global efficiency, and modularity.
2. **Given** a participant with insufficient signal quality (SNR < 10dB), **When** the pipeline processes their data, **Then** the output row for that participant must contain `NaN` for all metrics and a flag indicating "Low Signal Quality".

---

### User Story 2 - Correlate Network Metrics with Age and Cognition (Priority: P2)

As a researcher, I need to perform statistical correlations (Spearman rank) between the computed network efficiency metrics and participant age and cognitive scores (MMSE/MoCA), so that I can determine if network degradation tracks with aging and cognitive decline.

**Why this priority**: This addresses the primary research question. It transforms raw metrics into scientific findings regarding the relationship between brain organization and aging/cognition.

**Independent Test**: Can be tested by running the statistical analysis module on a synthetic dataset with known correlations and verifying that the output reports the correct correlation coefficients and p-values within a tolerance of 0.01.

**Acceptance Scenarios**:

1. **Given** a dataset of network metrics and corresponding age/cognitive scores, **When** the correlation analysis runs, **Then** the output must report a Spearman correlation coefficient (r) and p-value for each metric against age and against cognitive scores.
2. **Given** a dataset where no true correlation exists (random noise), **When** the analysis runs, **Then** the reported p-values for all metric-variable pairs must be > 0.05 in at least 95% of simulation runs (validating the statistical test's validity).

---

### User Story 3 - Generate Age-Stratified Network Visualization and Regression Analysis (Priority: P3)

As a stakeholder, I need to visualize the network changes across age groups (young, middle, older) and see the results of a multiple regression controlling for sex and education, so that I can assess the robustness of the findings and communicate the age-specific patterns.

**Why this priority**: This provides interpretability and context. While the correlations (P2) answer "is there a relationship?", this story answers "how does it look across the lifespan?" and "does it hold up to confounding variables?"

**Independent Test**: Can be tested by generating plots from a sample dataset and verifying that the regression output includes coefficients for age, sex, and education, and that the visualization clearly distinguishes the three age groups.

**Acceptance Scenarios**:

1. **Given** a dataset stratified into three age groups, **When** the visualization module runs, **Then** it must generate a plot showing the mean network efficiency metric per group with error bars (95% CI).
2. **Given** a dataset with sex and education metadata, **When** the multiple regression runs, **Then** the output must include a table of coefficients, standard errors, and p-values for Age, Sex, and Education as predictors of the primary network metric.

### Edge Cases

- **What happens when** the dataset contains participants with missing cognitive scores? **How does the system handle it?** The system must exclude these participants from the cognitive correlation analysis but retain them for the age correlation if age is present.
- **How does the system handle** EEG recordings with excessive artifact (e.g., >50% of epochs rejected by ICA)? The system must flag these participants as "Excluded" in the final report and not include them in the correlation statistics.
- **What happens when** the sample size for the "older" group (60+) is too small (<15 participants) for robust statistical inference? The system must output a warning flag in the results summary indicating "Low Power for Older Group" and adjust the confidence intervals accordingly.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse resting-state EEG data specifically from the Temple University Hospital (TUH) EEG Corpus hosted on PhysioNet (accession ID: tuh_eeg), ensuring all required variables (age, cognitive score, EEG signal) are present. (See US-1)
- **FR-002**: System MUST implement a preprocessing pipeline using MNE-Python to bandpass filter (1-40 Hz), remove artifacts via ICA, and segment data into 2-second epochs. (See US-1)
- **FR-003**: System MUST compute graph-theoretical metrics (characteristic path length, clustering coefficient, modularity) from functional connectivity matrices derived using coherence or phase-locking value. Global and local efficiency MUST be calculated as the mathematical inverse of the characteristic path length to avoid circular validation, but reported as distinct derived metrics. (See US-1)
- **FR-004**: System MUST perform Spearman rank correlation analysis between network metrics and both age and cognitive performance scores, explicitly framing results as associational. The system MUST account for the family of tests (multiple metrics vs. multiple outcomes) when calculating power and error rates. (See US-2)
- **FR-005**: System MUST implement a multiple regression model to control for covariates (sex, education) and report adjusted effect sizes for network metrics predicting cognitive performance. (See US-3)
- **FR-006**: System MUST apply multiple-comparison correction (e.g., Bonferroni or FDR) when testing >1 hypothesis (e.g., multiple metrics vs. multiple outcomes) to control family-wise error rate. (See US-2)
- **FR-007**: System MUST validate that all cognitive assessment instruments used (e.g., MMSE, MoCA) match a hardcoded registry of standard, validated tools with citable references. If an instrument is not in the registry, the system MUST flag the participant as "Invalid Cognitive Measure" and exclude them from cognitive analysis. (See US-2)
- **FR-008**: System MUST perform a sensitivity analysis on the network density threshold by sweeping values over {0.05, 0.1, 0.15} and reporting the stability of correlation coefficients (variation < 0.05) to ensure findings are not artifacts of the threshold choice. (See US-1)

### Key Entities

- **Participant**: Represents a single individual in the study, with attributes: `age`, `sex`, `education_years`, `cognitive_score`, `signal_quality_flag`.
- **NetworkMetric**: Represents a computed graph-theoretical value for a participant, with attributes: `path_length`, `clustering_coeff`, `global_efficiency`, `modularity`.
- **CorrelationResult**: Represents the statistical relationship between a metric and a variable, with attributes: `metric_name`, `variable_name`, `correlation_coefficient`, `p_value`, `corrected_p_value`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The proportion of participants with valid, non-NaN network metrics is measured against the total number of downloaded participants to assess data quality and preprocessing efficacy. (See US-1)
- **SC-002**: The statistical power for detecting a correlation of r=0.3, adjusted for the family of tests (Bonferroni-corrected alpha), is measured against a simulation-based power analysis to ensure the study is not underpowered (minimum acceptable power ≥ 0.80). (See US-2)
- **SC-003**: The consistency of correlation coefficients across different sensitivity thresholds for artifact rejection (e.g., [deferred] vs [deferred] epoch rejection) is measured to verify the robustness of the findings (coefficients must vary by < 0.05 across thresholds). (See US-2)
- **SC-004**: The family-wise error rate (FWER) is measured against the nominal alpha level (0.05) after applying the specified multiple-comparison correction method. (See US-2)

## Assumptions

- **Assumption about data source**: The PhysioNet datasets used contain both raw EEG signals and verified demographic/cognitive metadata for a sufficient number of participants (N > 100) to achieve statistical power for r=0.3.
- **Assumption about methodology**: The relationship between network efficiency and aging/cognition is associative; no causal claims will be made due to the observational nature of the data (no random assignment).
- **Assumption about compute environment**: The entire analysis (preprocessing, graph computation, statistical testing) fits within the GitHub Actions free-tier constraints (2 CPU cores, ~7 GB RAM, ≤6 hours) by processing data in batches or using a representative subset if the full corpus exceeds memory limits.
- **Assumption about threshold justification**: The primary coherence threshold for defining edges in the functional connectivity matrix is set to the top [deferred] of connections (density=0.1) based on community standards for sparse brain networks. A sensitivity analysis (see FR-008) will validate that results are not dependent on this specific value.
- **Assumption about measurement validity**: The cognitive scores (MMSE/MoCA) available in the dataset are administered according to standard clinical protocols and are not self-reported estimates.
- **Assumption about collinearity**: Age and cognitive decline are expected to be correlated, but the regression model will include a Variance Inflation Factor (VIF) check to ensure that multicollinearity does not invalidate the coefficient estimates.