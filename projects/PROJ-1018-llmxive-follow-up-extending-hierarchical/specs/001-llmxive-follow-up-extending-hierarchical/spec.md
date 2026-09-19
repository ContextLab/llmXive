# Feature Specification: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

**Feature Branch**: `001-llmxive-static-distillation`  
**Created**: 2026-09-19  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode'"

## User Scenarios & Testing

### User Story 1 - Dynamic Baseline Extraction (Priority: P1)

The researcher MUST be able to execute the dynamic HiLS model on the PG-19 or arXiv long-context validation set to extract the retrieval score matrices for every chunk, aggregating these into a "canonical relevance profile" for each chunk. This step establishes the ground truth against which the static approximation is measured.

**Why this priority**: Without a verified dynamic baseline and its corresponding relevance profiles, the static index cannot be constructed, and no comparison is possible. This is the foundational data acquisition step.

**Independent Test**: Can be fully tested by running the extraction script on a sample of 10 documents and verifying that the output JSON contains non-empty retrieval score matrices for every chunk ID, with dimensions matching the model's expected configuration (e.g., $N_{chunks} \times N_{tokens}$).

**Acceptance Scenarios**:

1. **Given** a pre-trained HiLS checkpoint and the PG-19 validation set, **When** the extraction script is executed with the `--mode dynamic` flag, **Then** the script outputs a JSON file containing aggregated relevance profiles for every document chunk with a success status.
2. **Given** the extraction script output, **When** the profile dimensions are inspected, **Then** the number of chunks per document matches the expected token count divided by the chunk size, and no retrieval scores are null or NaN.

---

### User Story 2 - Static Index Construction (Priority: P2)

The system MUST apply CPU-optimized K-Means clustering to the aggregated relevance profiles to group chunks into $K$ canonical landmarks, generating a static lookup table (cluster centroids and chunk-to-cluster mappings) that bypasses dynamic retrieval during inference.

**Why this priority**: This implements the core hypothesis (static distillation). It transforms the dynamic data from US-1 into the static structure required for the efficiency claim.

**Independent Test**: Can be tested by running the clustering algorithm on the extracted profiles and verifying that the resulting lookup table maps every unique chunk ID to exactly one cluster centroid, with the number of clusters matching the user-specified $K$.

**Acceptance Scenarios**:

1. **Given** the aggregated relevance profiles from US-1, **When** the clustering script is executed with $K=100$ (or a specified default), **Then** the output static index file contains a mapping of chunk IDs to cluster IDs and a list of $K$ centroid vectors.
2. **Given** the static index, **When** a random chunk ID is queried against an index built from a 100k token document on a standard CPU (Intel Xeon or equivalent, 2 cores), **Then** the system returns a valid cluster assignment within 50ms.

---

### User Story 3 - Comparative Evaluation & Statistical Significance (Priority: P3)

The system MUST execute the modified "Static-HiLS" inference (using the static index) on a held-out test set, compute perplexity and downstream QA accuracy, and perform a paired t-test against the dynamic baseline to determine if the performance difference is statistically significant ($p < 0.05$).

**Why this priority**: This delivers the final research answer (the "extent" of reliance on dynamic vs. static priors) and validates the edge deployment claim.

**Independent Test**: Can be tested by running the evaluation suite on a small subset (e.g., 5 documents) and verifying that the output includes perplexity scores for both models, a calculated p-value, and a latency comparison.

**Acceptance Scenarios**:

1. **Given** the static index and the dynamic model, **When** both are run on the same held-out test documents (average of 5 runs on a 32k token document), **Then** the system outputs a report containing the perplexity for both, the QA accuracy for both, and the latency reduction factor.
2. **Given** the paired perplexity scores across documents, **When** the statistical test is run, **Then** the system reports a p-value and a conclusion (e.g., "Significant" or "Not Significant") based on the $p < 0.05$ threshold.

### Edge Cases

