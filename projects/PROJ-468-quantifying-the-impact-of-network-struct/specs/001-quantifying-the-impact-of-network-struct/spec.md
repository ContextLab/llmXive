# Feature Specification: Quantifying the Impact of Network Structure on Energy Dissipation in Driven Granular Materials

**Feature Branch**: `001-network-dissipation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Network Structure on Energy Dissipation in Driven Granular Materials"

## User Scenarios & Testing

### User Story 1 - Core Data Extraction and Metric Calculation (Priority: P1)

As a researcher, I need the system to ingest raw DEM simulation output files, extract contact networks (particle pairs and forces), and calculate fundamental topology metrics (coordination number, clustering coefficient, force heterogeneity) and energy dissipation rates per timestep, so that I have a clean, structured dataset for initial analysis.

**Why this priority**: This is the foundational capability. Without accurate extraction and calculation of the predictor (network) and outcome (dissipation) variables, no statistical analysis can occur. It represents the Minimum Viable Product for the research pipeline.

**Independent Test**: Can be fully tested by running the pipeline on a single, small-scale synthetic DEM dataset (e.g., a representative number of particles and timesteps) and verifying that the output CSV contains non-null values for coordination number, clustering coefficient, force heterogeneity, and dissipation rate for every timestep.

**Acceptance Scenarios**:

1. **Given** a valid Yade-DEM output file containing particle positions and contact forces, **When** the extraction script is executed, **Then** a structured dataset is produced with rows for each timestep containing the mean coordination number, clustering coefficient, force heterogeneity, and calculated energy dissipation rate.
2. **Given** a simulation file with missing force data for specific contacts, **When** the extraction script runs, **Then** the system logs a warning for the affected timesteps. If >50% of the *total expected contacts* for that timestep are missing, the entire timestep is excluded. If <50% are missing, missing forces are imputed as 0.0, the force heterogeneity metric is marked as 'UNRELIABLE', and the dissipation calculation proceeds but is flagged as 'ESTIMATED'.
3. **Given** a dataset of [deferred] particles processed on a GitHub Actions free-tier runner (2 vCPU), **When** the script runs, **Then** the memory usage target is ≤ 7GB and the runtime target is ≤ 6 hours; if these targets are exceeded, the system triggers subsampling per FR-008.

---

### User Story 2 - Statistical Correlation and Regression Analysis (Priority: P2)

As a researcher, I need the system to perform statistical correlation (Pearson/Spearman) and multiple linear regression (with autocorrelation correction) between the extracted network metrics and the dissipation rates, so that I can quantify the strength and direction of the relationship.

**Why this priority**: This transforms raw data into scientific insight. It directly addresses the primary research question regarding the impact of topology on dissipation.

**Independent Test**: Can be tested by feeding the system a pre-processed CSV with known correlations (simulated data) and verifying that the output report correctly identifies the correlation coefficients (within a a small tolerance threshold) and regression p-values.

**Acceptance Scenarios**:

1. **Given** a dataset with calculated network metrics and dissipation rates (filtered for steady-state windows), **When** the analysis module is executed, **Then** the system outputs a report containing Pearson and Spearman correlation coefficients for each metric against dissipation rate, including p-values.
2. **Given** a dataset with multiple predictors (coordination number, clustering, force heterogeneity) and driving amplitude, **When** the multiple linear regression is run, **Then** the system outputs the coefficient estimates, standard errors (Newey-West corrected), and adjusted R-squared value for the combined model.
3. **Given** a dataset where the relationship is non-linear, **When** the analysis runs, **Then** the system flags a potential non-linearity if the residual regression quadratic term has p < 0.05 OR if the absolute residual skewness > 0.5.

---

### User Story 3 - Cross-Dataset Validation and Visualization (Priority: P3)

As a researcher, I need the system to validate the observed correlations across multiple independent datasets with varying particle counts and driving amplitudes, and generate visualizations (scatter plots, heatmaps), so that I can confirm the robustness of the findings and prepare them for publication.

**Why this priority**: This ensures the findings are generalizable and not artifacts of a single simulation setup. It is critical for the "publishable" criteria but relies on the successful completion of US-1 and US-2.

**Independent Test**: Can be tested by providing two distinct datasets with different particle counts (e.g., 1k vs 5k) and verifying that the system generates a combined correlation plot and a mixed-effects model summary showing whether the slope is consistent across datasets.

**Acceptance Scenarios**:

1. **Given** two input datasets with different driving amplitudes, **When** the validation module runs, **Then** the system produces a scatter plot overlaying the regression lines for both datasets and outputs an ANOVA result indicating if the slopes are significantly different.
2. **Given** a successful correlation analysis, **When** the visualization module runs, **Then** the system generates a PDF report containing a correlation heatmap, residual distribution plots, and a time-series plot of dissipation rate vs. force heterogeneity.
3. **Given** a dataset where the correlation is statistically insignificant (p > 0.05), **When** the report is generated, **Then** the system explicitly labels the result as "Non-significant" and includes a note suggesting potential causes (e.g., sample size, noise) in the summary text.

### Edge Cases

- **Boundary Condition**: What happens when the driving amplitude is zero (static packing)? The system must detect this and calculate dissipation as the absolute sum of kinetic and potential energy changes (|ΔKE + ΔPE|) rather than dividing by zero work input, or flag the dataset as "static" if both work and energy change are zero.
- **Error Scenario**: How does the system handle a simulation where the contact network is disconnected (isolated particles)? The system must handle `NaN` values for clustering coefficient gracefully by excluding the timestep if >50% of system-wide contacts are missing. If <50% are missing, the clustering coefficient is set to 0.0 (representing no clustering) rather than imputing forces, as force imputation does not resolve topological NaNs.
- **Data Volume**: What happens if the simulation output file is corrupted or truncated mid-write? The system must validate the file integrity before processing and abort with a clear error message rather than producing partial, misleading results.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse Yade-DEM output files to extract particle positions, contact forces, and total energy at each timestep. Edges in the contact network MUST be defined by geometric overlap > 0, regardless of force magnitude, to ensure independence from the dissipation outcome (See US-1). Topology metrics (coordination, clustering) are derived solely from this binary graph.
- **FR-002**: System MUST calculate the mean coordination number and clustering coefficient for the contact network at every timestep (See US-1).
- **FR-002b**: System MUST calculate the force heterogeneity (coefficient of variation of contact forces) for every timestep (See US-1).
- **FR-003**: System MUST compute the energy dissipation rate using the equation: Dissipation = Work_Input - (ΔKE + ΔPE). Work_Input is calculated directly from the driving boundary parameters (e.g., wall velocity) in the input file. If Work_Input is zero, Dissipation = |ΔKE + ΔPE|. The result is normalized by the timestep interval. The final metric used for correlation is the *normalized* dissipation rate (Dissipation / Work_Input) to avoid tautology with driving input (See US-1).
- **FR-004**: System MUST perform Pearson and Spearman correlation analyses between each network metric (coordination, clustering, force heterogeneity) and the *normalized* dissipation rate. Rows flagged as 'ESTIMATED' or 'UNRELIABLE' MUST be excluded from this analysis (See US-2).
- **FR-005**: System MUST execute a Generalized Least Squares (GLS) regression with AR(1) error structure (or Newey-West corrected OLS) to determine the combined predictive power of network metrics on dissipation rate, accounting for temporal autocorrelation (See US-2).
- **FR-005b**: System MUST include driving amplitude as a control variable in the regression model to account for confounding effects (See US-2).
- **FR-006**: System MUST validate correlation consistency across multiple datasets using a mixed-effects model or ANOVA to test for slope differences (See US-3).
- **FR-007**: System MUST generate a PDF report containing scatter plots with regression lines, residual diagnostics, and a correlation heatmap (See US-3).
- **FR-008**: System MUST enforce a memory cap and a runtime limit to ensure resource efficiency. Subsampling MUST trigger automatically if the estimated memory usage exceeds a predefined high threshold or estimated runtime exceeds a substantial duration. The estimation MUST be performed by a linear extrapolation from a small initial portion of the file. (See US-1).
- **FR-009**: System MUST calculate a 'Topology-Only' metric (e.g., degree distribution) and a 'Force-Only' metric to distinguish between structural connectivity and force transmission, ensuring the analysis is not circular (See US-2).
- **FR-010**: System MUST perform an Augmented Dickey-Fuller (ADF) test on the time series. If non-stationarity is detected (p > 0.05), the data MUST be segmented into quasi-stationary windows (e.g., a suitable number of timesteps) and the regression performed on each segment, with results aggregated (See US-2).

### Key Entities

- **Contact Network**: A graph where nodes represent particles and edges represent physical contacts (defined by geometric overlap); attributes include edge weight (force magnitude) and node degree (coordination number).
- **Dissipation Record**: A time-indexed record containing the calculated energy loss rate (sum of force × relative velocity) and the concurrent state of the system (driving amplitude, volume fraction).
- **Analysis Result**: A structured output containing statistical metrics (correlation coefficients, p-values, regression coefficients with corrected standard errors) and diagnostic plots for a specific dataset or combined set.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The system MUST output the p-value for the correlation test; the pipeline flags results with p < 0.01 as significant (See US-2).
- **SC-002**: The adjusted R-squared value of the multiple linear regression model is measured against a baseline of zero. to determine the proportion of variance in dissipation explained by network topology (See US-2).
- **SC-003**: The consistency of correlation slopes across datasets is measured against the result of an ANOVA test (p > 0.05 required to claim generalizability across driving amplitudes) (See US-3).
- **SC-004**: The memory footprint of the analysis pipeline is measured against the free-tier runner limit., requiring successful completion without OOM errors. This limit applies to the *actual* runtime memory usage after any subsampling triggered by FR-008 (See US-1).
- **SC-005**: The total runtime of the end-to-end pipeline (extraction + analysis + visualization) is measured against a predefined job duration limit per GitHub Actions job. This limit applies to the *actual* runtime after any subsampling triggered by FR-008 (See US-1).

## Assumptions

- **Dataset Availability**: Publicly available DEM datasets (e.g., from Yade-DEM or OpenGRAN) exist and contain the necessary variables: particle positions, contact forces, and total energy. If these variables are missing, the system will fail gracefully with a clear error message.
- **Observational Framing**: The analysis is strictly observational; findings will be framed as "associations" between network topology and dissipation, not causal effects, as there is no random assignment of network structures.
- **Compute Constraints**: The entire analysis (including subsampling if necessary) will fit within the free-tier CI limits (a small number of CPU cores, limited RAM, 6 hours). using CPU-tractable methods (scikit-learn, scipy) without GPU acceleration or 8-bit quantization.
- **Threshold Justification**: The significance threshold for statistical tests is fixed at p < 0.01, based on standard physics literature conventions for multiple hypothesis correction (Bonferroni or FDR will be applied if >5 tests are run).
- **Sensitivity Analysis**: A sensitivity analysis will be performed by sweeping the subsampling fraction across a range of values (e.g., full, partial) to ensure results are robust, as no specific cutoff was defined in the idea.
- **Measurement Validity**: The "force heterogeneity" metric (coefficient of variation) is a validated proxy for network stress distribution in granular physics, citing Majmudar & Behringer (2005) and related literature.
- **Predictor Collinearity**: Coordination number and clustering coefficient may be definitionally related (bounded by local density); the analysis will treat them as a joint descriptive set rather than claiming independent causal effects, and will include a Variance Inflation Factor (VIF) diagnostic.