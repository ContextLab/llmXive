# Feature Specification: llmXive Follow-up: Interdisciplinary Bridging Coefficient Analysis

**Feature Branch**: `001-bridging-coefficient-analysis`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Does the density of cross-disciplinary connections (interdisciplinary bridging coefficient) in a scientific knowledge graph predict the future citation impact and novelty of research nodes?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Topological Metric Computation (Priority: P1)

The researcher downloads the PubGraph dataset, assigns primary disciplines to nodes via community detection on the graph structure, and computes the "bridging coefficient" for each node based on edge distribution across these structural clusters.

**Why this priority**: This is the foundational step; without the computed metric, no correlation analysis can occur. It directly addresses the core predictor variable of the research question.

**Independent Test**: Can be fully tested by running the ingestion pipeline on a [deferred]-node subset and verifying that every node has a valid `bridging_coefficient` value (0.0 to 1.0) and a `primary_cluster` label, with no memory errors on a standard CPU environment.

**Acceptance Scenarios**:

1. **Given** the PubGraph dataset is available, **When** the system extracts a [deferred]-node subgraph and runs the Louvain algorithm, **Then** every node in the subgraph is assigned a `primary_cluster` ID.
2. **Given** nodes are clustered, **When** the system calculates the bridging coefficient for a node, **Then** the value is strictly the ratio of edges connecting to different clusters divided by total degree, with no division-by-zero errors (nodes with degree 0 are flagged or excluded).
3. **Given** a node acts as a gatekeeper between two distinct clusters, **When** the coefficient is computed, **Then** the system correctly calculates the ratio of inter-cluster edges to total degree without error.

---

### User Story 2 - Outcome Variable Derivation (Citations and Novelty) (Priority: P2)

The system extracts historical citation counts from metadata and computes a novelty score for each node by measuring the cosine distance between its title embedding and the centroid of its **text-based topic cluster** (independent of graph topology), ensuring no circular validation.

**Why this priority**: These are the outcome variables required to test the hypothesis. Separating text-based novelty (derived from semantic similarity) from topology-based bridging (derived from graph structure) is critical for the study's validity and independence of variables.

**Independent Test**: Can be tested by processing a batch of [deferred] nodes, verifying that citation counts are non-negative integers, and that novelty scores are positive floats, with a check confirming that nodes with identical titles have zero novelty distance.

**Acceptance Scenarios**:

1. **Given** a node with a title and metadata, **When** the system retrieves citation counts, **Then** the value is a non-negative integer derived strictly from the graph metadata, not inferred.
2. **Given** a node's title, **When** the system generates an embedding using `sentence-transformers/all-MiniLM-L6-v2`, **Then** the embedding vector is correctly normalized and stored.
3. **Given** a cluster of nodes defined by text similarity, **When** the novelty score is calculated, **Then** it is the cosine distance between the node's embedding and the cluster centroid, ensuring the predictor (topology) and outcome (novelty) are mathematically independent.

---

### User Story 3 - Statistical Validation and Correlation Analysis (Priority: P3)

The system performs Spearman rank correlation and linear regression to test the relationship between the bridging coefficient (topology) and citation/novelty metrics (text/outcome), applying corrections for multiple comparisons.

**Why this priority**: This delivers the final scientific result, confirming or refuting the hypothesis. It includes necessary statistical rigor (multiplicity correction) to ensure the findings are methodologically sound.

**Independent Test**: Can be tested by running the analysis on the computed dataset, verifying that a p-value is returned for the correlation, and that a Bonferroni or FDR correction is applied to the significance threshold.

**Acceptance Scenarios**:

1. **Given** the predictor (bridging coefficient) and outcomes (citations, novelty), **When** the system runs Spearman correlation, **Then** a correlation coefficient (rho) and p-value are output for both relationships.
2. **Given** multiple hypothesis tests are performed, **When** the system applies multiple-comparison correction, **Then** the adjusted p-value threshold is strictly lower than the raw alpha (0.05) to control family-wise error.
3. **Given** a significant correlation is found, **When** the system generates the report, **Then** the findings are explicitly framed as "associational" rather than "causal" due to the observational nature of the data.