- What happens when the validation set contains documents shorter than the minimum chunking threshold (e.g., < 2048 tokens)? The system must skip these or pad them to the minimum length, logging the action.
- How does the system handle K-Means convergence failure (e.g., empty clusters)? The system must retry with a different random seed up to 3 times, then fail with an explicit error if convergence is not achieved.
- What if the pre-trained HiLS checkpoint is incompatible with the local environment (e.g., PyTorch version mismatch)? The system must detect this during initialization and halt with a clear error message rather than producing corrupted scores.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST extract retrieval score matrices from the dynamic HiLS model for every chunk in the validation set and aggregate them into canonical relevance profiles (See US-1).
- **FR-002**: The system MUST construct a static lookup table by applying K-Means clustering to the relevance profiles, mapping chunk IDs to cluster centroids (See US-2).
- **FR-003**: The system MUST modify the HiLS inference pipeline to bypass dynamic retrieval and use the static lookup table for attention sparsity patterns (See US-3).
- **FR-004**: The system MUST compute perplexity and downstream QA accuracy on a held-out test set for both the dynamic baseline and the static variant (See US-3).
- **FR-005**: The system MUST perform a paired t-test on the perplexity scores across documents to determine statistical significance ($p < 0.05$) (See US-3).
- **FR-006**: The system MUST measure and report the inference latency reduction factor (dynamic vs. static) on a standard CPU (2 cores) using a fixed protocol: 32k token input context, 10 runs, and 2 warm-up iterations (See US-3).
- **FR-007**: The system MUST evaluate the static index on a downstream long-context QA task (e.g., HotpotQA subset) to provide an independent measure of relevance distinct from the internal retrieval scores (See US-3).
- **FR-008**: The system MUST perform a sensitivity analysis by sweeping the cluster count $K$ over the set $\{50, 100, 200\}$ and report the resulting perplexity and QA accuracy trade-offs (See US-3).

### Key Entities

- **RelevanceProfile**: An aggregated vector representing the average retrieval scores for a specific document chunk across the validation set.
- **StaticIndex**: A data structure containing $K$ cluster centroids and a mapping from chunk IDs to cluster IDs, used for static attention patterns.
- **EvaluationReport**: A structured output containing perplexity, QA accuracy, p-value, and latency metrics for both dynamic and static models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in perplexity between the static and dynamic models is measured against the dynamic baseline to determine the performance degradation (See US-3).
- **SC-002**: The inference latency of the static model is measured against the dynamic baseline to quantify the reduction factor (See US-3).
- **SC-003**: The statistical significance of the perplexity difference is measured against the $p < 0.05$ threshold using a paired t-test (See US-3).
- **SC-004**: The accuracy on the downstream long-context QA task is measured against the dynamic baseline to assess semantic coherence preservation (See US-3).
- **SC-005**: The memory footprint of the static index is measured against the dynamic retrieval module's runtime memory usage using `tracemalloc` to isolate the retrieval module specifically (See US-3).
- **SC-006**: The QA accuracy degradation of the static model is measured against the dynamic baseline across the sensitivity sweep of $K \in \{50, 100, 200\}$ (See US-3).

## Assumptions

- **Dataset Variable Fit**: The analysis targets the `PG-19` dataset (HuggingFace `lmsys/pg-19-test`), which contains full-length books with document lengths typically exceeding 32k tokens (median ~50k, max >100k). If a specific subset or alternative `arXiv` split is used that fails this threshold, the system will filter documents to retain only those with token counts ≥ 32,000, logging the exclusion count. This ensures the ultra-long-context hypothesis is tested on valid data.
- **Inference Framing**: The comparison is observational (no random assignment of documents to models); findings regarding the "necessity" of dynamic retrieval will be framed as associational evidence regarding performance degradation, not causal proof of mechanism necessity.
- **Compute Feasibility**: The entire analysis (extraction, clustering, inference, evaluation) will run on a GitHub Actions free-tier runner (limited CPU cores, constrained RAM and disk, no GPU) by using CPU-optimized K-Means (scikit-learn) and sampling the dataset if necessary to fit memory constraints.
- **Threshold Justification**: The number of clusters $K$ will be set to 100 (a community-standard default for landmark-based indexing) unless the idea specifies otherwise. A sensitivity analysis will sweep $K \in \{, \text{low}, \text{high}\}$ to report how the perplexity degradation varies across these values.
- **Measurement Validity**: The perplexity and QA accuracy metrics are derived from standard, validated evaluation protocols for language models (e.g., L-Eval or HotpotQA subsets) and are mathematically independent of the clustering centroids used to construct the static index.
- **Predictor Collinearity**: Since the static index is derived directly from the dynamic model's scores, the two predictors (dynamic scores vs. static cluster assignment) are definitionally related. This study does not claim to prove the "necessity" of dynamic retrieval in an absolute sense, but rather measures the **distillation fidelity** and **cost-benefit trade-off**. The research question is revised to: "How much dynamic retrieval signal can be compressed into a static index without significant downstream performance loss?"
- **Model Availability**: The pre-trained HiLS checkpoint is available via the original repository or HuggingFace and is compatible with the specified CPU-only environment without requiring CUDA or 8-bit quantization libraries.