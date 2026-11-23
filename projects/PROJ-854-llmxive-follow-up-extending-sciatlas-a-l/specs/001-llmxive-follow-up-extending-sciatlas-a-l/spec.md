# Specification: Interdisciplinary Bridging Coefficient Analysis

## Overview
This project analyzes the relationship between topological bridging in scientific collaboration networks and research outcomes (citations, novelty). The data source is an **OpenAlex-derived Subgraph** of scientific works. OpenAlex is used as the primary source to replace PubGraph due to API accessibility and data freshness requirements, maintaining the subgraph extraction methodology.

## Functional Requirements

### FR-001: Data Ingestion (See US-001)
The system MUST ingest data from an **OpenAlex-derived Subgraph** stored in `data/processed/subgraph.parquet`. The data must include:
- `id`: Unique work identifier
- `title`: Work title
- `cited_by_count`: Citation count
- `publication_date`: Date of publication
- `field`: Disciplinary field identifier

The system MUST validate the ingested data against the schema defined in `data/schema/openalex_works.json` and reject any records failing validation.

### FR-002: Clustering
The system MUST assign `primary_cluster` IDs using Louvain community detection on the graph topology.

### FR-003: Bridging Coefficient
The system MUST calculate `bridging_coefficient` for each node as: (inter-cluster edges) / (total degree).
- **Edge Case**: Nodes with degree 0 MUST be assigned `bridging_coefficient = 0.0`.
- **Edge Case**: Purely Intra-Cluster Nodes (degree > 0, 0 inter-cluster edges) MUST be assigned `bridging_coefficient = 0.0`.

### FR-004: Embeddings (See US-002)
The system MUST generate title embeddings using `sentence-transformers/all-MiniLM-L6-v2` (v2).

### FR-005: Novelty Score (See US-002)
The system MUST compute `novelty_score` as the cosine distance between a node's embedding and the **GLOBAL centroid** of all work embeddings in the dataset.
- **Edge Case**: Singleton clusters MUST be calculated naturally (distance to global centroid), allowing for non-zero novelty scores. No artificial suppression of the signal is permitted.

### FR-006: Statistical Analysis (See US-003)
The system MUST perform Spearman correlation and Linear Regression with covariates.
- **Mandatory Covariates**: The regression model MUST include `publication_date` and `field` to control for confounding.
- **Multiple-comparison correction**: MUST be configurable (Bonferroni or Benjamini-Hochberg), defaulting to Benjamini-Hochberg. Configuration is exposed via the `--correction-method` CLI flag.

### FR-007: Reporting
The final report MUST explicitly label results as "associational" and NOT "causal".

### FR-008: Validation Independence (See US-002)
The system MUST ensure novelty scores are derived strictly from text embeddings and global statistics, with no dependency on graph topology or cluster assignments. This prevents circular validation between the bridging metric and the novelty metric.

## Assumptions
1. The **OpenAlex** API is accessible and returns consistent data structures.
2. The graph fits in memory when sampled (target size < 100k nodes).
3. CPU-only execution is sufficient for embedding generation and clustering, constrained to **2-CPU** cores and **7GB RAM** with a **6-hour** maximum runtime.
4. The `sentence-transformers/all-MiniLM-L6-v2` model is available locally or via the specified API.

## Edge Cases
1. **Isolated Nodes**: Assigned bridging coefficient of 0.0.
2. **Purely Intra-Cluster Nodes**: Assigned bridging coefficient of 0.0.
3. **Null Titles**: Excluded from embedding generation; logged to `excluded_nodes.json`.
4. **Missing Data**: If a node lacks a `cited_by_count`, it defaults to 0.
5. **Singleton Clusters**: Novelty score is calculated naturally against the global centroid (no artificial 0.0 assignment).

## User Scenarios

### US-001: Data Ingestion and Integrity Verification (Priority: P1)
A researcher wants to ingest a subgraph from **OpenAlex**, compute topological metrics, and verify data integrity.

**Why this priority**: Data integrity is the foundation of all subsequent analysis; without verified data, results are invalid.
**Independent Test**: Can be fully tested by running the ingestion pipeline on a known-good sample and verifying the schema validation report.

**Acceptance Scenarios**:
1. **Given** a valid OpenAlex subgraph file, **When** the ingestion pipeline runs, **Then** the system validates the schema and proceeds.
2. **Given** a malformed subgraph file, **When** the ingestion pipeline runs, **Then** the system rejects the file and logs the specific schema violations.

### US-002: Topology-Independent Novelty Computation (Priority: P2)
A researcher wants to compute novelty scores based on text embeddings independent of graph topology.

**Why this priority**: Ensures the novelty metric is not circularly dependent on the clustering used for bridging, preserving scientific validity.
**Independent Test**: Can be tested by computing novelty on a dataset where cluster assignments are shuffled; the novelty scores must remain unchanged.

**Acceptance Scenarios**:
1. **Given** a set of work embeddings, **When** the novelty score is computed, **Then** the score is based solely on the distance to the global centroid.
2. **Given** a node assigned to a singleton cluster, **When** the novelty score is computed, **Then** the score reflects its distance to the global centroid (not 0.0).

### US-003: Confounding-Controlled Correlation Analysis (Priority: P3)
A researcher wants to analyze the correlation between bridging and citations, controlling for confounds.

**Why this priority**: Essential for distinguishing true bridging effects from spurious correlations caused by publication age or field-specific citation rates.
**Independent Test**: Can be tested by verifying the regression model includes `publication_date` and `field` covariates.

**Acceptance Scenarios**:
1. **Given** the computed bridging and citation data, **When** the regression model runs, **Then** it includes `publication_date` and `field` as covariates.
2. **Given** the regression output, **When** the results are reported, **Then** they are labeled as "associational".

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Schema validation error rate is measured against [deferred] (zero tolerated errors) for US-001.
- **SC-002**: Novelty score variance is measured against the global centroid distribution to confirm independence from cluster topology for US-002.
- **SC-003**: Regression model R-squared improvement is measured against a baseline model without covariates for US-003.
- **SC-004**: Runtime performance is measured against the 6-hour limit on 2-CPU, 7GB RAM hardware.

## Non-Functional Requirements
- **Memory**: Peak RAM usage must not exceed 7GB to ensure resource efficiency.
- **Reproducibility**: All random seeds must be pinned (default).
- **Performance**: Embedding generation latency must be < 50ms per node.