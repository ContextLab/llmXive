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

1. **Given** a raw CSV file containing x,y coordinates of defects for a graphene sample, **When** the ingestion script processes the file, **Then** a NetworkX graph object is created with exactly N nodes (where N is the row count of valid coordinates) and edges exist only between nodes within the specified Euclidean distance threshold.
2. **Given** a dataset with missing coordinate values, **When** the ingestion script processes the file, **Then** the script skips the incomplete rows (rows with null or invalid x,y values), logs a warning with row number and sample_id, reports the count of skipped rows, and the resulting graph contains only valid nodes.
3. **Given** a dataset for MoS2 with a different lattice constant, **When** the ingestion script processes the file WITH statistical-override mode ACTIVE, **Then** the proximity threshold is automatically scaled by the material lattice constant parameter (retrieved from a material-type lookup table, all values in nanometers: graphene=0.246 nm, MoS₂=0.316 nm, default=0.250 nm for unknown materials) multiplied by a scaling factor (default 1.0). When statistical-override mode is INACTIVE (default), the threshold is a fixed physical distance on the nanometer scale..
4. **Given** multiple CSV files from heterogeneous sources (Materials Cloud, Zenodo, etc.) with potentially different coordinate conventions, **When** the ingestion script processes the files, **Then** the system normalizes coordinate conventions to Ångströms (detecting or accepting user-specified source units), merges them into a unified dataset, and logs any unit conversions applied.

---

### User Story 2 - Topological Metric Calculation (Priority: P2)

As a researcher, I need the system to calculate specific network topology metrics (clustering coefficient, average path length, degree distribution, size of the largest connected component, and percolation threshold) for each generated graph, so that I can quantify the structural arrangement of defects.

**Why this priority**: This step transforms the raw graph into the predictor variables required for the correlation analysis. It is distinct from the data ingestion but precedes the statistical analysis.

**Independent Test**: Can be fully tested by running the metric calculator on a synthetic graph with known properties (e.g., a random Erdos-Renyi graph) and verifying that the calculated metrics match theoretical expectations within a predefined tolerance threshold.

**Acceptance Scenarios**:

1. **Given** a valid graph object representing a defect network, **When** the metric calculator runs, **Then** it outputs a dictionary containing the global clustering coefficient (raw, non-normalized), average path length, degree distribution, size of the largest connected component (LCC) fraction, and percolation threshold with numerical precision of at least 6 decimal places.
2. **Given** a disconnected graph (common in sparse defect distributions), **When** the metric calculator runs, **Then** it calculates the average path length only over the largest connected component and flags the graph as "disconnected" in the metadata.
3. **Given** a graph where the degree distribution is required, **When** the metric calculator runs, **Then** it outputs the distribution as a histogram-ready list of (degree, frequency) pairs.
4. **Given** a graph across a range of proximity thresholds, **When** the metric calculator runs, **Then** it computes the percolation threshold (the critical proximity distance at which the largest connected component transitions from finite to infinite size) using numerical bisection over the threshold range [lower nanometer regime, 10 nm] with tolerance at a sub‑nanometer scale.

---

### User Story 3 - Correlation Analysis and Statistical Validation (Priority: P3)

As a researcher, I need the system to perform correlation analysis (linear and non-linear regression, Pearson and Spearman) between the calculated topological metrics and thermal conductivity values, including bootstrap resampling for significance, so that I can determine if defect topology predicts heat dissipation.

**Why this priority**: This is the core research question. While dependent on the previous steps, it represents the final analytical output. It is prioritized P3 as it requires the data and metrics to be ready first.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset where a known correlation (e.g., r=0.8) is injected between a "topology" column and a "conductivity" column, verifying the system detects the correlation with p < 0.05.

**Acceptance Scenarios**:

