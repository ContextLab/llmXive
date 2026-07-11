# Feature Specification: llmXive follow-up: extending "MemLens"

**Feature Branch**: `001-llmxive-memlens-granularity`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Lang'"

## User Scenarios & Testing

### User Story 1 - Multi-Session Reasoning Evaluation (Priority: P1)

The system MUST process the filtered MemLens dataset (Multi-Session Reasoning and Temporal Reasoning subsets) to generate answers using a retrieval-augmented generation pipeline. This is the core research function: without the ability to run the evaluation loop, no data can be collected to answer the research question.

**Why this priority**: This is the primary value driver. The entire project exists to measure the delta in accuracy between indexing strategies. If this fails, the research question cannot be answered.

**Independent Test**: Can be fully tested by running the evaluation script against a small, hardcoded subset of 5 MemLens queries and verifying that the system produces an output JSON with generated answers and ground truth labels, without requiring the full dataset or complex statistical analysis.

**Acceptance Scenarios**:

1. **Given** a filtered MemLens query requiring multi-session reasoning, **When** the system constructs a context window from the "Fine Store" (object-level embeddings), "Medium Store" (summaries + CLIP), or "Coarse Store" (summaries only) and passes it to the frozen LLM, **Then** the system outputs a generated answer string and records the exact match score against the ground truth.
2. **Given** a query where the answer relies on visual details from a previous session, **When** the system retrieves context from the "Coarse Store" (session summaries only), **Then** the system outputs an answer (potentially incorrect) and records the semantic similarity score against the ground truth.
3. **Given** a query with no relevant historical context, **When** the system attempts retrieval, **Then** the system returns an empty or low-confidence context window and generates an answer based solely on the current prompt, recording the result.

---

### User Story 2 - Comparative Indexing Strategy Execution (Priority: P2)

The system MUST execute the same evaluation loop across three distinct memory store configurations: Coarse (text summaries only), Medium (summaries + CLIP embeddings), and Fine (object-level captions + bounding boxes). This allows the direct comparison required to isolate the effect of semantic granularity.

**Why this priority**: The research question specifically asks about the *influence* of granularity. Without running all three variants, the comparative analysis (ANOVA/Friedman) cannot be performed.

**Independent Test**: Can be fully tested by running the pipeline on 10 queries for each of the three store types and verifying that the output logs contain distinct entries for "Coarse," "Medium," and "Fine" strategies with non-identical context windows and potentially different generated answers.

**Acceptance Scenarios**:

1. **Given** the same query and ground truth, **When** the system runs the "Coarse Store" pipeline, **Then** the context window contains only text summaries and no image embeddings or object descriptions.
2. **Given** the same query and ground truth, **When** the system runs the "Fine Store" pipeline, **Then** the context window contains object-level captions and bounding box descriptions derived from a CPU-optimized detector.
3. **Given** a completed run of all three strategies, **When** the system aggregates results, **Then** the output includes a structured dataset linking each query ID to its accuracy score for each of the three indexing strategies.

---

### User Story 3 - Efficiency and Resource Profiling (Priority: P3)

The system MUST measure and record the retrieval latency (time to construct context) and peak RAM usage for each indexing strategy. This validates the "CPU-tractability" constraint and the trade-off hypothesis that fine-grained indexing may be more accurate but computationally heavier.

**Why this priority**: The motivation explicitly mentions the need for "efficient, CPU-tractable memory systems." Accuracy without feasibility is not a viable solution for the target constraints.

**Independent Test**: Can be fully tested by instrumenting the retrieval pipeline on a single query and verifying that the logs contain numerical values for `latency_ms` and `peak_ram_mb` for the specific strategy being tested.

**Acceptance Scenarios**:

1. **Given** a retrieval request against the "Fine Store," **When** the system executes the cosine similarity search, **Then** the system logs the elapsed time in milliseconds.
2. **Given** a full evaluation run, **When** the system monitors the process memory, **Then** the system records the peak RAM usage in MB for each of the three store types.
3. **Given** a comparison of the three strategies, **When** the results are aggregated, **Then** the system outputs a summary table showing the trade-off between accuracy gain and latency/RAM overhead for each strategy.

### Edge Cases

