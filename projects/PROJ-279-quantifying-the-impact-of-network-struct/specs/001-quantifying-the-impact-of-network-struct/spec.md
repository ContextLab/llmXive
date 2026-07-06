# Feature Specification: Quantifying the Impact of Network Structure on Heat Transport in Amorphous Silicon

**Feature Branch**: `001-quantify-heat-transport`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Network Structure on Heat Transport in Amorphous Silicon"

## Hypothesis Targets

> The following are scientific hypotheses to be tested. They are NOT system success criteria. The system succeeds if it correctly measures and reports the values needed to evaluate these hypotheses.

- **H-001**: The correlation strength (Pearson r) between the top topological descriptor and thermal conductivity will exceed |0.7| with p < 0.05.
- **H-002**: The predictive performance of the model will yield an R² score > 0.1, significantly better than a random baseline (R² > 0.0).
- **H-003**: The most frequent ring size in the amorphous silicon dataset will be between 5 and 7 atoms.
- **H-004**: The top 3 features in the regression model will have p-values < 0.05.

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

The researcher needs to download pre-existing molecular dynamics (MD) trajectories of amorphous silicon (a-Si) from a public repository and convert them into graph representations where nodes represent atoms and edges represent bonds within a specific cutoff radius.

**Why this priority**: This is the foundational step. Without valid graph representations of the atomic structures, no topological metrics can be calculated, and the subsequent correlation analysis is impossible. It delivers the primary data artifact required for the study.

**Independent Test**: Can be fully tested by verifying the successful download of a sample trajectory, the construction of a graph with the correct number of nodes (atoms) and edges (bonds), and the validation that the graph topology matches the spatial coordinates within a defined tolerance.

**Acceptance Scenarios**:

1. **Given** a valid URL to an a-Si MD trajectory on Zenodo, **When** the system executes the download script, **Then** the trajectory file is saved locally with a verified checksum, and the file size is > 0 MB.
2. **Given** a loaded trajectory file, **When** the graph construction module runs with a configurable cutoff radius (default 3.0 Å), **Then** the resulting graph contains exactly N nodes (where N is the atom count) and the average degree of the graph is logged.
3. **Given** a constructed graph, **When** the system validates connectivity, **Then** the graph is fully connected (single component) or the number of disconnected components is logged as a warning if the system is fragmented.

---

### User Story 2 - Topological and Vibrational Descriptor Calculation (Priority: P2)

The researcher needs to compute specific topological metrics (ring statistics, bond orientational order parameters, clustering coefficients) AND vibrational spectral descriptors (VDOS, participation ratios) for each atomic configuration to serve as predictors for thermal conductivity.

**Why this priority**: This transforms raw structural data into the scientific variables required to answer the research question. Including vibrational descriptors addresses the physical mechanism of heat transport (phonons) rather than relying solely on static topology. It is the core analytical engine of the feature.

**Independent Test**: Can be fully tested by calculating descriptors on a known crystal structure (where values are deterministic) and comparing them against theoretical expectations, ensuring the code logic is sound before applying it to disordered systems.

**Acceptance Scenarios**:

1. **Given** a graph representation of an a-Si structure, **When** the ring statistics module runs, **Then** the system outputs a distribution of ring sizes (3 to 10 atoms).
2. **Given** a graph representation, **When** bond orientational order parameters (e.g., Steinhardt parameters) and vibrational density of states (VDOS) are calculated, **Then** the system returns a vector of values where the average Q6 parameter is calculated and the VDOS spectrum is generated.
3. **Given** a set of calculated descriptors, **When** the system aggregates them, **Then** the output is a structured dataset (CSV/JSON) linking each configuration ID to its corresponding vector of topological and vibrational metrics.

---

### User Story 3 - Statistical Correlation and Visualization (Priority: P3)

The researcher needs to perform a statistical analysis (Ridge regression and non-linear model comparison) to correlate the topological descriptors with thermal conductivity values, validate the model via k-fold cross-validation (or Leave-One-Out if N < 30), and generate visualizations (scatter plots, feature importance charts).

**Why this priority**: This delivers the final scientific insight (the correlation) and the evidence required to validate the hypothesis. It is the culmination of the workflow.

**Independent Test**: Can be fully tested by running the regression on a synthetic dataset with a known linear relationship and verifying that the model recovers the expected coefficient and R² score within a defined margin of error.

**Acceptance Scenarios**:

1. **Given** the dataset of topological descriptors and thermal conductivity values, **When** the Ridge regression and Random Forest models are trained with k=5 folds (or LOOCV if N < 30), **Then** the system outputs a mean R² score and standard deviation for each model, and reports the p-values for the top 3 features.
2. **Given** the trained models, **When** the visualization module runs, **Then** it generates a scatter plot with the top predictor on the X-axis and thermal conductivity on the Y-axis, showing a fitted regression line and the Pearson correlation coefficient (r) displayed in the legend.
3. **Given** the feature importance results, **When** the system generates the importance chart, **Then** the chart displays the top 5 features with error bars representing the standard deviation across cross-validation folds.

---

### User Story 4 - Data Independence Verification (Priority: P1)

The researcher needs to verify that the thermal conductivity target values are derived from an independent source (experimental data or a distinct simulation ensemble) and are converged to the thermodynamic limit to avoid circular validation.

**Why this priority**: This ensures scientific validity. If the target is derived from the same simulation used for predictors, the correlation is tautological. This step prevents invalid scientific conclusions.

