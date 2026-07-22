# Feature Specification: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

**Feature Branch**: `001-quantify-network-heat-transport`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Defect Network Construction (Priority: P1)

The researcher MUST be able to download molecular dynamics (MD) snapshots of disordered alloys (Cu-Ni, Au-Ag) from a public repository and automatically construct a graph representation where nodes represent atomic sites and edges connect nearest-neighbor atoms of mismatched species.

**Why this priority**: This is the foundational step. Without a correctly constructed graph derived from the raw atomic coordinates, no subsequent analysis of topology or correlation with thermal conductivity can occur. It defines the "predictor" variables for the entire study.

**Independent Test**: The system can be tested by running the ingestion script on a known small subset of the dataset and verifying that the resulting NetworkX graph object contains the expected number of nodes and edges, and that edge weights (if used) correctly reflect species mismatch.

**Acceptance Scenarios**:

1. **Given** a valid MD snapshot file from the OpenKim or Materials Cloud repository containing atomic positions and species for a Cu-Ni alloy, **When** the ingestion script is executed, **Then** a NetworkX graph object is generated where nodes correspond to atomic indices and edges exist only between nearest neighbors with different species.
2. **Given** a snapshot file with missing metadata or corrupted coordinate data, **When** the ingestion script is executed, **Then** the system halts with a descriptive error message identifying the specific file and the nature of the data failure, preventing silent corruption of the analysis pipeline.

---

### User Story 2 - Topological Metric Extraction (Priority: P2)

The researcher MUST be able to compute a vector of network descriptors (clustering coefficient, average path length, degree distribution moments, percolation threshold) for each constructed defect network.

**Why this priority**: This step transforms the raw graph into the quantitative features required for statistical analysis. It is the core "feature engineering" phase that enables the research question to be tested.

**Independent Test**: The system can be tested by running the metric extraction on a synthetic graph with known properties (e.g., a complete graph or a random Erdős-Rényi graph) and verifying that the calculated metrics match theoretical expectations within a tolerance of < 1e-6.

**Acceptance Scenarios**:

1. **Given** a constructed defect graph for a specific alloy snapshot, **When** the metric extraction module runs, **Then** it outputs a structured record containing the clustering coefficient (C), average path length (L), and percolation threshold (p_c) as floating-point numbers.
2. **Given** a graph that is disconnected (multiple components), **When** the average path length is calculated, **Then** the system calculates the metric only over the largest connected component (or reports NaN with a warning) to ensure mathematical validity, rather than failing or returning infinity.

---

### User Story 3 - Statistical Correlation and Visualization (Priority: P3)

The researcher MUST be able to correlate the extracted topological metrics with the thermal conductivity values from the dataset metadata and generate visualizations (scatter plots, correlation heatmaps) with statistical significance testing (p < 0.05).

**Why this priority**: This delivers the final research insight. It answers the primary research question by quantifying the relationship between structure and transport properties.

**Independent Test**: The system can be tested by running the correlation analysis on a synthetic dataset where a known linear relationship exists between a predictor and an outcome, verifying that the correlation coefficient and p-value are computed correctly.

**Acceptance Scenarios**:

1. **Given** a dataset of paired (network metric, thermal conductivity) values, **When** the correlation analysis is executed, **Then** the system outputs a table of Pearson/Spearman correlation coefficients and corresponding p-values for each metric, flagging any correlation with p < 0.05.
2. **Given** a set of significant correlations, **When** the visualization module runs, **Then** it generates scatter plots with regression lines and a correlation heatmap, saving them as high-resolution PNG files in the designated output directory.

---

### Edge Cases

- What happens if the dataset contains only a single atomic configuration (N=1)? The system must detect this and report that statistical correlation is impossible, exiting gracefully rather than attempting division by zero or returning NaN.
- How does the system handle a dataset where the thermal conductivity metadata is missing for a specific snapshot? The system must skip that sample during correlation but log the exclusion count, ensuring the analysis proceeds on valid data without crashing.
- What if the percolation threshold calculation fails due to numerical instability in a highly sparse graph? The system must catch the exception, assign a default "undefined" value, and flag the sample for manual review in the final report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse MD snapshot files from the specified public repositories (OpenKim/Materials Cloud) for Cu-Ni and Au-Ag alloys, extracting atomic species and 3D coordinates. (See US-1)
- **FR-002**: System MUST construct a defect network graph where nodes represent lattice sites and edges connect nearest-neighbor atoms of mismatched species, using a cutoff distance derived from the average nearest-neighbor distance in the pure crystal. (See US-1)
- **FR-003**: System MUST compute the clustering coefficient, average path length, degree distribution moments (mean, variance), and percolation threshold for every constructed graph. (See US-2)
- **FR-004**: System MUST perform Pearson and Spearman correlation analysis between each network metric and the corresponding thermal conductivity value, calculating p-values for all tests. (See US-3)
- **FR-005**: System MUST generate scatter plots with regression lines and a correlation heatmap, saving them as PNG files with a resolution of at least 300 DPI. (See US-3)
- **FR-006**: System MUST apply a Bonferroni correction (or similar family-wise error rate control) to the p-values when reporting significance, given that multiple hypotheses (metrics) are tested simultaneously. (See US-3)

### Key Entities

- **AtomicSnapshot**: Represents a single MD configuration; attributes include atomic positions (3D vector), species (string/enum), and thermal conductivity (float).
- **DefectGraph**: Represents the topological structure of disorder; attributes include nodes (atomic indices), edges (nearest-neighbor pairs), and computed metrics (clustering, path length, etc.).
- **CorrelationResult**: Represents the statistical outcome; attributes include metric name, correlation coefficient, p-value, corrected p-value, and significance flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between network metrics and thermal conductivity is measured against the null hypothesis of zero correlation (random chance), with significance determined by the corrected p-value. (See FR-004)
- **SC-002**: The accuracy of the extracted network metrics (clustering, path length) is measured against theoretical values for known graph topologies (e.g., random graphs, lattices) to ensure computational validity. (See FR-003)
- **SC-003**: The validity of the dataset-variable fit is measured by confirming that every required variable (atomic species, position, thermal conductivity) is present in the source data for ≥ 95% of the available snapshots. (See FR-001)
- **SC-004**: The robustness of the statistical inference is measured by the consistency of correlation results when the significance threshold is swept (e.g., p < 0.01, p < 0.05, p < 0.10), ensuring no single arbitrary cutoff drives the conclusion. (See FR-006)

## Assumptions

- **Dataset Availability**: The OpenKim or Materials Cloud repositories contain at least 20 distinct atomic configurations for both Cu-Ni and Au-Ag alloys with associated thermal conductivity metadata, sufficient to perform a basic correlation analysis.
- **Metric Definition**: The "nearest neighbor" relationship is defined by the Voronoi tessellation or a fixed cutoff distance of 3.5 Å, which is a standard community default for metallic alloys and will be applied uniformly across all samples.
- **Computational Feasibility**: The total number of atomic configurations in the dataset is ≤ 50, ensuring that the graph construction and metric extraction (O(N log N) or O(N^2) depending on algorithm) will complete within the 6-hour CPU limit of the GitHub Actions free tier.
- **Statistical Validity**: The dataset is assumed to be representative of the alloy system, and any observed correlations are interpreted as associational (observational) rather than causal, consistent with the lack of randomization in the source data.
- **Threshold Justification**: The significance threshold of p < 0.05 is adopted as the standard community default for physics literature; a sensitivity analysis will sweep this value to {0.01, 0.05, 0.10} to confirm result stability.
