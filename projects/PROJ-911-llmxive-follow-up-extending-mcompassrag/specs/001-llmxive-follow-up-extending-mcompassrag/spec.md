# Feature Specification: GraphCompass: Topological Predictors of Semantic Coherence in CPU-Constrained RAG

**Feature Branch**: `001-graph-compass-topology`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending MCompassRAG: To what extent do topological features of lexical co-occurrence graphs predict semantic coherence compared to neural embeddings in CPU-constrained RAG?"

## User Scenarios & Testing

### User Story 1 - Graph Construction and Feature Extraction (Priority: P1)

**Journey**: A researcher needs to process a corpus of academic abstracts to extract deterministic topological features (modularity, centrality) from lexical co-occurrence graphs without relying on GPU resources.

**Why this priority**: This is the foundational capability. Without the ability to construct graphs and extract features on CPU, no comparison with neural baselines is possible. It directly addresses the "resource-constrained" motivation.

**Independent Test**: Can be fully tested by running the graph construction pipeline on a sample subset of the dataset (up to 360 documents) and verifying that numerical feature vectors are generated for every document within a fixed time budget, independent of any retrieval simulation.

**Acceptance Scenarios**:
1. **Given** a corpus of academic abstracts and a sliding window size of 10, **When** the system constructs lexical co-occurrence graphs, **Then** it must generate a graph object for each document where nodes are TF-IDF filtered terms and edges represent co-occurrence.
2. **Given** a constructed graph for a document, **When** the system calculates topological metrics, **Then** it must output a vector containing cluster modularity, average path length, and degree/betweenness centrality distributions for that document.
3. **Given** the CPU constraints (2 cores, no GPU) and a sample size of up to 360 documents, **When** the pipeline processes a document, **Then** the execution time must not exceed a predefined acceptable threshold per document to ensure the full sample is processed within the acceptable CI limit.

---

### User Story 2 - Neural Baseline Generation and Retrieval Simulation (Priority: P2)

**Journey**: A researcher needs to generate a comparative baseline using neural topic embeddings (BERTopic) and simulate retrieval performance for both graph-based and neural-based approaches against ground-truth queries.

**Why this priority**: This enables the core scientific comparison. It validates the hypothesis by providing the "control" (neural) against which the "treatment" (graph) is measured.

**Independent Test**: Can be tested by running the BERTopic baseline (CPU mode) and the retrieval simulation on a disjoint test set, verifying that Recall@k scores are generated for both methods.

**Acceptance Scenarios**:
1. **Given** the same corpus used for graph construction, **When** the system runs BERTopic in CPU-only mode, **Then** it must generate topic embeddings and cluster assignments without triggering CUDA/GPU errors.
2. **Given** a set of complex queries from the HotpotQA ground-truth query set, **When** the system simulates retrieval using both topological signatures (via graph similarity) and neural embeddings, **Then** it must output Recall@k scores where k represents a range of top-ranked positions for both methods.
3. **Given** the retrieval results, **When** the system performs statistical validation, **Then** it must execute a paired t-test comparing the precision metrics of the graph-based and neural-based approaches.

---

### User Story 3 - Correlation Analysis and Latency Benchmarking (Priority: P3)

**Journey**: A researcher needs to quantify the relationship between graph topology and retrieval precision, and measure the computational efficiency gain of the graph method over the neural method.

**Why this priority**: This delivers the final research output (the "extent" of prediction) and the practical validation (latency reduction) required to justify the method's adoption.

**Independent Test**: Can be tested by analyzing the output correlation coefficients and latency logs to confirm that the hypothesis is evaluated and that latency reduction is quantified.

**Acceptance Scenarios**:
1. **Given** the extracted topological features (aggregated per query) and the corresponding Recall@10 scores, **When** the system performs a Spearman rank correlation, **Then** it must output the correlation coefficient (r) and p-value for each topological metric.
2. **Given** the execution logs for both methods, **When** the system calculates wall-clock time, **Then** it must report the percentage reduction in metadata generation latency for the graph method compared to the neural method.
3. **Given** the correlation results, **When** the system evaluates the hypothesis, **Then** it must output the raw correlation coefficient and p-value, allowing the researcher to determine if the correlation exceeds a predefined threshold of practical significance..

