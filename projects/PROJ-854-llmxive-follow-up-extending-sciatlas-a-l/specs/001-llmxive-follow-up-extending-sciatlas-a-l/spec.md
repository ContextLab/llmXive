# Specification: Interdisciplinary Bridging Coefficient Analysis

## Overview
This project analyzes the relationship between topological bridging in scientific collaboration networks and research outcomes (citations, novelty). The data source is an **OpenAlex-derived Subgraph** of scientific works, replacing the previously assumed PubGraph dataset.

## Functional Requirements

### FR-001: Data Ingestion
The system MUST ingest data from an **OpenAlex-derived Subgraph**. The data must include:
- `id`: Unique work identifier
- `title`: Work title
- `cited_by_count`: Citation count
- `publication_date`: Date of publication

### FR-002: Clustering
The system MUST assign `primary_cluster` IDs using Louvain community detection on the graph topology.

### FR-003: Bridging Coefficient
The system MUST calculate `bridging_coefficient` for each node as: (inter-cluster edges) / (total degree).
- **Edge Case**: Nodes with degree 0 MUST be assigned `bridging_coefficient = 0.0`.

### FR-004: Embeddings
The system MUST generate title embeddings using `sentence-transformers/all-MiniLM-L6-v2`.

### FR-005: Novelty Score
The system MUST compute `novelty_score` as the cosine distance between a node's embedding and its own `topic_cluster` centroid.
- **Edge Case**: Singleton clusters MUST be assigned `novelty_score = 0.0`.

### FR-006: Statistical Analysis
The system MUST perform Spearman correlation and Linear Regression with covariates.
- Multiple-comparison correction MUST be configurable (Bonferroni or Benjamini-Hochberg).

### FR-007: Reporting
The final report MUST explicitly label results as "associational" and NOT "causal".

## Assumptions
1. The **OpenAlex** API is accessible and returns consistent data structures.
2. The graph fits in memory when sampled (target size < 100k nodes).
3. CPU-only execution is sufficient for embedding generation and clustering.

## Edge Cases
1. **Isolated Nodes**: Assigned bridging coefficient of 0.0.
2. **Singleton Clusters**: Assigned novelty score of 0.0.
3. **Null Titles**: Excluded from embedding generation; logged to `excluded_nodes.json`.
4. **Missing Data**: If a node lacks a `cited_by_count`, it defaults to 0.

## User Scenarios
- **US1**: A researcher wants to ingest a subgraph from **OpenAlex**, compute topological metrics, and verify data integrity.
- **US2**: A researcher wants to compute novelty scores based on text embeddings independent of graph topology.
- **US3**: A researcher wants to analyze the correlation between bridging and citations, controlling for confounds.

## Non-Functional Requirements
- **Memory**: Peak RAM usage must not exceed a predefined memory threshold to ensure resource efficiency..
- **Reproducibility**: All random seeds must be pinned (default).
- **Performance**: Embedding generation latency must be < 50ms per node.
