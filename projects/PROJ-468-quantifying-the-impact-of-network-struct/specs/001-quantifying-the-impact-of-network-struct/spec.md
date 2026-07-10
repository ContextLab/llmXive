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
2. **Given** a simulation file with missing force data for specific contacts, **When** the extraction script runs, **Then** the system logs a warning for the affected timesteps and excludes the entire timestep if >50% of contacts are missing; otherwise, it imputes missing forces as 0.0 and retains the timestep.
3. **Given** a dataset of [deferred] number of particles processed on a GitHub Actions free-tier runner (2 vCPU), **When** the script runs, **Then** the memory usage target is ≤ 6GB and the runtime target is ≤ A duration of approximately half an hour. for the small-scale test case; if these targets are exceeded, the system triggers subsampling per FR-010. Note: The production trigger for subsampling is estimated memory > 6.5GB or estimated runtime > 5.5 hours (see FR-010).

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
- **Error Scenario**: How does the system handle a simulation where the contact network is disconnected (isolated particles)? The system must handle `NaN` values for clustering coefficient gracefully by excluding the timestep if >50% of contacts are missing; otherwise, it imputes missing forces as 0.0. For force heterogeneity, if all edges have zero forces, the metric is set to 0.0.
- **Data Volume**: What happens if the simulation output file is corrupted or truncated mid-write? The system must validate the file integrity before processing and abort with a clear error message rather than producing partial, misleading results.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse Yade-DEM output files to extract particle positions, contact forces, and total energy at each timestep. Edges in the contact network MUST be defined by geometric overlap > 0, regardless of force magnitude, to ensure independence from the dissipation outcome (See US-1). Topology metrics (coordination, clustering) are derived solely from this binary graph.
- **FR-002**: System MUST calculate the mean coordination number and clustering coefficient for the contact network at every timestep (See US-1).
- **FR-003**: System MUST calculate the force heterogeneity (coefficient of variation of contact forces) for every timestep. If forces are imputed as 0.0 or are zero, the coefficient of variation is calculated only over edges with non-zero forces; if all edges are zero, the metric is set to 0.0 (See US-1).
- **FR-004**: System MUST compute the energy dissipation rate using the sum of force × relative velocity over all contacts (internal damping model). This calculation is independent of the external Work_Input term, which is retained only as a control variable (See US-1).
- **FR-005**: System MUST perform Pearson and Spearman correlation analyses between each network metric (coordination, clustering, force heterogeneity) and the dissipation rate (See US-2).
- **FR-006**: System MUST execute a Generalized Least Squares (GLS) regression with AR(1) error structure (or Newey-West corrected OLS) to determine the combined predictive power of network metrics on dissipation rate, accounting for temporal autocorrelation (See US-2).
- **FR-007**: System MUST include driving amplitude as a control variable in the regression model to account for confounding effects (See US-2).
- **FR-008**: System MUST validate correlation consistency across multiple datasets using a mixed-effects model or ANOVA to test for slope differences (See US-3).
- **FR-009**: System MUST generate a PDF report containing scatter plots with regression lines, residual diagnostics, and a correlation heatmap (See US-3).
- **FR-010**: System MUST enforce a memory cap and a runtime limit to ensure resource efficiency. Subsampling MUST trigger automatically if estimated memory > 6.5GB or estimated runtime > 5.5 hours (providing a safety buffer before the 7GB/6h hard limits) (See US-1).
- **FR-011**: System MUST detect and exclude non-steady-state transients by identifying windows where the rolling variance of dissipation rate exceeds a significant threshold over 100 timesteps; analysis is restricted to steady-state windows only (See US-2).

### Key Entities

- **Contact Network**: A graph where nodes represent particles and edges represent physical contacts (defined by geometric overlap); attributes include edge weight (force magnitude) and node degree (coordination number).
- **Dissipation Record**: A time-indexed record containing the calculated energy loss rate (sum of force × relative velocity) and the concurrent state of the system (driving amplitude, volume fraction).
- **Analysis Result**: A structured output containing statistical metrics (correlation coefficients, p-values, regression coefficients with corrected standard errors) and diagnostic plots for a specific dataset or combined set.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The system MUST output the p-value for the correlation test; the pipeline flags results with p < 0.01 as significant (See US-2).
- **SC-002**: The adjusted R-squared value of the multiple linear regression model is measured against a baseline of 0.0; the result is considered successful if adjusted R-squared > 0.1 or if the model is significantly better than a null model (p < 0.05) (See US-2).
- **SC-003**: The consistency of correlation slopes across datasets is measured against the result of an ANOVA test; the system outputs the ANOVA p-value; if p > 0.05, the report flags the result as "Generalizable across amplitudes", otherwise "Non-generalizable" (See US-3).
- **SC-004**: The memory footprint of the analysis pipeline is measured against the free-tier runner's memory limit., requiring successful completion without OOM errors (See US-1).
- **SC-005**: The total runtime of the end-to-end pipeline (extraction + analysis + visualization) is measured against a predefined time limit per GitHub Actions job (See US-1).

## Assumptions

- **Dataset Availability**: Publicly available DEM datasets (e.g., from Yade-DEM or OpenGRAN) exist and contain the necessary variables: particle positions, contact forces, and total energy, with no gaps in the variable list, consistent with standard Yade-DEM output schemas.
- **Observational Framing**: The analysis is strictly observational; findings will be framed as "associations" between network topology and dissipation, not causal effects, as there is no random assignment of network structures.
- **Compute Constraints**: The entire analysis (including subsampling if necessary) will fit within the free-tier CI limits (multiple CPU cores, Substantial RAM, a limited time window). using CPU-tractable methods (scikit-learn, scipy) without GPU acceleration or 8-bit quantization.
- **Threshold Justification**: The significance threshold for statistical tests is fixed at p < 0.01, based on standard physics literature conventions for multiple hypothesis correction (Bonferroni or FDR will be applied if >5 tests are run).
- **Sensitivity Analysis**: A sensitivity analysis will be performed by sweeping the subsampling fraction across a range of values (e.g., full, partial) to ensure results are robust, as no specific cutoff was defined in the idea.
- **Measurement Validity**: The "force heterogeneity" metric (coefficient of variation) is a validated proxy for network stress distribution in granular physics, citing Majmudar & Behringer (year) and related literature.
- **Predictor Collinearity**: Coordination number and clustering coefficient may be definitionally related (bounded by local density); the analysis will treat them as a joint descriptive set rather than claiming independent causal effects, and will include a Variance Inflation Factor (VIF) diagnostic.