1. **Given** a dataset of samples with calculated topology metrics and corresponding thermal conductivity values, **When** the analysis script runs, **Then** it outputs a correlation matrix with Pearson and Spearman coefficients and associated p-values for each metric-conductivity pair.
2. **Given** the same dataset, **When** the bootstrap resampling module runs (n=1000 iterations, per Wikipedia, Bootstrapping (statistics)), **Then** it outputs a 95% confidence interval for the correlation coefficients and flags any results where the interval crosses zero.
3. **Given** multiple hypothesis tests (specifically, the 4 scalar topological metrics — clustering coefficient, average path length, LCC fraction, and percolation threshold; degree distribution is excluded as a non-scalar quantity — each tested with Pearson and Spearman correlation, plus polynomial regression models of degrees 1–3 for each metric-conductivity pair), **When** the analysis completes, **Then** it applies a Bonferroni correction across the total family of m=20 tests and reports the adjusted significance levels.
4. **Given** a dataset of samples with exact pairing (sample with both topology metrics and thermal conductivity), **When** the analysis script runs, **Then** it performs correlation analysis on the paired samples and reports the number of pairs used and the correlation matrix.
5. **Given** the analysis results, **When** the visualization module runs, **Then** it generates scatter plots of topology metrics vs. thermal conductivity with regression lines overlaid.
6. **Given** the correlation analysis results, **When** the density-adjustment module runs, **Then** it performs partial correlation analysis controlling for defect density (node count per unit area) as the single covariate, outputting both raw and density-adjusted correlation coefficients with corresponding p-values.
7. **Given** the target sample size of ≤50 samples, **When** the power analysis module runs, **Then** it reports statistical power for detecting an expected effect size r≥0.3 at α=0.05 with desired power≥0.8, and recommends sample-size adjustments if power is insufficient.

---

### Edge Cases

- What happens when a dataset contains zero defects (perfect crystal)? The system must handle this gracefully by assigning a null value to path length and clustering metrics, flagging the graph with a 'zero_defects' metadata flag, and logging a specific warning that no topology can be computed (See FR-010).
- How does the system handle datasets where the thermal conductivity value is missing for a specific sample? The system must exclude that sample from the correlation analysis but retain it in the raw data log for debugging (See FR-011).
- What happens if the proximity threshold creates a fully connected graph (all defects within distance)? The system must compute the true average path length (= 1.0 for unit-weight edges), flag the graph with a 'fully_connected' metadata flag, and include the true metric in correlation analysis rather than substituting a nominal placeholder (See FR-012).
- What happens if a CSV file's coordinate unit is ambiguous? The system will attempt auto-detection via metadata headers or default to Ångströms with a logged warning (See FR-001 and Assumptions).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest defect coordinate data from CSV files (single or multiple files from heterogeneous sources including Materials Cloud, Zenodo, etc.), normalize coordinate conventions to Ångströms (detecting or accepting user-specified source units), convert them into network graphs using a configurable Euclidean distance threshold, skip rows with missing or invalid coordinates, log a warning with row number and sample_id for each skipped row, report the count of skipped rows in the final results, merge data from multiple sources into a unified dataset, and log any unit conversions applied (See US-1).
- **FR-002**: System MUST calculate the global clustering coefficient (raw, non-normalized), average path length, degree distribution, size of the largest connected component (LCC) fraction (calculated as nodes in LCC / total nodes), and percolation threshold (critical proximity distance for LCC transition, computed via bisection over [0.5 nm, 10 nm] with tolerance sub‑nanometer scale.) for each input graph (See US-2).
- **FR-003**: System MUST perform Pearson and Spearman correlation analysis AND fit linear regression and polynomial regression (degree ≤ 3) models between each topological metric and the thermal conductivity values. Non-linear models (e.g., Gaussian Process) are optional for exploratory analysis only. Model selection for polynomial degree is performed via k-fold cross-validation (k=5, minimizing mean squared error) (See US-3).
- **FR-004**: System MUST execute bootstrap resampling (n=1000 iterations, per Wikipedia Bootstrapping (statistics)) to generate a 95% confidence interval for all correlation coefficients (See US-3).
- **FR-005**: System MUST apply a multiple-comparison correction (Bonferroni) to p-values when more than one hypothesis test is performed. The family of tests comprises the 4 scalar topological metrics used in correlation analysis — clustering coefficient, average path length, LCC fraction, and percolation threshold (the degree distribution is excluded from the correlation family because it is a non-scalar distribution rather than a single per-sample value) — × 2 correlation types (Pearson and Spearman) = 8 base tests, plus polynomial regression models (polynomial degrees 1–3 for each metric-conductivity pair = 4 metrics × 3 polynomial degrees = 12 additional tests). Total family m = 20 tests. Adjusted p-value = raw p × m, where m is the total number of tests (See US-3).
- **FR-006**: System MUST handle disconnected graphs by calculating path metrics only on the largest connected component and flagging the graph as "disconnected" in the metadata (See US-2).
- **FR-007**: System MUST output all results in a structured JSON format containing metrics, correlations, p-values, confidence intervals, and generate scatter plots of topology metrics vs. thermal conductivity with regression lines (See US-3).
- **FR-008**: System MUST allow the proximity threshold to be configured as a fixed physical distance (default 2.5 nm) or as a statistical multiplier of the material lattice constant (retrieved from a material-type lookup table with all entries in nanometers: default lattice constants are used for unknown materials, with graphene and MoS₂ assigned their standard literature values, and a default value for materials without established constants; threshold = lattice constant × scaling factor, scaling factor defaulting to 1.0) when statistical-override mode is active (See US-1).
- **FR-009**: System MUST perform a sensitivity analysis on the proximity threshold by testing values at multiple multiples of the default threshold value (default 2.5 nm), including 1.0x, 1.5x, 2.0x, and 2.5x configurations and reporting the stability of the correlation coefficient (See US-3).
- **FR-010**: System MUST handle zero-defect datasets (perfect crystals) by assigning null values to path length and clustering metrics, flagging the graph with a 'zero_defects' metadata flag, and logging a specific warning that no topology can be computed (See Edge Cases).
- **FR-011**: System MUST exclude samples with missing thermal conductivity values from the correlation analysis, retain them in the raw data log for debugging, and report the number of samples excluded in the final results (See Edge Cases).
- **FR-012**: System MUST detect fully connected graphs (all-to-all edges) and compute the true average path length (= 1.0 for unit-weight edges). The true value must be used in correlation analysis; if the graph is fully connected, the system MUST flag it with a 'fully_connected' metadata flag but MUST NOT substitute a nominal placeholder (See Edge Cases).
- **FR-013**: System MUST perform partial correlation analysis controlling for defect density (node count per unit area) as the single covariate, using the method of residuals or multiple regression. Report both raw correlations (metric vs. thermal conductivity) and density-adjusted correlations (residuals of metric regressed on density vs. residuals of thermal conductivity regressed on density) (See US-3).
- **FR-014**: System MUST report a statistical power analysis justifying the target sample size (≤50 samples) for detecting the expected correlation between topological metrics and thermal conductivity, assuming an effect size r≥0.3, α=0.05, and desired power≥0.8. If power is insufficient, the report MUST recommend an increased sample-size target or alternative analysis strategy (See US-3).

