# Feature Specification: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

**Feature Branch**: `001-assessing-parcellation-sensitivity`  
**Created**: 2026-07-09  
**Status**: Draft  
**Input**: User description: "Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Multi-Resolution Matrix Generation (Priority: P1)

The system must download raw fMRI time-series data for a healthy adult cohort and generate adjacency matrices for three distinct parcellation resolutions (AAL-90, Schaefer-200, Schaefer-400) by applying the respective atlases to the same raw source data.

**Why this priority**: This is the foundational step. Without consistent multi-resolution matrices derived from a single source via distinct parcellation pipelines, no comparison of hub resilience is possible. It delivers the primary dataset required for all subsequent analysis.

**Independent Test**: The pipeline can be tested by verifying the existence of three distinct adjacency matrix files (one per resolution) for a single subject, ensuring they share the same underlying raw data but differ in node count, and confirming the total memory footprint fits within the available RAM limit of the CI runner (≤ 7 GB).

**Acceptance Scenarios**:

1. **Given** a valid connection to the OpenNeuro/HCP repository, **When** the script requests raw fMRI data for N=100 healthy adults, **Then** the system downloads the time-series data and successfully processes it into three separate adjacency matrices (90, 200, and 400 nodes) without memory overflow.
2. **Given** a single subject's raw fMRI stream, **When** the three different parcellation pipelines (AAL, Schaefer-200, Schaefer-400) are applied, **Then** the resulting matrices contain non-zero edge counts and the node labels correspond exactly to the respective atlas definitions.

---

### User Story 2 - Centrality Computation and Hub Definition (Priority: P2)

The system must calculate degree centrality and betweenness centrality for all nodes in each resolution and define "hubs" as the top [deferred] of nodes by metric value for each scheme.

**Why this priority**: This transforms raw connectivity into the specific metrics (centrality) and constructs (hubs) required to answer the research question. It is the core analytical logic.

**Independent Test**: The calculation logic can be tested on a small, synthetic 5-node graph where the centrality values and top-10% cutoff are manually calculable, ensuring the system correctly identifies the single "hub" node.

**Acceptance Scenarios**:

1. **Given** the three generated adjacency matrices, **When** the centrality algorithms (degree and betweenness) are executed, **Then** the system outputs a CSV for each resolution containing a centrality score for every node, with no missing values.
2. **Given** the centrality scores for a resolution with N nodes, **When** the top 10% threshold is applied, **Then** the system identifies exactly `floor(N * 0.10)` nodes as "hubs" and flags them in the output metadata.

---

### User Story 3 - Sensitivity Quantification and Statistical Validation (Priority: P3)

The system must compute Jaccard/Dice overlap indices, Spearman rank correlations (after spatial alignment), and a permutation test to determine if observed hub overlap exceeds chance, visualizing the results.

**Why this priority**: This delivers the final scientific answer to the research question (quantifying resilience) and provides the statistical validation required for publication.

**Independent Test**: The statistical module can be tested by running it on a dataset with randomized node labels; the system must report that the proportion of significant results (p < 0.05) across 50 independent randomization runs does not exceed 5%, confirming the logic correctly identifies "no resilience" and controls Type I error.

**Acceptance Scenarios**:

1. **Given** the hub sets from the 90-node and 200-node resolutions (after spatial mapping), **When** the overlap analysis is run, **Then** the system outputs a Jaccard index and Dice coefficient, and a Spearman correlation coefficient between the centrality ranks.
2. **Given** the observed hub overlap statistic, **When** the permutation test runs 1,000 iterations, **Then** the system calculates a p-value and generates a Venn diagram heatmap showing the overlap distribution.

---

### Edge Cases

- **What happens when** the downloaded dataset contains missing subjects or corrupted matrix files? **The system must skip the corrupted entry, log a warning, and proceed with the remaining N subjects to ensure the analysis completes without crashing.**
- **How does the system handle** resolutions where the node count is not perfectly divisible by 10 (e.g., 90 nodes)? **The system must use a configurable proportional threshold to strictly define the top [deferred] set, ensuring a consistent integer count of hubs across all resolutions.**
- **What happens if** the permutation test exceeds the 6-hour CI time limit? **The system must default to a reduced number of iterations (minimum 500) and log a warning that statistical power for the permutation test is limited by time constraints, but the analysis must still complete.**

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw fMRI time-series data for a cohort of at least 100 healthy adults from a public repository (e.g., OpenNeuro) and generate three adjacency matrices by applying AAL-90, Schaefer-200, and Schaefer-400 parcellation pipelines to the raw data. (See US-1)
- **FR-002**: System MUST calculate degree centrality and betweenness centrality for every node in all three generated adjacency matrices using CPU-tractable graph libraries (e.g., NetworkX). (See US-2)
- **FR-003**: System MUST define "hubs" as the top [deferred] of nodes by centrality score for each resolution, using `floor(N * 0.10)` to determine the cutoff count. (See US-2)
- **FR-004**: System MUST compute the Jaccard index and Dice coefficient to measure the set-theoretic overlap of hub sets between every pair of parcellation resolutions. (See US-3)
- **FR-005**: System MUST perform a Spearman's rank correlation analysis between centrality values of nodes across the different parcellation schemes, but ONLY after mapping higher-resolution nodes to the lower-resolution atlas via spatial overlap (majority vote). (See US-3)
- **FR-006**: System MUST execute a permutation test (minimum 1,000 iterations) to determine if the observed hub overlap is statistically significant (p < 0.05) compared to a null distribution generated by permuting the spatially-mapped labels. (See US-3)
- **FR-007**: System MUST generate visualizations including a heatmap of centrality correlation and a Venn diagram of hub overlap. (See US-3)
- **FR-008**: System MUST perform a sensitivity analysis sweeping the hub definition threshold over a range of plausible values to report how hub overlap rates vary. (See US-3)
- **FR-009**: System MUST implement a spatial mapping function that aligns nodes from higher-resolution atlases (Schaefer-200/400) to lower-resolution atlases (AAL-90) using a majority-vote spatial overlap method to enable valid node-wise comparisons. (See US-3)

