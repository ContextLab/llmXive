# Feature Specification: Uncovering Latent Relationships Between Molecular Descriptors and Antibiotic Resistance

**Feature Branch**: `001-uncovering-latent-relationships`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Uncovering Latent Relationships Between Molecular Descriptors and Antibiotic Resistance"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Descriptor Computation (Priority: P1)

The researcher downloads approved and investigational antibiotic structures from ChEMBL and ZINC15, retrieves resistance phenotype frequencies from NCBI Pathogen Detection, and computes a standardized set of molecular descriptors (e.g., logP, TPSA) using RDKit.

**Why this priority**: This is the foundational step. Without the merged dataset of structures, resistance labels, and calculated descriptors, no analysis, visualization, or statistical testing can occur. It delivers the primary data asset required for the research.

**Independent Test**: The pipeline can be tested by running the data ingestion script on a subset of 50 compounds and verifying the output `descriptors.csv` contains the correct columns, valid numeric values, and matches the expected InChIKey counts without requiring downstream statistical analysis.

**Acceptance Scenarios**:

1. **Given** the ChEMBL and ZINC15 API endpoints are accessible, **When** the ingestion script runs, **Then** the output CSV contains at least 200 molecular descriptor columns and matches >90% of the requested antibiotic InChIKeys.
2. **Given** the NCBI Pathogen Detection FTP site is accessible, **When** the resistance frequency fetch script runs, **Then** the resistance data is successfully merged with the descriptor table on InChIKey, resulting in a unified dataset with no duplicate compound entries.
3. **Given** a compound with missing resistance data, **When** the merge occurs, **Then** the record is either excluded from the analysis set or flagged with a `NaN` resistance label, ensuring no silent data corruption occurs.

---

### User Story 2 - Dimensionality Reduction and Cluster Enrichment (Priority: P2)

The researcher applies UMAP to the descriptor matrix to visualize the chemical space and runs DBSCAN clustering to identify natural groups, then evaluates if specific clusters are significantly enriched for high-resistance compounds using Fisher's exact test with permutation validation.

**Why this priority**: This step transforms raw numerical data into interpretable spatial patterns. It allows the researcher to visually validate the hypothesis that physicochemical properties drive resistance clustering, while the permutation test ensures the enrichment is not a tautology of the clustering method.

**Independent Test**: The visualization module can be tested independently by generating a 2D UMAP plot file; the test verifies that points are colored by resistance label and that the system either identifies clusters with significant enrichment (p < 0.05) or correctly reports a 'no clusters found' diagnostic if the data does not support clustering.

**Acceptance Scenarios**:

1. **Given** the merged descriptor dataset, **When** UMAP (n_neighbors=15, min_dist=0.1) is applied, **Then** the resulting 2D embedding file is generated and visualized, showing a silhouette score ≥ 0.25 if distinct groups exist in the data.
2. **Given** the UMAP coordinates, **When** DBSCAN (eps=0.5, min_samples=10) is executed, **Then** the output either identifies distinct clusters and performs a Fisher's exact test (with a sufficient number of permutations) confirming enrichment (p < 0.05), OR logs a diagnostic message "No clusters found; skipping enrichment analysis" if all points are labeled as noise.
3. **Given** a cluster with low sample size (<10 compounds), **When** the enrichment test runs, **Then** the system flags the cluster as "insufficient power" and excludes it from the final enrichment ranking to avoid false positives.

---

### User Story 3 - Statistical Association and Effect Size Ranking (Priority: P3)

