# Feature Specification: llmXive follow-up: extending "Heterogeneous Scientific Foundation Model Collaboration"

**Feature Branch**: `001-llmxive-cache-optimization`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "How does the introduction of a semantic similarity-based caching mechanism affect the computational efficiency and scientific reasoning accuracy of the EywaOrchestra framework when processing iterative, multi-turn hypothesis-testing tasks?"

## User Scenarios & Testing

### User Story 1 - Semantic Cache Implementation and Hit-Rate Measurement (Priority: P1)

The system must implement a lightweight semantic caching layer that intercepts prompt queries, computes embeddings using a CPU-tractable model, and retrieves cached outputs when cosine similarity exceeds a defined threshold.

**Why this priority**: This is the core innovation. Without the cache mechanism itself, no efficiency gains can be measured. It establishes the baseline functionality required to test the research hypothesis.

**Independent Test**: Can be fully tested by running a batch of synthetic iterative queries (BenchmarkQuery entities) against the cache module in isolation. The test verifies that the cache correctly identifies hits based on the cosine similarity threshold and records the hit-rate.

**Acceptance Scenarios**:

1. **Given** a set of 500 iterative sub-task queries (BenchmarkQuery entities) with varying input parameters, **When** the Semantic Cache module processes them with a threshold of 0.95, **Then** the system must record the total number of requests served from the cache and calculate the hit-rate percentage relative to the total requests.
2. **Given** a query with a semantic similarity score of 0.96 to a cached entry, **When** the system processes the query, **Then** the system must return the cached result and log the event as a "Cache Hit" without triggering a new model inference.
3. **Given** a query with a semantic similarity score of 0.90 to any cached entry, **When** the system processes the query, **Then** the system must bypass the cache, invoke the standard EywaOrchestra pipeline, and log the event as a "Cache Miss".

---

### User Story 2 - Efficiency and Accuracy Trade-off Quantification (Priority: P2)

The system must execute the EywaOrchestra pipeline on a benchmark dataset twice (with and without caching) and quantitatively compare the reduction in model invocations and runtime against the degradation in scientific reasoning accuracy.

**Why this priority**: This directly addresses the research question. It transforms the cache mechanism into empirical data, validating whether the efficiency gains come at an unacceptable cost to accuracy.