### Key Entities

- **Connectivity Matrix**: A symmetric adjacency matrix representing the weighted connections between brain regions for a single subject, derived from raw fMRI data via a specific parcellation atlas.
- **Parcellation Scheme**: A specific atlas definition (e.g., AAL-90) mapping continuous brain data to discrete nodes.
- **Hub Set**: The set of nodes identified as the top [deferred] by a specific centrality metric within a specific parcellation scheme.
- **Overlap Metric**: A quantitative value (Jaccard/Dice) representing the similarity between two Hub Sets.
- **Spatial Map**: A lookup table or function that maps node indices from a high-resolution atlas to their corresponding low-resolution atlas nodes based on spatial overlap.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variation in hub identification (measured by Jaccard index) across resolutions is measured against the baseline of perfect overlap (Jaccard = 1.0) to quantify resilience. (See FR-004)
- **SC-002**: The stability of node rankings (measured by Spearman correlation) is measured against the null hypothesis of random ranking (r = 0) to assess metric consistency, calculated only after spatial alignment. (See FR-005)
- **SC-003**: The statistical significance of observed hub overlap (measured by permutation p-value) is measured against the standard alpha threshold of 0.05 to validate findings. (See FR-006)
- **SC-004**: The sensitivity of hub definitions (measured by the change in Jaccard index) is measured across the mandatory swept thresholds to assess robustness of the [deferred] cutoff. (See FR-008)
- **SC-005**: The computational feasibility (measured by total runtime and peak RAM usage) is measured against the CI runner limits (≤6 hours, ≤7 GB RAM) to ensure the analysis is reproducible. (See FR-001)

## Assumptions

- **Assumption about data availability**: The Human Connectome Project or OpenNeuro repositories contain raw fMRI time-series data for at least 100 healthy adult subjects that can be processed into AAL-90, Schaefer-200, and Schaefer-400 resolutions.
- **Assumption about dataset-variable fit**: The downloaded raw data contains sufficient quality and coverage to compute both degree and betweenness centrality without requiring imputation; if the source lacks specific edge types, the analysis will be limited to the available modalities.
- **Assumption about inference framing**: Since the study uses observational data (existing healthy cohorts) without random assignment to parcellation schemes, all findings regarding "hub resilience" are framed as associational relationships between atlas choice and metric stability, not causal effects.
- **Assumption about power**: A sample size of N=100 is sufficient to detect a moderate effect size in the correlation of centrality ranks; if the observed effect is small, the study will explicitly acknowledge the power limitation in the results.
- **Assumption about multiplicity**: The analysis involves multiple hypothesis tests (correlations and overlap indices across three resolutions); a correction for multiple comparisons (e.g., Bonferroni or FDR) will be applied to the final p-values.
- **Assumption about compute feasibility**: The graph-theory computations (centrality, overlap) for N=100 subjects and 400 nodes can be executed entirely on a CPU within the 6-hour limit, avoiding any need for GPU acceleration or large model inference.
- **Assumption about threshold justification**: The 10% threshold for hub definition is based on the community standard for identifying "rich club" or "hub" nodes in connectome literature; the sensitivity analysis (FR-008) will verify that results are not an artifact of this specific cutoff.
- **Assumption about measurement validity**: The AAL-90, Schaefer-200, and Schaefer-400 atlases are recognized, validated parcellation schemes in the neuroscience community, ensuring the node definitions are biologically meaningful.
- **Assumption about predictor collinearity**: While degree and betweenness centrality are definitionally related (both depend on network topology), the analysis will treat them as distinct metrics to be compared descriptively, and a collinearity diagnostic will be reported to avoid claiming independent predictive effects where none exist.
- **Assumption about spatial mapping validity**: The majority-vote spatial overlap method provides a biologically plausible and mathematically consistent mapping between nodes of different resolutions for the purpose of rank correlation analysis.