**Independent Test**: Can be fully tested by verifying that the metadata of the thermal conductivity data explicitly states the source method (e.g., "Experimental" or "Green-Kubo on distinct ensemble") and system size (> 1000 atoms).

**Acceptance Scenarios**:

1. **Given** a dataset of thermal conductivity values, **When** the system validates the source metadata, **Then** the system confirms the values are from an independent source or distinct ensemble.
2. **Given** a dataset derived from simulation, **When** the system checks system size, **Then** the system confirms the simulation size is ≥ 1000 atoms or flags a warning if smaller.

---

### Edge Cases

- What happens when the downloaded trajectory file is corrupted or incomplete? (System must detect checksum mismatch and abort with a clear error message).
- How does the system handle atomic configurations with unexpected coordination numbers (e.g., dangling bonds or high-coordination defects > 5)? (System must flag these atoms and optionally exclude them or log them as outliers).
- What occurs if the calculated thermal conductivity values are missing for certain configurations in the dataset? (System must skip those configurations during regression and log the count of skipped samples).
- What happens if the sample size N < 30? (System must automatically switch from 5-fold cross-validation to Leave-One-Out Cross-Validation (LOOCV) to maintain statistical stability).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download molecular dynamics trajectories of amorphous silicon from a specified public repository (e.g., Zenodo) and verify file integrity via checksums (See US-1).
- **FR-002**: System MUST construct a graph representation of atomic structures where nodes are atoms and edges are bonds defined by a configurable cutoff radius. The system MUST perform a sensitivity analysis by sweeping the radius over {2.8, 3.0, 3.2} Å and report the impact on graph topology (See US-1).
- **FR-003**: System MUST calculate ring statistics (distribution of ring sizes), bond orientational order parameters (Steinhardt Q6), clustering coefficients, AND vibrational density of states (VDOS) and participation ratios for every configuration (See US-2).
- **FR-004**: System MUST perform Ridge regression AND a non-linear model (Random Forest or Kernel Ridge) to map the calculated topological and vibrational descriptors to thermal conductivity values. The system MUST use 5-fold cross-validation if N ≥ 30, otherwise it MUST use Leave-One-Out Cross-Validation (LOOCV) (See US-3).
- **FR-005**: System MUST generate a scatter plot of the top predictor vs. thermal conductivity and a feature importance bar chart with error bars (See US-3).
- **FR-006**: System MUST validate that the thermal conductivity target values are derived from an independent source (experimental data or a distinct simulation ensemble) to avoid circular validation (See US-4).
- **FR-007**: System MUST validate that the thermal conductivity target values are converged to the thermodynamic limit (system size ≥ 1000 atoms) or are experimental data (See US-4).

### Key Entities

- **AtomicConfiguration**: Represents a snapshot of the a-Si system, containing atom coordinates, element types, and the associated thermal conductivity value.
- **TopologicalDescriptor**: A vector of numerical values derived from the atomic graph, including ring statistics, order parameters, and clustering coefficients.
- **VibrationalDescriptor**: A vector of numerical values derived from the vibrational spectrum, including VDOS peaks and participation ratios.
- **RegressionModel**: The statistical model trained to predict thermal conductivity, containing coefficients, intercept, and cross-validation metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation strength (Pearson r) between the top topological descriptor and thermal conductivity is measured against the hypothesis target (H-001). The project succeeds if the observed value meets the target (|r| > 0.7) with p < 0.05.
- **SC-002**: The statistical significance of the correlation is measured by the p-value of the regression coefficient. The project succeeds if the p-value is < 0.05.
- **SC-003**: The predictive performance of the model is measured by the R² score from cross-validation. The project succeeds if the R² score is > 0.0 (better than random) and > 0.1 (practical utility) (See US-3).
- **SC-004**: The computational feasibility is measured by the total execution time of the analysis pipeline, which must not exceed 6 hours on a standard CPU-only runner (See Assumptions).
- **SC-005**: The model comparison succeeds if the non-linear model (Random Forest/Kernel Ridge) achieves an R² score within 5% of the Ridge regression model or exceeds it, justifying the complexity.

## Assumptions

- **Dataset Availability**: Publicly available molecular dynamics trajectories of amorphous silicon with pre-calculated or calculable thermal conductivity values exist on Zenodo or HuggingFace and fit within the disk storage constraints of the GitHub Actions runner.
- **Methodological Framing**: The study is observational; therefore, any identified relationships are framed as associational correlations, not causal effects, as the dataset does not involve random assignment of structural features.
- **Compute Constraints**: The analysis (graph construction, descriptor calculation, and Ridge regression) is computationally lightweight enough to run on a standard multi-core CPU with modest memory resources without requiring GPU acceleration or large-model inference.
- **Threshold Justification**: The cutoff radius for bond definition is configurable, and a sensitivity analysis is performed over {2.8, 3.0, 3.2} Å to ensure robustness.
- **Power Limitation**: The sample size (number of configurations) is limited by the available public dataset; if the dataset is small (< 30 samples), the study uses Leave-One-Out Cross-Validation (LOOCV) to maintain statistical power.
- **Measurement Validity**: The thermal conductivity values associated with the downloaded trajectories are derived from established methods (e.g., Green-Kubo) on systems with ≥ 1000 atoms or are experimental data, ensuring they are converged to the thermodynamic limit and treated as ground truth for the correlation analysis.
- **Data Independence**: The thermal conductivity values used as targets are derived from an independent source (experimental data or a distinct simulation ensemble) to avoid circular validation.