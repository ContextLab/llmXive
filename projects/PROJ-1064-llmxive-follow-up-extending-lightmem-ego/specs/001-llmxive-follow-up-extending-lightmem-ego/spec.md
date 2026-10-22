# Feature Specification: llmXive follow-up: extending "LightMem-Ego: Your AI Memory for Everyday Life"

**Feature Branch**: `001-semantic-decay-retrieval`  
**Created**: 2026-07-28  
**Status**: Draft  
**Input**: User description: "Can a 'Semantic Decay' retrieval mechanism, which dynamically weights memory nodes by semantic relevance and learnable forgetting curves rather than fixed temporal hierarchies, improve the recall of rare, semantically significant events in long-term egocentric memory retrieval on CPU-constrained devices?"

## User Scenarios & Testing

### User Story 1 - Benchmarking Dynamic vs. Fixed Retrieval Accuracy (US-1) (Priority: P1)

A researcher needs to quantitatively compare the retrieval accuracy of a new "Semantic Decay" algorithm against the existing fixed hierarchical baseline (LightMem-Ego) specifically for rare events that occurred more than 14 days ago, to determine if the dynamic model solves the "catastrophic forgetting" problem.

**Why this priority**: This is the core research question. Without establishing whether the new mechanism actually improves Top-1 accuracy for long-term rare events, no further optimization or deployment is meaningful.

**Independent Test**: Execute the evaluation protocol on a CPU‑only runner using a fixed set of representative user queries. (including the specific "long-term" subset) and compare the Top-1 accuracy scores of both models.

**Acceptance Scenarios**:

1. **Given** a multi-week egocentric dataset and a substantial set of labeled queries, **When** the system runs the Semantic Decay retriever and the Fixed Hierarchy retriever on a CPU-only environment, **Then** the system must output a comparative accuracy report showing the Top-1 accuracy for events >14 days old for both models.
2. **Given** the baseline Fixed Hierarchy model, **When** it retrieves results for queries regarding events older than 14 days, **Then** the system must record the baseline accuracy to serve as the reference point for the improvement calculation.
3. **Given** the Semantic Decay model, **When** it retrieves results for the same long-term queries, **Then** the system must calculate and report the percentage improvement (or degradation) relative to the baseline.

---

### User Story 2 - Latency and Resource Constraint Validation (US-2) (Priority: P2)

A deployment engineer needs to verify that the Semantic Decay mechanism does not introduce prohibitive computational overhead, ensuring that inference latency remains [deferred] and the process fits within standard CPU-only CI limits (2 cores, 7GB RAM).

**Why this priority**: Even if accuracy improves, the method is useless if it cannot run on the target hardware (mobile CPU or free-tier CI). This validates the "CPU-constrained" constraint of the research question.

**Independent Test**: Measure the inference time and memory footprint of the Semantic Decay retriever during the benchmark run and compare it against the 200ms threshold and CI resource limits.

**Acceptance Scenarios**:

1. **Given** a standard CPU-only runner environment, **When** the Semantic Decay retriever processes a single query, **Then** the system must record the inference latency and confirm it is ≤ 200 ms for **all** queries.
2. **Given** the full dataset loaded into memory, **When** the retrieval process runs, **Then** the system must not exceed 7 GB of RAM usage at any point during execution.
3. **Given** the need to estimate energy consumption, **When** the system runs, **Then** it must output an estimated CPU cycle count per query and demonstrate that the average cycles increase by no more than 10 % relative to the baseline.

---

### User Story 3 - Robustness Check on Short-Term Retrieval (US-3) (Priority: P3)

A quality assurance specialist needs to ensure that optimizing for long-term rare events does not degrade the performance of retrieving recent events (1-3 days old), maintaining the system's utility for immediate recall.

**Why this priority**: A model that improves long-term recall but fails at short-term recall is a regression. This ensures the "dynamic decay" does not disrupt the existing utility of the memory system.

**Independent Test**: Analyze the retrieval accuracy of both models specifically on the subset of queries targeting events aged 1-3 days.

**Acceptance Scenarios**:

1. **Given** the subset of queries for events aged 1-3 days, **When** the Semantic Decay model retrieves results, **Then** the Top-1 accuracy must not drop by more than 5 % compared to the Fixed Hierarchy baseline, and the final report must explicitly flag any degradation exceeding this threshold for manual review.
2. **Given** the full evaluation results, **When** the system generates the final report, **Then** it must explicitly flag any significant degradation in short-term performance for manual review.

---

### Edge Cases

