# Feature Specification: llmXive follow-up: extending "MiniMax Sparse Attention"

**Feature Branch**: `001-llmxive-sparse-attention-heuristics`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "To what extent can local statistical properties of token blocks (such as entropy and gradient magnitude) approximate the information-selection capability of a learned attention routing mechanism in long-context language models?"

## User Scenarios & Testing

### User Story 1 - Heuristic Injection & Baseline Comparison (Priority: P1)

**Description**: As a researcher, I want to run the frozen MiniMax-M3 model with the learned "Index Branch" disabled and replaced by the "Local Gradient Magnitude" heuristic, so that I can measure if this zero-parameter selector approximates the information-selection capability of the dense attention baseline on the RULER benchmark.

**Why this priority**: This is the core scientific validation. If the heuristic cannot approximate the dense baseline, the subsequent efficiency gains are irrelevant. This story delivers the primary "validity" result.

**Independent Test**: The system can be fully tested by executing a single RULER "Needle In A Haystack" task, logging the Exact Match score for both the dense baseline and the Local Gradient Magnitude heuristic on the same input sequence, and verifying the delta is within the target range.

**Acceptance Scenarios**:

1. **Given** the model is loaded in frozen mode with the Index Branch disabled, **When** the Local Gradient Magnitude heuristic selects the Top-k blocks for a query, **Then** the model generates a response with a retrieval accuracy (Exact Match) that is within 2% (upper bound of the 1-2% expected range) of the dense attention baseline.
2. **Given** a Multi-Hop Retrieval task from the RULER benchmark, **When** the Local Gradient Magnitude heuristic is applied, **Then** the system successfully completes the inference pass on the CPU-only runner without OOM errors and logs the F1 score.

---

### User Story 2 - Multi-Heuristic Evaluation & Statistical Significance (Priority: P2)

**Description**: As a researcher, I want to compare the performance of three distinct heuristics (Block Entropy, Local Gradient Magnitude, Recency-Weighted Bias) against the dense baseline, so that I can determine which local statistical property is the most effective predictor of attention importance.

**Why this priority**: This expands the validity of the findings beyond a single heuristic, providing a comparative analysis that strengthens the conclusion about "local statistical properties" in general.

**Independent Test**: The system can be tested by running the full RULER suite (Needle In A Haystack + Multi-Hop) for all three heuristics and the dense baseline, then generating a summary report containing the mean accuracy and the result of a Wilcoxon signed-rank test.

**Acceptance Scenarios**:

1. **Given** the results for all three heuristics and the dense baseline are collected across 50 distinct RULER tasks, **When** the statistical analysis module runs, **Then** it outputs a Wilcoxon signed-rank test result indicating whether the best heuristic's performance is statistically indistinguishable from the dense baseline (p-value > 0.05) AND the accuracy delta is ≤ 2%. If the delta is ≤ 2% but p < 0.05, the result is flagged as "statistically significant but practically negligible".
2. **Given** the inference logs, **When** the system calculates computational cost, **Then** it reports the CPU time and memory footprint for each heuristic, demonstrating a reduction in overhead compared to the dense baseline.

---

### User Story 3 - Sensitivity Analysis of Selection Thresholds (Priority: P3)

**Description**: As a researcher, I want to sweep the Top-k selection cutoff (e.g., k ∈ {10, 20, 30}) and report how retrieval accuracy varies, so that I can justify the robustness of the heuristic and ensure the results are not dependent on a single arbitrary hyperparameter.

**Why this priority**: This addresses the methodological requirement for "threshold justification & sensitivity." It proves the heuristic's utility is stable across a reasonable range of sparsity levels, preventing the conclusion from being an artifact of a lucky hyperparameter choice.

**Independent Test**: The system can be tested by running the best-performing heuristic from Story 1 with three different k-values and verifying that the accuracy degradation curve is smooth and predictable.

**Acceptance Scenarios**:

1. **Given** the Local Gradient Magnitude heuristic is selected, **When** the system runs inference with k=10, k=20, and k=30 blocks, **Then** the output includes a sensitivity report showing the accuracy drop-off rate for each step, confirming no catastrophic failure at intermediate thresholds.
2. **Given** the sensitivity report, **When** the system compares the accuracy at k=20 to k=30, **Then** it flags if the accuracy drop exceeds 5% for a 10-block increase, triggering a "high sensitivity" warning in the logs.

### Edge Cases