### Edge Cases

- **What happens when** a document has extremely low term diversity (e.g., < 5 unique terms after filtering)? The system must handle this by assigning default zero values for centrality metrics or skipping the document with a logged warning, ensuring the pipeline does not crash.
- **How does the system handle** a dataset split where the ground-truth query set has no overlap with the training corpus? The system must strictly enforce that the test set is disjoint from the data used to construct graphs and train the neural baseline to prevent data leakage.
- **What happens when** BERTopic fails to converge on CPU due to memory pressure? The system must implement a fallback mechanism to reduce the corpus size or document window size dynamically, logging the adjustment.

## Requirements

### Functional Requirements

- **FR-001**: System MUST construct lexical co-occurrence graphs for each document using a sliding window of an appropriate number of terms, filtering nodes by TF-IDF scores, to ensure consistent graph topology generation (See US-1).
- **FR-002**: System MUST calculate cluster modularity, average path length, and node centrality distributions (degree, betweenness) for every constructed graph using CPU-optimized libraries (See US-1).
- **FR-003**: System MUST run BERTopic in CPU-only mode to generate neural topic embeddings and cluster assignments for the same corpus, ensuring no CUDA dependencies are invoked (See US-2).
- **FR-004**: System MUST simulate retrieval ranking for complex queries from the HotpotQA dataset based on both topological signatures (via graph similarity to query graphs) and neural embeddings, calculating Recall@5 and Recall@10 against human-annotated ground-truth answers (See US-2).
- **FR-005**: System MUST perform a Spearman rank correlation between topological features (aggregated per query) and retrieval precision scores per query (See US-3).
- **FR-006**: System MUST execute a paired t-test to compare the precision metrics and latency between the graph-based and neural-based approaches (See US-3).
- **FR-007**: System MUST enforce a memory limit and a time limit for the entire pipeline execution on the CI runner, ensuring the sample size N satisfies N * 60s <= 6h (See US-1).

### Key Entities

- **Lexical Graph**: A network structure where nodes represent filtered terms and edges represent co-occurrence within a sliding window.
- **Topological Signature**: A numerical vector containing modularity, path length, and centrality metrics derived from a Lexical Graph.
- **Neural Embedding**: A vector representation of document topics generated by BERTopic in CPU mode.
- **Retrieval Score**: A scalar value (Recall@k) representing the precision of a retrieval method against human-annotated ground-truth queries.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The Spearman rank correlation coefficient (r) between the average modularity of retrieved documents and Recall@k (per query) is measured to determine the extent of predictive power. (See US-3).
- **SC-002**: The latency of graph construction and feature extraction is measured against the latency of the BERTopic baseline to quantify the percentage reduction in metadata generation time (See US-3).
- **SC-003**: The retrieval precision (Recall@10) of the graph-based approach is measured against the neural baseline to determine if it achieves at least 70% of the neural performance (See US-2).
- **SC-004**: The computational resource usage (RAM and CPU time) is measured against the CI runner constraints (limited RAM, 2 cores, 6 hours) to confirm feasibility (See US-1).
- **SC-005**: The statistical significance (p-value) of the paired t-test comparing precision metrics is measured against a predetermined alpha level. to validate the performance difference (See US-2).

## Assumptions

- The HotpotQA dataset is available via HuggingFace and contains the necessary human-annotated ground-truth question-answer pairs for the retrieval simulation.
- BERTopic can successfully run in CPU-only mode on the specified CI runner without requiring 8-bit quantization or GPU acceleration.
- The lexical co-occurrence graph construction using a sliding window of 10 is a valid proxy for semantic coherence in the context of complex answer retrieval.
- The sample size (N ≤ 360) is sufficient to achieve statistical power for the correlation analysis; if not, the analysis will report the limitation rather than forcing a false positive.
- The "2-core CPU" environment of the GitHub Actions free tier is sufficient to process the dataset within the 6-hour window, provided the dataset is sampled if memory limits are approached.
- The correlation between topological features and retrieval precision is assumed to be monotonic, justifying the use of Spearman rank correlation.