---

### Edge Cases

- What happens when a node has a degree of zero (isolated node)? The system must exclude it from the bridging coefficient calculation or assign a value of 0.0, preventing division by zero.
- How does the system handle nodes with titles that are missing or empty? The system must exclude these nodes from the novelty score calculation but retain them for citation analysis if metadata exists.
- How does the system handle clusters with only one node? The system must handle the centroid calculation for single-node clusters (distance = 0) without error.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the PubGraph dataset, extracting a representative subgraph of [deferred] nodes, serving the Data Acquisition goal (See US-1).
- **FR-002**: System MUST apply the Louvain community detection algorithm to assign a `primary_cluster` label to every node based on local connectivity, serving the Cluster Definition goal (See US-1).
- **FR-003**: System MUST calculate the `bridging_coefficient` for each node as the ratio of inter-cluster edges to total degree, serving the Metric Computation goal (See US-1).
- **FR-004**: System MUST compute a `novelty_score` for each node using cosine distance between title embeddings and the centroid of its **text-based topic cluster** (computed via k-means on embeddings only), serving the Outcome Retrieval goal (See US-2).
- **FR-005**: System MUST perform Spearman rank correlation and linear regression between the `bridging_coefficient` and `citation_count`/`novelty_score`, serving the Statistical Analysis goal (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to all hypothesis test p-values, serving the Methodological Soundness goal regarding multiplicity (See US-3).
- **FR-007**: System MUST explicitly label all reported correlations as "associational" in the final output, avoiding causal claims due to the lack of random assignment, serving the Inference Framing goal (See US-3).
- **FR-008**: System MUST perform k-means clustering (k=100) on title embeddings to assign a `topic_cluster` ID to every node, independent of graph topology, serving the Independence of Variables goal (See US-2).

### Key Entities

- **Node**: Represents a scientific publication; attributes include `id`, `title`, `citation_count`, `embedding_vector`, `primary_cluster`, `topic_cluster`.
- **Edge**: Represents a relationship between publications; attributes include `source_id`, `target_id`, `type`.
- **Primary Cluster**: A community of nodes identified by Louvain (topology); attributes include `cluster_id`, `node_count`.
- **Topic Cluster**: A community of nodes identified by k-means on embeddings (text); attributes include `cluster_id`, `centroid_embedding`, `node_count`.
- **Metric**: A derived value for a node; attributes include `bridging_coefficient`, `novelty_score`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (Spearman's rho) between the `bridging_coefficient` and `citation_count` is measured against the null hypothesis of zero correlation (See FR-005).
- **SC-002**: The statistical significance (p-value) of the correlation is measured against the corrected alpha threshold (e.g., 0.05 / number of tests) to account for multiplicity (See FR-006).
- **SC-003**: The pipeline runtime is ≤ 6 hours on the specified 2-CPU, 7GB RAM runner (See FR-001, Constitution Principle VI).
- **SC-004**: Peak memory usage is ≤ 7GB during graph processing (See FR-001, Constitution Principle VI).
- **SC-005**: The embedding computation completes within 50ms per node on a 2-core CPU (See FR-004).

## Assumptions

- The PubGraph dataset is publicly accessible via the provided arXiv link and can be downloaded within the CI runner's time limits.
- The `sentence-transformers/all-MiniLM-L6-v2` model can be loaded and executed entirely on CPU within the 6-hour limit for [deferred] nodes.
- The "primary cluster" assignment via Louvain is a valid proxy for "discipline" for the purpose of defining cross-disciplinary connections, as no explicit discipline metadata is guaranteed in the raw graph.
- Citation counts in the PubGraph metadata are up-to-date and accurate enough to serve as a proxy for "future citation impact" relative to the graph's publication date.
- The relationship between bridging coefficient and impact is linear or monotonic, justifying the use of Spearman correlation and linear regression.
- The [deferred]-node subgraph is representative of the broader scientific landscape regarding interdisciplinary dynamics.
- Text-based clustering (k-means on embeddings) provides a sufficiently distinct definition of "topic" to serve as an independent baseline for novelty calculation against topological clusters.