- What happens when the object detector (e.g., YOLOv8n) fails to detect any objects in a session image? (System must handle empty object lists gracefully, falling back to image-level embeddings or a null context without crashing).
- How does the system handle a query that references a session not present in the filtered subset? (System must return a "context not found" state and record a baseline failure).
- What happens if the LLM generation exceeds the 6-hour total job limit due to the volume of queries? (System must support checkpointing/resuming or limit the sample size to ensure completion within the CI runner constraints).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the MemLens dataset and filter for the subset of queries requiring Multi-Session Reasoning (MSR) and Temporal Reasoning (TR). (See US-1)
- **FR-002**: System MUST construct three distinct memory stores strictly adhering to Constitution Principle VI: Coarse (text summaries only, discarding all image data), Medium (summaries + frozen CLIP embeddings), and Fine (summaries + object-level captions + bounding boxes via CPU-optimized detector). (See US-2)
- **FR-003**: System MUST execute a retrieval-augmented generation loop using `faiss-cpu` or `scikit-learn` for cosine similarity, retrieving top-k=5 chunks for each query against each store. (See US-2)
- **FR-004**: System MUST generate answers using a frozen, 4-bit quantized LLM (e.g., Llama-3-8B-Instruct) running strictly on CPU without CUDA/GPU acceleration. (See US-1)
- **FR-005**: System MUST calculate performance metrics (exact match, semantic similarity) and efficiency metrics (latency, peak RAM) for every query-store combination. (See US-3)
- **FR-006**: System MUST perform a statistical analysis (repeated-measures ANOVA or Friedman test) to determine if the differences in accuracy across the three indexing strategies are statistically significant, and output the calculated p-value and the resulting decision (reject/fail to reject null hypothesis) to the results dataset. (See US-2)
- **FR-007**: System MUST ensure ground truth labels are derived strictly from original MemLens annotations, independent of the generated memory stores, to prevent circular validation. (See US-1)
- **FR-008**: System MUST report the distribution of excluded queries (those with missing metadata) to detect potential selection bias, ensuring the exclusion is not correlated with specific session types or visual complexity. (See US-2)

### Key Entities

- **Query**: A single question from the MemLens dataset requiring multi-session reasoning, including the ground truth answer and session metadata.
- **MemoryStore**: A collection of retrieved context chunks, parameterized by its granularity level (Coarse, Medium, Fine) and the underlying data representation (text, embeddings, object captions).
- **EvaluationResult**: A record containing the query ID, the indexing strategy used, the generated answer, the accuracy score, the retrieval latency, and the peak RAM usage.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in reasoning accuracy (exact match and semantic similarity) between the "Fine" and "Coarse" indexing strategies is measured against the null hypothesis of no difference (See US-2).
- **SC-002**: The statistical significance of the granularity effect is measured against a p-value threshold of 0.05 using a repeated-measures ANOVA or Friedman test (See US-2).
- **SC-003**: The computational cost (latency and RAM) of the "Fine" strategy is measured against the "Coarse" strategy to quantify the efficiency trade-off (See US-3).
- **SC-004**: The validity of the evaluation is measured by ensuring [deferred] of ground truth labels are sourced strictly from the original MemLens annotations without derivation from the retrieval process, verified by loading labels from a read-only external file prior to any retrieval logic (See US-1).
- **SC-005**: The feasibility of the method is measured by confirming the entire evaluation pipeline completes within the CI runner constraints (≤6 hours, ≤7 GB RAM, no GPU) (See US-1).

## Assumptions

- **Assumption about dataset availability**: The MemLens dataset is publicly available and can be downloaded directly from the official repository without authentication barriers or proprietary restrictions.
- **Assumption about model compatibility**: A low-bit quantized Llama-8B-Instruct model (or similar) can run inference on a standard CPU-only GitHub Actions runner (2 cores, 7 GB RAM) within the 6-hour time limit for the filtered subset of queries.. If the 6-hour limit is exceeded, the system will dynamically reduce the sample size to ensure completion, or the study will be interpreted as demonstrating CPU-inefficiency for that model size.
- **Assumption about detector performance**: A CPU-optimized object detector (e.g., YOLOv8n) can process the session images within the time budget and provide sufficiently accurate object-level captions for the "Fine Store" construction.
- **Assumption about statistical power**: The filtered subset of queries provides sufficient statistical power to detect a medium effect size in a repeated-measures ANOVA.; if the power is low, the result will be interpreted as "inconclusive due to sample size" rather than a false negative.
- **Assumption about variable fit**: The MemLens dataset contains the necessary ground truth labels for both "Multi-Session Reasoning" and "Temporal Reasoning" tasks, allowing for the isolation of the indexing granularity variable. The dataset provides explicit task-type metadata (e.g., `task_type` field) for each query, enabling clean filtering. If metadata is missing for < 5% of queries, those entries are excluded from the analysis to maintain dataset integrity. The system will report the distribution of these excluded queries to verify the exclusion is not biased (See FR-008). (See US-1)
- **Assumption about inference framing**: Since the study uses a fixed dataset and experimental conditions without random assignment of participants, findings will be framed as associational relationships between indexing granularity and performance, not causal effects on human cognition.