### Key Entities

- **DefectSample**: Represents a single physical sample; attributes include `sample_id`, `material_type` (graphene/MoS2), `defect_coordinates` (list of [x, y] pairs in Ångströms), and `thermal_conductivity` (single scalar bulk property measured at standard temperature, nullable; linked statistically rather than causally to local topology).
- **TopologyGraph**: Represents the network abstraction of a sample; attributes include `node_count`, `edge_count`, `clustering_coefficient` (raw), `clustering_coefficient_normalized` (optional, C_norm = C / ρ, computed only if density-adjustment analysis is explicitly requested via FR-013), `average_path_length`, `degree_distribution`, `lcc_fraction`, `percolation_threshold`, `is_connected`, `zero_defects` (boolean flag), and `fully_connected` (boolean flag).
- **AnalysisResult**: Represents the statistical output for a sample pair; attributes include `metric_name`, `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval`, `regression_model_params`, `density_adjusted_correlation_coefficient`, and `power_analysis_result`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correlation coefficient between topological metrics and thermal conductivity is measured against the null hypothesis of zero correlation (p < 0.05 after Bonferroni correction, m=20) (See US-3).
- **SC-002**: The stability of the correlation estimates is measured against the bootstrap resampling distribution (95% confidence interval width) (See US-3).
- **SC-003**: The validity of the multiple-comparison correction is verified by confirming that each adjusted p-value equals the raw p-value × 20 (where m=20 is the total number of tests in the family), and that no adjusted p-value is less than its raw p-value (See US-3).
- **SC-004**: The computational feasibility is measured against the constraint of execution within 6 hours on a CPU-only environment with ≤7 GB RAM for a dataset of up to 50 samples, each containing up to 10,000 defects, INCLUDING bootstrap resampling time (See FR-004).
- **SC-005**: The methodological robustness is measured by the presence of a sensitivity analysis for the proximity threshold testing values at 1.0x (default 2.5 nm), 1.5x, 2.0x, and 2.5x the default threshold value, with robustness measured by the standard deviation of the correlation coefficient across these four threshold values (target ≤ 0.05) (See FR-009).
- **SC-006**: The percolation-threshold calculation is verified by confirming that the bisection algorithm converges to a threshold value within a specified tolerance over the range [0.5 nm, 10 nm], and that the LCC size exhibits a phase transition at the computed threshold (See FR-002).
- **SC-007**: The model-selection procedure for polynomial regression is verified by confirming that the degree chosen (1 ≤ degree ≤ 3) minimizes the 5-fold cross-validation mean squared error (See FR-003).
- **SC-008**: The density-adjusted correlation analysis is verified by confirming that the density-adjusted correlation coefficients are computed from residuals of metric and thermal conductivity regressed on defect density (the single covariate), and that the adjusted p-values are reported (See FR-013).
- **SC-009**: The power analysis is verified by confirming that the reported power is computed for the assumed effect size r≥0.3, α=0.05, and the actual sample size N, and that the recommendation (increase N or use alternative strategy) is stated if power < 0.8 (See FR-014).

