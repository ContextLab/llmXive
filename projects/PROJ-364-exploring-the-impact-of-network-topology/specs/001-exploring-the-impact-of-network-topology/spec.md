# Feature Specification: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

**Feature Branch**: `001-network-topology-heat-dissipation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

As a researcher, I need to ingest raw defect coordinate datasets from public repositories (Materials Cloud, Zenodo) and convert them into network graphs where nodes represent defects and edges represent proximity within a defined threshold, so that I can establish the structural basis for topology analysis.

**Why this priority**: Without a valid graph representation of the defect distributions, no topological metrics can be calculated. This is the foundational data pipeline step.

**Independent Test**: Can be fully tested by loading a known sample dataset (e.g., a 500x500 pixel graphene simulation with 100 known defect coordinates) and verifying that the resulting graph has the correct node count and that edge density matches the proximity threshold logic.

**Acceptance Scenarios**:

1. **Given** a raw CSV file containing x,y coordinates of defects for a graphene sample, **When** the ingestion script processes the file, **Then** a NetworkX graph object is created with exactly N nodes (where N is the row count) and edges exist only between nodes within the specified Euclidean distance threshold.
2. **Given** a dataset with missing coordinate values, **When** the ingestion script processes the file, **Then** the script skips the incomplete rows and logs a warning, ensuring the resulting graph contains only valid nodes.
3. **Given** a dataset for MoS2 with a different lattice constant, **When** the ingestion script processes the file, **Then** the proximity threshold is automatically scaled by the lattice constant parameter to maintain physical consistency.

---

### User Story 2 - Topological Metric Calculation (Priority: P2)

As a researcher, I need the system to calculate specific network topology metrics (clustering coefficient, average path length, degree distribution, percolation threshold) for each generated graph, so that I can quantify the structural arrangement of defects.

**Why this priority**: This step transforms the raw graph into the predictor variables required for the correlation analysis. It is distinct from the data ingestion but precedes the statistical analysis.

**Independent Test**: Can be fully tested by running the metric calculator on a synthetic graph with known properties (e.g., a random Erdos-Renyi graph) and verifying that the calculated metrics match theoretical expectations within a tolerance of 0.01.

**Acceptance Scenarios**:

1. **Given** a valid graph object representing a defect network, **When** the metric calculator runs, **Then** it outputs a dictionary containing the global clustering coefficient, average path length, and percolation threshold with numerical precision of at least 6 decimal places.
2. **Given** a disconnected graph (common in sparse defect distributions), **When** the metric calculator runs, **Then** it calculates the average path length only over the largest connected component and flags the graph as "disconnected" in the metadata.
3. **Given** a graph where the degree distribution is required, **When** the metric calculator runs, **Then** it outputs the distribution as a histogram-ready list of (degree, frequency) pairs.

---

### User Story 3 - Correlation Analysis and Statistical Validation (Priority: P3)

As a researcher, I need the system to perform correlation analysis (linear and non-linear) between the calculated topological metrics and thermal conductivity values, including bootstrap resampling for significance, so that I can determine if defect topology predicts heat dissipation.

**Why this priority**: This is the core research question. While dependent on the previous steps, it represents the final analytical output. It is prioritized P3 as it requires the data and metrics to be ready first.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset where a known correlation (e.g., r=0.8) is injected between a "topology" column and a "conductivity" column, verifying the system detects the correlation with p < 0.05.

**Acceptance Scenarios**:

1. **Given** a dataset of samples with calculated topology metrics and corresponding thermal conductivity values, **When** the analysis script runs, **Then** it outputs a correlation matrix with Pearson and Spearman coefficients and associated p-values for each metric-conductivity pair.
2. **Given** the same dataset, **When** the bootstrap resampling module runs (n=1000 iterations), **Then** it outputs a 95% confidence interval for the correlation coefficients and flags any results where the interval crosses zero.
3. **Given** multiple hypothesis tests (e.g., testing 5 different metrics), **When** the analysis completes, **Then** it applies a Bonferroni correction to the p-values and reports the adjusted significance levels.

---

### Edge Cases

- What happens when a dataset contains zero defects (perfect crystal)? The system must handle this gracefully by assigning a "null" or "infinity" value to path length metrics and logging a specific warning that no topology can be computed.
- How does the system handle datasets where the thermal conductivity value is missing for a specific sample? The system must exclude that sample from the correlation analysis but retain it in the raw data log for debugging.
- What happens if the proximity threshold creates a fully connected graph (all defects within distance)? The system must detect this and report the average path length as 1.0, preventing division-by-zero errors in subsequent calculations.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest defect coordinate data from CSV files and convert them into network graphs using a configurable Euclidean distance threshold (See US-1).
- **FR-002**: System MUST calculate the global clustering coefficient, average path length, degree distribution, and percolation threshold for each input graph (See US-2).
- **FR-003**: System MUST perform Pearson and Spearman correlation analysis between each topological metric and the thermal conductivity values (See US-3).
- **FR-004**: System MUST execute bootstrap resampling (n=1000 iterations) to generate 95% confidence intervals for all correlation coefficients (See US-3).
- **FR-005**: System MUST apply a multiple-comparison correction (Bonferroni) to p-values when more than one hypothesis test is performed (See US-3).
- **FR-006**: System MUST handle disconnected graphs by calculating path metrics only on the largest connected component and flagging the result (See US-2).
- **FR-007**: System MUST output all results in a structured JSON format containing metrics, correlations, p-values, and confidence intervals (See US-3).

### Key Entities

- **DefectSample**: Represents a single physical sample; attributes include `sample_id`, `material_type` (graphene/MoS2), `defect_coordinates`, and `thermal_conductivity`.
- **TopologyGraph**: Represents the network abstraction of a sample; attributes include `node_count`, `edge_count`, `clustering_coefficient`, `average_path_length`, and `is_connected`.
- **AnalysisResult**: Represents the statistical output for a sample pair; attributes include `metric_name`, `correlation_coefficient`, `p_value`, `adjusted_p_value`, and `confidence_interval`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correlation coefficient between topological metrics and thermal conductivity is measured against the null hypothesis of zero correlation (p < 0.05) (See US-3).
- **SC-002**: The stability of the correlation estimates is measured against the bootstrap resampling distribution (95% confidence interval width) (See US-3).
- **SC-003**: The validity of the multiple-comparison correction is measured against the family-wise error rate control (See US-3).
- **SC-004**: The computational feasibility is measured against the constraint of execution within 6 hours on a CPU-only environment with ≤7 GB RAM (See FR-004).
- **SC-005**: The methodological robustness is measured by the presence of a sensitivity analysis for the proximity threshold (See FR-002).

## Assumptions

- Public datasets from Materials Cloud, Zenodo, or similar repositories contain defect coordinate data paired with thermal conductivity measurements for at least 20 distinct samples to enable statistical correlation.
- The proximity threshold for edge creation in the network graph is set to 2.5 times the average nearest-neighbor distance of defects, a value chosen based on phonon mean free path considerations in 2D materials.
- The analysis is observational; findings will be framed as associational correlations rather than causal effects, as the data is not derived from a randomized controlled trial.
- The thermal conductivity values provided in the datasets are measured at a standard temperature (e.g., 300K) and do not require temperature normalization.
- The "percolation threshold" metric will be approximated using standard networkX algorithms, assuming the defect network behaves as a random geometric graph.
- If a dataset lacks a specific material (e.g., MoS2), the analysis will proceed with the available material (e.g., graphene) and note the limitation in the final report.
- The analysis will treat the defect distribution as a static snapshot; temporal evolution of defect networks is out of scope.
- The bootstrap resampling will be capped at a sufficient number of iterations to ensure the total runtime remains [deferred] on the free-tier GitHub Actions runner.
