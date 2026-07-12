# Feature Specification: llmXive Follow-up: Semantic Divergence Diagnostic for Agentic Reasoning

**Feature Branch**: `001-llmxive-semantic-gap-diagnostic`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Agent Explorative Policy Optimization for Multimodal Agentic Reasoning'"

## User Scenarios & Testing

### User Story 1 - Compute Semantic Divergence Metrics (Priority: P1)

**User Journey**: A researcher loads a static subset of multimodal reasoning problems (e.g., from MathVista/ScienceQA). The system extracts the "thinking" prefix from the agent's trace and generates a "tool-action distribution" using a deterministic, non-reasoning keyword retrieval system (BM25). It then computes the cosine similarity and mutual information between these two vectors to produce a "Semantic Divergence Score" for each problem instance.

**Why this priority**: This is the core scientific contribution. Without the ability to compute the divergence metric, the entire hypothesis regarding the "thinking-acting gap" cannot be tested. It establishes the independent variable for the study.

**Independent Test**: The system can be tested by processing a small, fixed set of problems and verifying that the output JSON contains a calculated divergence score for each, derived from the specific embeddings of the thinking prefix and the keyword-retrieved tool centroid, without requiring any RL training loops.

**Acceptance Scenarios**:

1. **Given** a dataset file containing 500 problems with "thinking" traces and ground-truth tools, **When** the system processes a single record using the DistilBERT encoder and BM25 retrieval, **Then** it outputs a JSON object containing `thinking_embedding`, `tool_centroid_embedding`, `cosine_similarity`, and `semantic_divergence_score`.
2. **Given** a problem where the thinking trace and the keyword-retrieved tools are semantically identical, **When** the system calculates the metric, **Then** the `cosine_similarity` is ≥ 0.95 and the `semantic_divergence_score` is ≤ 0.05.
3. **Given** a problem where the thinking trace is unrelated to the retrieved tools, **When** the system calculates the metric, **Then** the `cosine_similarity` is ≤ 0.30 and the `semantic_divergence_score` is ≥ 0.70.

---

### User Story 2 - Correlate Divergence with RL Failure Rates (Priority: P2)

**User Journey**: A researcher provides the computed divergence scores alongside the known failure rates (percentage of "all-wrong" rollouts) for each problem type from the original AXPO paper. The system performs a Pearson correlation test to determine if high semantic divergence predicts high RL failure rates.

**Why this priority**: This validates the hypothesis. It transforms the raw metric into a predictive diagnostic tool, directly addressing the research question of whether the gap predicts failure.

**Independent Test**: The system can be tested by feeding it a synthetic dataset where divergence scores are perfectly negatively correlated with success rates, verifying that the output correlation coefficient is ≤ -0.90.

**Acceptance Scenarios**:

1. **Given** a CSV of divergence scores and a corresponding CSV of RL failure rates for 500 problem instances, **When** the system runs the correlation analysis, **Then** it outputs a Pearson correlation coefficient and a p-value.
2. **Given** a dataset where divergence and failure rates are randomly generated (no relationship), **When** the system runs the analysis, **Then** the p-value is > 0.05, indicating no statistically significant correlation.
3. **Given** a dataset with a strong negative correlation, **When** the system runs the analysis, **Then** it flags the result as "Significant Negative Correlation" and reports the coefficient magnitude.

---

### User Story 3 - Generate Predictive Gap Risk Classification (Priority: P3)

**User Journey**: A researcher uses the divergence scores to categorize problems into "High-Divergence" (high risk) and "Low-Divergence" (low risk) clusters using K-Means. They then train a simple logistic regression classifier to predict the binary success/failure outcome of RL attempts based on these metrics.

**Why this priority**: This operationalizes the diagnostic. It moves from correlation to prediction, enabling the "proactive problem characterization" mentioned in the motivation.

**Independent Test**: The system can be tested by running the K-Means clustering on a subset of data and verifying that the resulting clusters are distinct (silhouette score > 0.25) and that the logistic regression model achieves an accuracy > 60% on a held-out test set.

**Acceptance Scenarios**:

1. **Given** the computed divergence scores, **When** the system applies K-Means clustering with k=2, **Then** it outputs two distinct clusters labeled "High-Divergence" and "Low-Divergence" with a silhouette score ≥ 0.25.
2. **Given** the clustered data and the binary RL outcome labels, **When** the system trains a logistic regression classifier, **Then** it outputs the model's accuracy, precision, and recall on a [deferred] hold-out test set.
3. **Given** a new problem instance with a calculated divergence score, **When** the system applies the trained classifier, **Then** it returns a predicted binary outcome (Success/Failure) with an associated probability score.