## Assumptions

- Public datasets from Materials Cloud, Zenodo, or similar repositories contain defect coordinate data and thermal conductivity measurements for at least 20 distinct samples. Exact sample pairing (sample with both topology metrics and thermal conductivity) is required for correlation analysis. Samples lacking a paired thermal conductivity value are excluded from the correlation analysis and reported in the final results.
- The proximity threshold for edge creation is configurable, with a default physical distance of a nanometer‑scale magnitude. (absolute units). A statistical multiplier mode (threshold = material lattice constant × scaling factor) is available as an optional override via a material-type lookup table with all entries in nanometers (graphene lattice constant on the order of a few angstroms, MoS₂ 0.316 nm, default 0.250 nm for unknown materials, scaling factor defaulting to 1.0).
- The analysis is observational; findings will be framed as associational correlations rather than causal effects, as the data is not derived from a randomized controlled trial.
- The thermal conductivity values provided in the datasets are measured at a standard temperature and do not require temperature normalization. Thermal conductivity is a single scalar value per sample; if missing or null, the sample is excluded from correlation analysis per FR-011.
- The "size of the largest connected component (LCC) fraction" will be approximated using standard networkX algorithms, assuming the defect network behaves as a random geometric graph.
- If a dataset lacks a specific material (e.g., MoS2), the analysis will proceed with the available material (e.g., graphene) and note the limitation in the final report.
- The analysis will treat the defect distribution as a static snapshot; temporal evolution of defect networks is out of scope.
- Bootstrap resampling is performed with n=1000 iterations per FR-004 and verified statistical convention (source: Wikipedia, Bootstrapping (statistics)). The total runtime including bootstrap must remain within the 6-hour constraint specified in SC-004.
- Expected effect size r≥0.3 is based on preliminary data and community consensus for moderate correlations in materials science (e.g., Ashcroft & Mermin, Solid State Physics, on defect-property relationships).
- Density-adjusted analysis is required because topological metrics (clustering coefficient, average path length, LCC fraction) are monotone functions of defect density at fixed proximity threshold, and density itself is a known driver of thermal conductivity. Controlling for density isolates the topology-specific contribution to heat dissipation.
- If a CSV file's coordinate unit is ambiguous, the system will attempt auto-detection via metadata headers or default to Ångströms with a logged warning.
- Coordinate conventions across heterogeneous sources (Materials Cloud, Zenodo, etc.) may differ; the system normalizes all coordinates to Ångströms and logs any unit conversions applied.
- The 6-hour computational constraint (SC-004) is a target requiring empirical validation during implementation. If the constraint proves infeasible with n=1000 bootstrap iterations on 50 samples × 10k defects each, sample-size or iteration-count trade-offs may be required; the final plan will document any adjustments and their statistical justification.