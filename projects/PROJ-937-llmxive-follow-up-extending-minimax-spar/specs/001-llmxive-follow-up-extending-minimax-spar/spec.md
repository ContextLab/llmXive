# Feature Specification: llmXive follow-up: extending "MiniMax Sparse Attention"

**Feature Branch**: `001-llmxive-sparse-attention-heuristics`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'MiniMax Sparse Attention' - To what extent do local signal statistics (block entropy and gradient magnitude) capture the semantic importance of context tokens in long-window language models, and can these local approximations theoretically substitute for learned selection mechanisms without degrading retrieval performance?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CPU-Feasible Heuristic Evaluation (Priority: P1)

As a researcher, I want to execute the block-sparse attention selection logic using three deterministic heuristics (Block Entropy, Local Gradient Magnitude, Recency Bias) on a CPU-only environment without GPU acceleration, so that I can verify the feasibility of replacing the learned Index Branch on resource-constrained hardware.

**Why this priority**: This is the foundational capability; without a working CPU-only execution path, no comparison or accuracy measurement can occur. It directly addresses the "compute feasibility" constraint of the project.

**Independent Test**: Can be fully tested by running the inference script on the RULER "Needle In A Haystack" subset on a standard 2-core runner and confirming that the process completes within 6 hours without CUDA errors or out-of-memory exceptions.

**Acceptance Scenarios**:

1. **Given** the MiniMax-M3 model is loaded in frozen mode and the RULER dataset is chunked, **When** the script runs with `device="cpu"` and heuristic selection enabled, **Then** the inference completes successfully without raising `RuntimeError: CUDA` or `OutOfMemoryError`.
2. **Given** a batch of 100 context blocks, **When** the Local Gradient Magnitude heuristic is calculated, **Then** the selection logic returns the Top-k blocks based on gradient norms and reports the execution time in seconds.

---

### User Story 2 - Retrieval Accuracy & Perplexity Benchmarking (Priority: P2)

As a researcher, I want to measure the retrieval accuracy (Exact Match/F1) and perplexity of the heuristic-based sparse attention against the learned Index Branch baseline, so that I can determine if the local heuristics preserve semantic fidelity within the expected 1-2% margin.

**Why this priority**: This addresses the core research question regarding "semantic importance" capture. It is the primary metric for the "Expected Results" section.

**Independent Test**: Can be fully tested by comparing the F1 scores of the "Block Entropy" heuristic run against the "Learned Index Branch" run on the same RULER task subset and calculating the percentage difference.

**Acceptance Scenarios**:

1. **Given** the model has processed the "Needle In A Haystack" task using the Block Entropy heuristic, **When** the retrieval accuracy is calculated, **Then** the result is reported alongside the Learned Index Branch baseline with a difference value explicitly stated.
2. **Given** a set of Multi-Hop Retrieval tasks, **When** perplexity is measured for the Recency-Weighted heuristic, **Then** the output includes the exact perplexity score and the delta relative to the dense baseline.

---

### User Story 3 - Statistical Significance & Sensitivity Analysis (Priority: P3)

As a researcher, I want to perform a Wilcoxon signed-rank test on the retrieval scores and a sensitivity analysis on the selection thresholds, so that I can validate the robustness of the findings against random variance and arbitrary cutoff choices.

**Why this priority**: This ensures the results are scientifically defensible (addressing methodological soundness regarding multiplicity and threshold justification) before any claims are made.

**Independent Test**: Can be fully tested by running the analysis script which outputs a p-value for the Wilcoxon test and a table showing accuracy variance across three different Top-k thresholds.

**Acceptance Scenarios**:

1. **Given** the retrieval accuracy scores for 5 distinct RULER tasks, **When** a Wilcoxon signed-rank test is performed between the best heuristic and the learned baseline, **Then** the output includes the p-value and a clear statement of statistical significance (p < 0.05).
2. **Given** a Top-k selection threshold of 0.05 for gradient magnitude, **When** the sensitivity analysis sweeps the threshold to {0.01, 0.05, 0.1}, **Then** the report shows the variation in false-positive rates (defined as selecting a block that does NOT contain the target 'needle' string when the Learned Index Branch would have selected it) and the final accuracy for each sweep value.

---

### Edge Cases