- **What happens when** the dataset contains no "rare" events (e.g., all events are routine and frequent)? The system must handle this gracefully and report that the "rare event" subset is empty or below the statistical power threshold (see FR-009 / SC-006).
- **How does the system handle** a decay rate $\lambda$ that converges to zero or infinity during optimization? The system must enforce bounds on $\lambda$ ($0 < \lambda < 10$) to prevent numerical instability or a collapse back to the fixed hierarchy (see FR-010 / SC-007).
- **What happens when** the vector database index becomes corrupted or the FAISS HNSW index fails to load? The system must fail fast with a clear error message rather than returning random or empty results (see FR-011 / SC-008).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a "Semantic Decay" retrieval function calculating a relevance score $S = \alpha \cdot \text{sim}(q, m) + \beta \cdot e^{-\lambda \cdot t}$, where $\lambda$ is a learnable parameter optimized via grid search on a validation set. The grid search must explore $\lambda \in \{0.1, 0.2, \dots, 9.9\}$ and select the value that maximizes Top‑1 accuracy on a 50‑query validation set. (See US-1)
- **FR-002**: The system MUST implement a baseline "Fixed Hierarchy" retriever that strictly routes queries to "current," "short-term," or "long-term" buckets based on explicit timestamp thresholds without semantic weighting. (See US-1)
- **FR-003**: The system MUST execute the evaluation protocol on a substantial set of user queries spanning 1‑day to 30‑day lookups and output a comparative accuracy report. (See US-1)
- **FR-004**: The system MUST measure and record inference latency (in ms) and estimated energy consumption (via CPU cycle counts) for every query processed. (See US-2)
- **FR-005**: The system MUST perform a McNemar’s test to determine if the difference in Top‑1 accuracy between the Semantic Decay and Fixed Hierarchy models for the "long-term" subset is statistically significant ($p < 0.05$). (See US-1)
- **FR-006**: The system MUST validate that the inference latency for the Semantic Decay model does not exceed 200 ms for **all** queries. (See US-2)
- **FR-007**: The system MUST verify that the Top‑1 accuracy for short‑term queries (1‑3 days) does not degrade by more than 5 % compared to the baseline **and** the final evaluation report must flag any degradation >5 % for manual review. (See US-3)
- **FR-008**: The system MUST utilize a CPU‑only execution environment (no GPU, no CUDA, no mixed‑precision training) and ensure memory usage remains under 7 GB. (See US-2)
- **FR-009**: If the rare‑event subset contains fewer than 30 events, the system MUST abort the long‑term accuracy analysis and emit a clear report flag indicating insufficient statistical power. (See Edge Cases)
- **FR-010**: During grid search, any candidate $\lambda$ outside the interval $(0, 10)$ MUST cause the search to reject that value and raise a validation error. (See Edge Cases)
- **FR-011**: If the FAISS HNSW index fails to load, the system MUST raise a runtime exception with the message “FAISS index load failure: <details>” and terminate the retrieval pipeline. (See Edge Cases)
- **FR-012**: The system MUST identify “rare events” as event classes that occur **≤ 5 times** in the 60‑day corpus. (See Assumptions)
- **FR-013**: The system MUST record the average CPU cycles per query for both Semantic Decay and Fixed Hierarchy models and ensure the Semantic Decay average does not exceed 110 % of the baseline average. (See US-2)
- **FR-014**: The system MUST enforce the λ bounds $0 < \lambda < 10$ during training and inference; violations must trigger the error defined in FR‑010. (See Edge Cases)
- **FR-015**: The grid‑search procedure (as described in FR‑001) must be deterministic: use a fixed seed, enumerate λ values in ascending order, and select the first λ achieving the maximal validation Top‑1 accuracy. (See US-1)

### Key Entities

- **Memory Node**: A vector embedding representing an audio‑visual segment, associated with a timestamp and metadata.
- **Query**: A user intent representation (vector) used to search for relevant memory nodes.
- **Decay Parameter ($\lambda$)**: A scalar value learned during the grid search that controls the rate of semantic forgetting.
- **Evaluation Report**: A structured output containing accuracy metrics, latency stats, energy consumption, and statistical test results.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The improvement in Top‑1 accuracy for events older than 14 days is measured against the baseline Fixed Hierarchy model (See FR-001, FR-003, US-1).
- **SC-002**: The statistical significance of the accuracy improvement is measured using McNemar’s test with a threshold of $p < 0.05$ (See FR-005, US-1).
- **SC-003**: Inference latency for **all** queries must be ≤ 200 ms; the system must record latency per query and report the maximum observed latency (See FR-006, US-2).
- **SC-004**: Short‑term retrieval accuracy degradation is measured against the 5 % tolerance limit; any breach must be flagged in the final report (See FR-007, US-3).
- **SC-005**: Memory footprint is measured against the 7 GB RAM limit of the free‑tier CI runner (See FR-008, US-2).
- **SC-006**: When the rare‑event subset size is < 30, the report must contain a flag “Insufficient rare‑event data: analysis skipped” (See FR-009).
- **SC-007**: All λ values used during training/inference must satisfy $0 < \lambda < 10$; any violation must be captured in logs and cause pipeline termination (See FR-010, FR-014).
- **SC-008**: FAISS index load failures must produce the exact error message “FAISS index load failure: <details>” and abort execution (See FR-011).
- **SC-009**: Average CPU cycles per query for the Semantic Decay model must be ≤ 110 % of the baseline average; the report must include both averages and the ratio (See FR-013, US-2).
- **SC-010**: The McNemar’s test p‑value must be reported; the test is considered successful only if $p < 0.05$ (See FR-005).

## Assumptions

- The 60‑day egocentric dataset (e.g., from Ego4D or LightMem‑Ego repository) contains sufficient ground‑truth labels for “rare” events to perform a statistically valid comparison, **provided** at least 30 rare events exist as defined by FR‑012.
- The FAISS HNSW index implementation is compatible with CPU‑only execution and fits within the 7 GB RAM constraint for the specified dataset size.
- The “Semantic Decay” formula $S = \alpha \cdot \text{sim}(q, m) + \beta \cdot e^{-\lambda \cdot t}$ correctly captures the user’s “learnable forgetting curve” concept, where $\lambda$ is the decay rate.
- The grid search for $\lambda$ will converge within a reasonable number of iterations on a small validation set of 50 queries, ensuring the total compute time remains bounded (see FR‑001 and FR‑015).
- The vector embeddings generated by the existing LightMem‑Ego encoder are stable and do not require retraining, as the focus is on the retrieval mechanism.
- The “energy consumption” metric will be approximated via CPU cycle counts as a proxy, as precise Joule measurement is not available in the CI environment.
- The dataset variables (timestamps, event labels, embeddings) are present and correctly formatted in the source data; if a required variable (e.g., explicit “rare event” flag) is missing, the system will rely on the heuristic definition (≤ 5 occurrences) defined in FR‑012.
