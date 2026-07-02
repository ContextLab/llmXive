# Feature Specification: Predicting Gene Essentiality from Protein Interaction Network Topology

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Gene Essentiality from Protein Interaction Network Topology"

## User Scenarios & Testing

### User Story 1 - Cross-Species Correlation Analysis (Priority: P1)

The system must download Protein-Protein Interaction (PPI) networks from STRING and gene essentiality labels from DEG for several model organisms., compute network centrality metrics (degree, betweenness, eigenvector), and calculate Spearman's rank correlation between these metrics and essentiality status.

**Why this priority**: This is the core scientific hypothesis test. Without establishing the baseline correlation between topology and essentiality, no further comparative or sensitivity analysis is meaningful. It delivers the primary research output.

**Independent Test**: Can be fully tested by executing the analysis pipeline for a single organism (e.g., *S. cerevisiae*) and verifying that the output includes a valid correlation coefficient and p-value for degree centrality against essentiality labels.

**Acceptance Scenarios**:

1. **Given** a valid organism ID (e.g., "9606" for Human) exists in both STRING and DEG, **When** the system fetches data and computes degree centrality, **Then** the output must contain a Spearman correlation coefficient (ρ) and associated p-value for that organism.
2. **Given** an organism with no overlapping genes between STRING and DEG, **When** the system attempts to map identifiers, **Then** the system must log a warning, skip that organism, and continue processing the remaining list without crashing.

---

### User Story 2 - Comparative Statistical Testing (Priority: P2)

The system must compare the correlation coefficients obtained from different organisms using Phylogenetic Generalized Least Squares (PGLS) to determine if the strength of the topology-essentiality relationship varies significantly by species, accounting for evolutionary history.

**Why this priority**: This addresses the second part of the research question regarding systematic variation across the tree of life. It transforms individual results into a comparative evolutionary insight while correcting for phylogenetic non-independence, which is critical for scientific validity.

**Independent Test**: Can be tested by running the analysis on at least two distinct organisms (e.g., a bacterium and a eukaryote) with a provided phylogenetic tree, verifying the generation of a PGLS statistic and p-value indicating the significance of the variation.

**Acceptance Scenarios**:

1. **Given** valid correlation coefficients (ρ1, ρ2), sample sizes (n1, n2), and a phylogenetic tree for two different organisms, **When** the system applies PGLS, **Then** the output must include the PGLS test statistic and the two-tailed p-value for the difference.
2. **Given** a set of organisms where the null hypothesis (no difference in correlation strength) is true, **When** the comparison is run, **Then** the resulting p-values should be distributed uniformly (verified via a simple bootstrap or known statistical property check in the test suite).

---

### User Story 3 - Sensitivity Analysis on Network Confidence (Priority: P3)

The system must re-run the correlation analysis varying the STRING confidence score threshold (500, 700, 900) to assess the robustness of the findings to network construction parameters.

**Why this priority**: This addresses the "network construction method" variable in the research question. It ensures the findings are not artifacts of a specific arbitrary cutoff, fulfilling the requirement for methodological robustness.

**Independent Test**: Can be tested by running the pipeline with the default threshold (700) and one alternative (e.g., 500) for a single organism, verifying that the system produces a comparative table of correlation coefficients across thresholds.

**Acceptance Scenarios**:

1. **Given** a configuration specifying multiple confidence thresholds (e.g., [500, 700, 900]), **When** the analysis runs, **Then** the output must contain a separate correlation result for each threshold.
2. **Given** a high-confidence threshold (900) that results in a sparse network with fewer than 500 edges, **When** centrality is computed, **Then** the system must flag the network sparsity in the logs but still attempt to compute metrics (returning NaNs or 0s where undefined) rather than failing immediately.

### Edge Cases