- What happens when the block entropy calculation results in a uniform distribution (zero gradient), causing the heuristic to fail to prioritize any block?
- How does the system handle a RULER task where the "needle" is split across the boundary of two blocks, potentially confusing the block-level selection logic?
- How does the system behave if the frozen model weights are corrupted or if the HuggingFace `transformers` version mismatches the expected architecture?

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the MiniMax-M3 model weights in frozen mode. For the baseline, the system MUST use the dense attention mechanism (Index Branch enabled). For the experimental condition, the system MUST disable the learned "Index Branch" routing mechanism and inject the heuristic selector. (See US-1)
- **FR-002**: System MUST implement the "Local Gradient Magnitude" heuristic to calculate block importance scores via input gradients (gradients with respect to input tokens) using a single backward pass on a small batch (≤ 4 sequences) with cross-entropy loss, ensuring the calculation runs entirely on CPU without GPU acceleration. System MUST log a warning or error if GPU devices are detected during heuristic execution. (See US-1)
- **FR-003**: System MUST implement "Block Entropy" and "Recency-Weighted Positional Bias" heuristics as alternative selection strategies to allow for comparative analysis of different statistical properties. (See US-2)
- **FR-004**: System MUST execute the RULER benchmark tasks (Needle In A Haystack and Multi-Hop Retrieval) using the injected heuristics to measure retrieval accuracy (Exact Match/F1) against the dense attention baseline. (See US-1, US-2)
- **FR-005**: System MUST perform a Wilcoxon signed-rank test on the retrieval accuracy scores of the best-performing heuristic versus the dense attention baseline to determine statistical significance across 50 RULER tasks. (See US-2)
- **FR-006**: System MUST execute a sensitivity analysis sweeping the Top-k selection cutoff over at least three distinct values (e.g., {10, 20, 30}) and report the variation in accuracy rates. (See US-3)

### Key Entities

- **Block**: A fixed-size chunk of a document sequence, containing a subset of tokens, used as the unit of selection for sparse attention.
- **Heuristic Selector**: A parameter-free function (e.g., Gradient Magnitude, Entropy) that maps a block's local statistical properties to a scalar importance score.
- **RULER Task**: A specific evaluation instance from the RULER benchmark (e.g., "Needle In A Haystack" at context length 128k) used to measure retrieval performance.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy difference (Exact Match) between the Local Gradient Magnitude heuristic and the dense attention baseline is measured against the 2% tolerance threshold defined in the research question. (See US-1)
- **SC-002**: The statistical significance of the heuristic's performance is measured against a p-value threshold of 0.05 using a Wilcoxon signed-rank test across the RULER task suite (N=50). (See US-2)
- **SC-003**: The computational efficiency (CPU time and memory footprint) of the heuristic-based inference is measured against the dense attention baseline to quantify overhead reduction. (See US-2)
- **SC-004**: The robustness of the selection strategy is measured against a sensitivity curve generated by sweeping the Top-k cutoff over a defined set of values (e.g., {10, 20, 30}). (See US-3)
- **SC-005**: The feasibility of the method is measured against the constraint of completing the full RULER evaluation suite (N=50 tasks) within 6 hours on a 2-core, CPU-only runner. (See Assumptions)

## Assumptions

- **Assumption about data**: The RULER benchmark dataset and a subset of CommonCrawl are available and can be downloaded within the runner's network timeout limits; if the full dataset exceeds 14 GB disk, the system will sample a representative subset of documents.
- **Assumption about compute**: The frozen MiniMax-M3 model, when loaded with 4-bit or 8-bit quantization disabled (default precision), fits within the 7 GB RAM limit of the GitHub Actions free-tier runner when processing sequences up to the RULER target length.
- **Assumption about methodology**: The "Local Gradient Magnitude" heuristic requires a backward pass on a small batch (≤ 4 sequences) using input gradients; this is assumed to be computationally feasible on CPU within the 6-hour job limit for N=50 tasks.
- **Assumption about validity**: The RULER benchmark tasks are sufficient to proxy for general long-context retrieval capabilities specifically for retrieval-heavy tasks, and the "Needle In A Haystack" metric is a valid proxy for the "information-selection capability" of the attention mechanism in this context. Generative coherence is a separate validation step not covered in this scope.
- **Assumption about thresholds**: The Top-k selection values {10, 20, 30} are a defensible range for the sensitivity analysis based on standard block-sparse attention configurations found in the related work.
- **Assumption about statistical power**: A sample size of N=50 RULER tasks provides sufficient statistical power (≥0.8) to detect an effect size of [deferred] in retrieval accuracy within the 6-hour time budget.