---

### Edge Cases

- What happens if the BM25 retrieval returns zero results for a specific problem's tool description? (System should assign a null tool centroid and flag the record for exclusion or imputation).
- How does the system handle problems where the "thinking" prefix is missing or empty in the dataset? (System should skip the embedding calculation for that field and report a specific error code).
- What occurs if the dataset size is too small to compute a valid Pearson correlation (e.g., < 30 samples)? (System should raise a "Statistical Power Insufficient" warning and halt the correlation step).
- How are ties handled in the K-Means clustering when points are equidistant to centroids? (Standard K-Means tie-breaking rules apply, but the system must log the number of such instances).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a static subset of multimodal reasoning problems (max 500 records) from a specified HuggingFace dataset or local JSON file, extracting the "thinking" prefix and ground-truth tool identifiers. (See US-1)
- **FR-002**: System MUST generate a tool-action distribution for each problem using a deterministic BM retrieval system against a pre-indexed tool documentation corpus, returning the top 10-20 plausible tools. (See US-1)
- **FR-003**: System MUST compute vector embeddings for the "thinking" prefix and the centroid of the retrieved tool distribution using a CPU-optimized encoder (e.g., DistilBERT) without GPU acceleration. (See US-1)
- **FR-004**: System MUST calculate the cosine similarity and mutual information estimates between the thinking and tool embeddings to derive a "Semantic Divergence Score" for every record. (See US-1)
- **FR-005**: System MUST perform a Pearson correlation test between the calculated divergence scores and the external RL failure rates provided in the input data. (See US-2)
- **FR-006**: System MUST apply K-Means clustering (k=2) to the divergence scores to categorize problems into "High-Divergence" and "Low-Divergence" groups. (See US-3)
- **FR-007**: System MUST train a logistic regression classifier using the semantic metrics to predict the binary success/failure outcome of RL attempts and report accuracy on a hold-out set. (See US-3)
- **FR-008**: System MUST enforce a memory limit of ≤ 7 GB RAM and a CPU-only execution environment, automatically sampling data if the full dataset exceeds these constraints. (See Assumptions)

### Key Entities

- **ProblemInstance**: Represents a single multimodal reasoning task; attributes include `problem_id`, `thinking_prefix` (string), `ground_truth_tools` (list), `divergence_score` (float), `rl_failure_rate` (float).
- **ToolDistribution**: Represents the set of tools retrieved by the non-reasoning system; attributes include `retrieved_tool_ids` (list), `centroid_embedding` (vector), `bm25_scores` (list).
- **DivergenceMetric**: Represents the calculated relationship between thought and action; attributes include `cosine_similarity` (float), `mutual_information` (float), `semantic_divergence_score` (float).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Pearson correlation coefficient between semantic divergence and RL failure rates is measured against the null hypothesis of zero correlation to determine statistical significance (p < 0.05). (See US-2)
- **SC-002**: The predictive accuracy of the logistic regression classifier is measured against the held-out test set ([deferred] of data) to validate the "Gap Risk Score" utility. (See US-3)
- **SC-003**: The silhouette score of the K-Means clustering is measured against the threshold of 0.25 to ensure the "High" and "Low" divergence groups are distinct and meaningful. (See US-3)
- **SC-004**: The total execution time of the analysis pipeline is measured against the time limit of the free-tier GitHub Actions runner to ensure compute feasibility. (See Assumptions)
- **SC-005**: The memory usage of the embedding and correlation steps is measured against a predefined RAM limit to confirm the method fits the CPU-only constraint. (See Assumptions)

## Assumptions

- The HuggingFace Datasets library can successfully download and cache the MathVista/ScienceQA subset within the disk limit of the free-tier runner.
- The "thinking" prefixes in the dataset are valid text strings and do not require complex preprocessing to extract; if missing, the record is skipped.
- The BM25 retrieval corpus (tool documentation) is pre-indexed or can be built in < 5 minutes on a CPU without exceeding memory limits.
- The "failure rates" for the original RL attempts are available as a static lookup table or CSV provided by the user, as the project does not re-run the expensive RL training.
- The DistilBERT encoder (or equivalent) runs entirely on CPU in default precision and completes the embedding of 500 records within the 6-hour job limit.
- The dataset size is sufficient to perform a statistically valid Pearson correlation and K-Means clustering without requiring power analysis adjustments.
- The "thinking-acting gap" phenomenon is observable in the provided static dataset; if the data lacks the necessary variance in RL outcomes, the correlation analysis may yield null results.