The researcher performs Mann-Whitney U tests for each descriptor against the binary resistance label, applies Benjamini-Hochberg FDR correction, and ranks descriptors by effect size (Cohen's d) and significance to generate the final hypothesis, while also performing a sensitivity analysis against a continuous model.

**Why this priority**: This provides the quantitative evidence required to answer the research question. It moves beyond visual patterns to specific, testable claims about which physicochemical properties are systematically associated with resistance, while validating the robustness of the binary split assumption.

**Independent Test**: The statistical module can be tested by running the analysis on a mock dataset with known effect sizes; the test verifies that the output correctly ranks descriptors by Cohen's d, applies Benjamini-Hochberg correction correctly, and produces a sensitivity analysis report comparing binary vs. continuous results.

**Acceptance Scenarios**:

1. **Given** the binary resistance labels and descriptor values, **When** the Mann-Whitney U test is run for a comprehensive set of descriptors, **Then** the output table includes raw p-values, FDR-adjusted p-values, and Cohen's d effect sizes for every descriptor, sorted by effect size magnitude.
2. **Given** the full set of descriptors, **When** the ranking occurs, **Then** the output table is correctly sorted by |Cohen's d| (descending) and FDR-adjusted p-value (ascending), regardless of whether any descriptors meet a significance threshold.
3. **Given** a descriptor with a negligible effect size (|d| < 0.2) but a significant p-value due to large sample size, **When** the ranking occurs, **Then** this descriptor is ranked lower than descriptors with larger effect sizes, ensuring the output prioritizes biological relevance over statistical noise.

### Edge Cases

- What happens when the NCBI FTP site is temporarily unavailable or the ChEMBL API rate-limits requests? (System must implement exponential backoff and log failures, then proceed with available data rather than crashing).
- How does the system handle compounds where the SMILES string is invalid or cannot be parsed by RDKit? (Such compounds are excluded from the descriptor calculation with a warning logged, ensuring the analysis proceeds on valid data only).
- What occurs if the UMAP embedding fails to converge or DBSCAN finds no clusters (all points labeled as noise)? (The system must output a diagnostic report indicating "no structure found" and skip the enrichment analysis for that run).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download antibiotic SMILES from ChEMBL (latest available release) and ZINC15, and resistance frequencies from NCBI Pathogen Detection, then merge them on InChIKey to produce a unified dataset (See US-1).
- **FR-002**: System MUST calculate a standardized set of molecular descriptors (including logP, TPSA, HBD, HBA, rotatable bonds) using RDKit for every valid compound in the dataset (See US-1).
- **FR-003**: System MUST apply UMAP (n_neighbors=15, min_dist=0.1) to the descriptor matrix and generate a 2D embedding plot colored by resistance phenotype (See US-2).
- **FR-004**: System MUST execute DBSCAN clustering on the UMAP coordinates with baseline parameters (eps=0.5, min_samples=10) and support parameter sweeps for sensitivity analysis, then perform Fisher's exact test to evaluate cluster enrichment for high-resistance compounds (See US-2).
- **FR-005**: System MUST perform Mann-Whitney U tests for each descriptor, apply Benjamini-Hochberg FDR correction (α=0.05), and rank results by effect size (Cohen's d) and adjusted p-value (See US-3).
- **FR-006**: System MUST operate entirely within a CPU-only environment (no GPU/CUDA), ensuring all computations (RDKit, UMAP, DBSCAN) complete within 6 hours on a GitHub Actions free-tier runner (2 vCPU, ~7 GB RAM) to ensure CI/CD feasibility and reproducibility (See US-1, US-2, US-3).
- **FR-007**: System MUST perform a permutation test (sufficient iterations) for cluster enrichment to validate that the observed enrichment is not a tautology of the UMAP/DBSCAN construction (See US-2).
- **FR-008**: System MUST perform a sensitivity analysis comparing the binary Mann-Whitney U test results against a continuous Spearman correlation model to validate the robustness of the binarization assumption (See US-3).
- **FR-009**: System MUST generate a distribution analysis (histogram + Hartigan's dip test) of resistance frequencies to assess bimodality before proceeding with the binary split (See US-3).

### Key Entities

- **AntibioticCompound**: Represents a single drug entity, identified by InChIKey, containing raw SMILES, resistance frequency, and a binary resistance label (High/Low).
- **MolecularDescriptorSet**: A vector of 200 numerical properties (e.g., logP, TPSA) calculated for a specific AntibioticCompound.
- **ClusterGroup**: A set of compounds grouped by DBSCAN in the UMAP space, characterized by its centroid and resistance enrichment statistics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The fraction of successfully merged compounds (InChIKey match between structure and phenotype data) is measured against the total number of requested compounds from ChEMBL/ZINC (See US-1).
- **SC-002**: The system outputs a complete table of p-values for all tested clusters, and the calculation matches a reference implementation (e.g., SciPy) within floating-point tolerance (See US-2).
- **SC-003**: The system correctly calculates Cohen's d for all descriptors and the ranking output matches a reference implementation within floating-point tolerance (See US-3).
- **SC-004**: The computational feasibility is measured against the constraint of completing the full analysis (data fetch + 200 descriptors + UMAP + clustering + stats) within 6 hours on a CPU-only runner (See US-1, US-2, US-3).
- **SC-005**: The reproducibility of the analysis is measured by the ability to re-run the pipeline on a fresh GitHub Actions environment and produce identical results (within floating-point tolerance) for the same input dataset (See US-1, US-3).

## Assumptions

- The NCBI Pathogen Detection dataset provides resistance frequencies at a level of granularity (per antibiotic) that allows for a binary classification (High vs. Low) based on the top/bottom quartiles, chosen as a data-driven proxy due to the heterogeneity of antibiotic classes in the dataset.
- The ChEMBL and ZINC15 datasets contain a sufficient number of unique, drug-like antibiotics (≥ 100) with valid SMILES strings to support meaningful UMAP embedding and statistical testing.
- The "High Resistance" and "Low Resistance" labels derived from the top/bottom quartiles are a valid proxy for the binary phenotypes required by the Mann-Whitney U test, provided the distribution analysis (FR-009) confirms sufficient bimodality; otherwise, the system defaults to the continuous Spearman model.
- The set of descriptors calculated by RDKit is sufficient to capture the relevant physicochemical variance; no additional 3D or quantum-chemical descriptors are required for this initial exploratory study.
- The analysis is observational; therefore, any identified associations are framed as correlational and do not imply causation between physicochemical properties and resistance mechanisms.
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) is sufficient to hold the dataset (≤ 10k compounds) and execute the UMAP/DBSCAN algorithms without memory overflow.