**Independent Test**: Can be fully tested by running the paired execution pipeline on the "Eywa" benchmark subset (BenchmarkQuery entities) and generating a report containing the exact percentage reduction in runtime, the exact percentage deviation in accuracy, and the results of the statistical significance tests (McNemar's test for accuracy, t-test for runtime).

**Acceptance Scenarios**:

1. **Given** the "Eywa" benchmark subset of 500 iterative tasks (BenchmarkQuery entities), **When** the system runs the pipeline with the Semantic Cache enabled, **Then** the system must record the total wall-clock time and calculate the percentage reduction relative to the baseline (non-cached) execution time.
2. **Given** the same benchmark subset, **When** the system compares the cached results against the independent ground-truth scientific outcomes, **Then** the system must calculate and report the percentage deviation in scientific reasoning accuracy relative to the baseline.
3. **Given** a statistical test configuration, **When** the system analyzes the data, **Then** it must output a p-value for runtime differences using a paired t-test and a p-value for accuracy differences using McNemar's test for paired proportions (significance level α = 0.05).

---

### User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

The system must perform a sensitivity analysis by sweeping the cosine similarity threshold across a defined range and visualize the resulting trade-off curve between cache hit-rate, runtime reduction, and accuracy degradation.

**Why this priority**: This provides the methodological robustness required to justify the chosen threshold. It ensures the results are not an artifact of a single arbitrary parameter choice and allows future users to tune the system for their specific constraints.

**Independent Test**: Can be fully tested by running the pipeline with thresholds set to {0.90, 0.95, 0.99} and verifying that the generated visualization correctly plots the three metrics (hit-rate, runtime, accuracy) against the threshold values, and that the optimal threshold is identified based on the defined optimization rule.

**Acceptance Scenarios**:

1. **Given** a set of thresholds {0.90, 0.95, 0.99}, **When** the system executes the sensitivity analysis, **Then** it must generate a CSV or JSON report detailing the hit-rate, runtime reduction, and accuracy deviation for each threshold.
2. **Given** the sensitivity analysis data, **When** the system generates the trade-off curve plot, **Then** the plot must clearly show the inflection point where accuracy degradation begins to exceed the measured margin as the threshold decreases.
3. **Given** the analysis results, **When** a user reviews the output, **Then** they must be able to identify the optimal threshold that maximizes runtime reduction while keeping accuracy deviation within a user-defined tolerance or the measured deviation reported in the analysis.

---

### Edge Cases

- What happens when the embedding model fails to compute a similarity score due to an input format error? (System must log the error, treat it as a cache miss, and proceed with standard inference).
- How does the system handle a scenario where the cache memory limit (e.g., 1GB) is exceeded during the 500-query run? (System must implement an LRU eviction policy or stop caching new entries, logging the event).
- What happens if the benchmark dataset contains ambiguous ground-truth outcomes where multiple scientific answers are valid? (System must use a fuzzy matching or tolerance-based comparison for accuracy evaluation, documented in the sensitivity analysis).

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a semantic caching module that computes cosine similarity between incoming prompt embeddings and cached entries using a CPU-tractable model (e.g., `all-MiniLM-L6-v2`) to ensure compatibility with free-tier CI environments. The module must process BenchmarkQuery entities. (See US-1)
- **FR-002**: System MUST execute the EywaOrchestra pipeline on the benchmark dataset (BenchmarkQuery entities) in two distinct modes: (a) standard execution without caching, and (b) execution with the semantic cache enabled, logging all metrics for comparison. (See US-2)
- **FR-003**: System MUST perform a sensitivity analysis by automatically running the pipeline with similarity thresholds set to a discrete set of values (e.g., a range of high-confidence thresholds) to validate the robustness of the efficiency-accuracy trade-off. (See US-3)
- **FR-004**: System MUST calculate and report the percentage reduction in specialized model invocations and total wall-clock time relative to the baseline, and the percentage deviation in scientific reasoning accuracy against ground-truth outcomes. (See US-2)
- **FR-005**: System MUST generate a visualization (e.g., line plot) depicting the trade-off curve between cache hit-rate, runtime reduction, and accuracy degradation across the tested similarity thresholds. (See US-3)
- **FR-006**: System MUST perform a paired t-test on the runtime metrics and McNemar's test on the accuracy metrics (binary success/failure outcomes) from the cached and non-cached runs to determine statistical significance (p < 0.05). (See US-2)
- **FR-007**: If the "Eywa" benchmark lacks independent ground-truth numerical outcomes, the system MUST implement a deterministic synthetic ground-truth generator that produces numerical outcomes based on documented analytical solutions or established physical constants known to be independent of the EywaOrchestra pipeline's training corpus. The generation logic MUST be epistemologically independent of the EywaOrchestra pipeline's heuristics. If the specific analytical solution used is known to be part of the model's training data (e.g., via a lookup table of known training examples), the system MUST flag the inability to perform a valid scientific accuracy test. (See US-2)
- **FR-008**: System MUST validate that the ground-truth source (whether external or synthetic) is independent of the EywaOrchestra pipeline's inference logic before calculating accuracy metrics. (See US-2)

### Key Entities

- **BenchmarkQuery**: Represents a single iterative sub-task from the "Eywa" dataset, containing the input prompt, expected ground-truth outcome, and metadata for the specific scientific domain. Used in US-1, US-2, FR-001, FR-002.
- **CacheEntry**: Represents a stored result in the semantic cache, containing the prompt embedding, the original output, and the timestamp of insertion.
- **ExecutionRun**: Represents a single execution of the pipeline (either cached or baseline), containing aggregated metrics for runtime, invocation count, and accuracy.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in specialized model invocations is measured against the baseline count from the non-cached execution run. (See FR-004, US-2)
- **SC-002**: The total wall-clock runtime reduction is measured against the baseline runtime from the non-cached execution run. (See FR-004, US-2)
- **SC-003**: The scientific reasoning accuracy deviation is measured against the independent ground-truth outcomes provided in the "Eywa" benchmark dataset or the validated synthetic generator. (See FR-004, FR-007, US-2)
- **SC-004**: The statistical significance of the performance differences is measured against the standard threshold of p < 0.05 via paired t-test (runtime) and McNemar's test (accuracy). (See FR-006, US-2)
- **SC-005**: The sensitivity of the system to threshold changes is measured by the variation in accuracy deviation and hit-rate across the discrete set of tested thresholds {0.90, 0.95, 0.99}. (See FR-005, US-3)

## Assumptions

- **Assumption about data availability**: The "Eywa" benchmark subset containing iterative tasks (e.g., multi-step chemical reaction prediction, climate variable correlation) is accessible via the official repository or supplementary materials associated with the relevant arXiv paper and fits within the 7GB RAM / 14GB disk constraints of the GitHub Actions free runner.
- **Assumption about compute environment**: The analysis will be executed on a GitHub Actions free-tier runner (limited CPU cores, constrained RAM, no GPU), requiring all models (including the embedding model and Eywa components) to run in default precision on CPU without CUDA dependencies.
- **Assumption about threshold justification**: The initial similarity threshold of 0.95 is selected based on community standards for semantic similarity in retrieval tasks, and the sensitivity analysis (FR-003) will empirically validate or adjust this value.
- **Assumption about independence**: The ground-truth scientific outcomes in the benchmark are independent of the prompt embeddings and the cache mechanism, ensuring that accuracy evaluation is not circular.
- **Assumption about dataset-variable fit**: The "Eywa" benchmark contains all necessary variables (input prompts, ground-truth outcomes) to evaluate the efficiency and accuracy of the caching mechanism; no additional external data sources are required.
- **Hypothesis on Performance**: The research hypothesis posits that the semantic caching mechanism will achieve a hit-rate of ≥ 40% at a 0.95 threshold, resulting in a ≥ 40% reduction in wall-clock runtime, while maintaining accuracy deviation ≤ 2%. These values are targets for validation, not functional requirements.
- **Hypothesis on Ground Truth**: The "Eywa" benchmark dataset contains specific ground-truth numerical outcomes for all generated iterative sub-tasks. If the official repository provides only qualitative outcomes, the synthetic ground-truth generator (FR-007) will be used, subject to the independence constraint.