- **What happens when** a gene in the essentiality database (DEG) has no corresponding entry in the PPI network (STRING)? The system must exclude such genes from the correlation calculation (as they have undefined centrality) and report the count of excluded genes.
- **How does the system handle** organisms where the PPI network is fully disconnected (no edges)? The system must detect this, skip centrality calculation (or assign 0), and log that the network topology is invalid for this analysis.
- **What happens when** the dataset size for a specific organism is too small for Phylogenetic Generalized Least Squares (PGLS) (e.g., n < 10)? The system must skip the comparative test for that pair and log a "Power insufficient" warning.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download PPI networks from STRING for 5-8 model organisms with a default confidence score threshold of ≥700 (See US-1).
- **FR-002**: System MUST download gene essentiality labels (binary essential/non-essential) from the DEG database for the same set of organisms (See US-1).
- **FR-003**: System MUST map gene identifiers between STRING and DEG using Ensembl BioMart to ensure consistent matching (See US-1).
- **FR-004**: System MUST compute degree, betweenness, and eigenvector centrality metrics using CPU-tractable algorithms (NetworkX) for each organism's network. The algorithm must complete within 30 minutes per organism on a standard CPU core for networks with ≤ 25,000 nodes (See US-1).
- **FR-005**: System MUST calculate Spearman's rank correlation between each centrality metric and binary essentiality labels for each organism (See US-1).
- **FR-006**: System MUST perform Phylogenetic Generalized Least Squares (PGLS) to statistically compare correlation coefficients across different organisms, accounting for phylogenetic non-independence (See US-2).
- **FR-007**: System MUST support sensitivity analysis by re-running the correlation calculation across a configurable set of confidence thresholds (default: 500, 700, 900) (See US-3).
- **FR-008**: System MUST apply the Benjamini-Hochberg method for multiple-comparison correction when reporting p-values for the cross-species comparisons to control the false discovery rate (See US-2).
- **FR-009**: System MUST skip comparative tests (PGLS) if the effective sample size (n) for an organism is < 10 and log a "Power insufficient" warning (See Edge Cases).
- **FR-010**: System MUST generate degree-preserving random graphs for each organism. and compare the observed correlation coefficient against the null distribution generated by these randomized networks to validate that the correlation is not an artifact of scale-free topology (See US-1, Scientific Soundness).

### Key Entities

- **Organism Profile**: Represents a single species (e.g., *H. sapiens*), containing metadata (ID, name) and references to its network and label data.
- **Network Graph**: A graph structure representing the PPI network for a specific organism, containing nodes (genes/proteins) and edges (interactions with confidence scores).
- **Essentiality Label**: A binary attribute associated with a gene node, indicating "Essential" (1) or "Non-Essential" (0).
- **Centrality Metric**: A numerical value derived from the graph structure (e.g., degree centrality) assigned to each node.
- **Correlation Result**: A record containing the Spearman ρ, p-value, sample size (n), and the specific metric/organism/threshold used.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of organisms where a statistically significant correlation (p < 0.05) is found for degree centrality is measured against an empirical null distribution generated by shuffling essentiality labels [deferred] times and calculating the proportion of rejections for each shuffle; the observed proportion must significantly exceed a high percentile of this null distribution (See US-1).
- **SC-002**: The variation in correlation coefficients across different confidence thresholds (500, 700, 900) is measured against the stability of the primary finding, defined as the absolute difference in correlation coefficients (|Δρ|) being ≤ 0.1 across all thresholds (See US-3).
- **SC-003**: The statistical significance of differences in correlation strength between species (via PGLS) is measured against the threshold of p < 0.05 (adjusted for multiplicity using Benjamini-Hochberg) (See US-2).
- **SC-004**: The total runtime of the analysis pipeline on a standard GitHub Actions runner (limited CPU resources, constrained RAM) is measured against the 6-hour limit. (See Assumptions).
- **SC-005**: The percentage of genes successfully mapped between STRING and DEG is measured against the total number of essential genes in the source dataset to verify data coverage (See US-1).

## Assumptions

- **Dataset Variable Fit**: It is assumed that the STRING database contains interaction edges for the genes listed in the DEG database for the selected model organisms. If a required gene is missing from STRING, it will be excluded from the analysis (See FR-003).
- **Inference Framing**: The analysis is observational; findings will be framed as associational correlations between network topology and essentiality, not as causal mechanisms. No randomization is applied.
- **Power Limitation**: For organisms with small networks (n < 30), statistical power for correlation detection is limited; results for these organisms will be flagged as "Low Power" in the output.
- **Compute Feasibility**: The analysis assumes that NetworkX centrality calculations for the selected organisms (max. on the order of tens of thousands of nodes) will complete within the 6-hour GitHub Actions limit on CPU-only hardware without requiring GPU acceleration.
- **Threshold Justification**: The default confidence threshold of 700 is selected based on STRING's standard recommendation for high-confidence interactions; the sensitivity analysis (500, 900) covers the plausible range of community standards.
- **Measurement Validity**: The essentiality labels from DEG are assumed to be the ground truth for the analysis, despite potential experimental noise or context-specific essentiality not captured in the database.
- **Predictor Collinearity**: Degree, betweenness, and eigenvector centralities are known to be correlated; the analysis will report joint descriptive statistics but will not claim independent predictive effects for highly collinear metrics without a collinearity diagnostic.
- **Phylogenetic Data Availability**: It is assumed that a valid phylogenetic tree (Newick format) covering the selected organisms is available to perform PGLS. If unavailable, the comparative test (FR-006) will be skipped with a warning.