- **What happens when** the gradient magnitude or entropy score for all blocks in a window is near-zero? (System must fallback to selecting the first k blocks to ensure deterministic behavior and avoid empty KV caches).
- **How does system handle** a context window that exceeds the 7 GB RAM limit of the runner? (System must implement streaming chunking or aggressive subsampling to fit the data).
- **What happens when** the RULER dataset is partially corrupted or missing specific "needle" strings? (System must log a warning and skip the specific sample, reporting the exclusion count).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load the MiniMax-M3 model weights in frozen mode and disable the original learned "Index Branch" parameters for inference, serving as a fixed reference baseline. (See US-1)
- **FR-002**: System MUST implement three distinct CPU-executable selection heuristics: (1) Block Entropy, (2) Local Gradient Magnitude (computed via a proxy next-token prediction loss), and (3) Recency Bias (standard baseline for long-context attention). (See US-1)
- **FR-003**: System MUST execute the inference loop on a standard 2-core CPU runner without requiring CUDA, GPU, or 8-bit/4-bit quantization libraries. If memory constraints prevent loading the full model, the system MUST reduce context to [deferred] tokens OR reduce batch size to 1, whichever is necessary. If 4k context + batch 1 still exceeds 7 GB RAM, the system MUST exit with code 1 and log "Memory constraint exceeded". (See US-1)
- **FR-004**: System MUST calculate and output retrieval accuracy (Exact Match and F1) and perplexity for each heuristic against the Learned Index Branch baseline on RULER tasks. (See US-2)
- **FR-005**: System MUST perform a Wilcoxon signed-rank test comparing the retrieval accuracy of the best-performing heuristic against the learned baseline to determine statistical significance. (See US-3)
- **FR-006**: System MUST execute a sensitivity analysis sweeping the selection threshold (e.g., Top-k or gradient cutoff) across at least three values (e.g., 0.01, 0.05, 0.1) and report the resulting variation in accuracy. (See US-3)
- **FR-007**: System MUST ensure that data loading and processing fit within ~7 GB RAM and ~14 GB disk constraints, utilizing subsampling (defined as reducing context window to [deferred] tokens OR reducing batch size to 1) if necessary. (See US-1)

### Key Entities

- **HeuristicSelector**: An abstract component responsible for scoring and selecting the Top-k key-value blocks based on input signal statistics (entropy, gradients).
- **RetrievalMetric**: A data structure storing the Exact Match, F1, and Perplexity scores for a specific model configuration on a specific RULER task.
- **SensitivitySweep**: A record containing the threshold value, the resulting selection set, and the corresponding accuracy metrics used to validate robustness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The retrieval accuracy (F1) of the best-performing heuristic is measured against the Learned Index Branch baseline on the RULER benchmark tasks. (See US-2)
- **SC-002**: The computational cost (CPU time) and memory footprint of the heuristic execution are measured against the 6-hour time limit and 7 GB RAM constraint of the GitHub Actions free-tier runner; success is defined as completing in < 6 hours. (See US-1)
- **SC-003**: The statistical significance of the accuracy difference is measured against the p < 0.05 threshold using a Wilcoxon signed-rank test on the RULER task scores. (See US-3)
- **SC-004**: The robustness of the selection threshold is measured against the variance in accuracy rates across the sensitivity sweep values {0.01, 0.05, 0.1}. (See US-3)
- **SC-005**: The inference stability is measured against the requirement of zero CUDA-related runtime errors during execution on a CPU-only environment. (See US-1)

## Assumptions

- **Assumption about data**: The RULER benchmark dataset is available and can be downloaded directly via the HuggingFace datasets library or a standard HTTP request without requiring a paid API key or restricted access.
- **Assumption about model**: The MiniMax-M3 model weights are compatible with the `transformers` library in frozen mode and do not require custom CUDA kernels that cannot be mocked or disabled on CPU.
- **Assumption about gradients**: Calculating local gradient magnitudes via a single backward pass on a small batch is computationally feasible on the 2-core CPU runner within the 6-hour window, provided the batch size is restricted to ≤ 4. The gradients are derived from a proxy next-token prediction loss (cross-entropy), not the retrieval task itself.
- **Assumption about threshold justification**: The values {0.01, 0.05, 0.1} are selected as log-spaced candidate thresholds for the sensitivity analysis to observe variance, without asserting any as a community standard.
- **Assumption about inference framing**: Since the study uses a frozen model and observational benchmark data (RULER) without random assignment of tokens, findings will be framed as associational (correlation between heuristics and performance) rather than causal.