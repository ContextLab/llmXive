# Feature Specification: llmXive follow-up: extending "OCC-RAG: Optimal Cognitive Core for Faithful Question Answering"

**Feature Branch**: `001-llmxive-occrag-sparse-core`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Is the capacity for faithful, context-grounded multi-hop reasoning in Retrieval-Augmented Generation implemented via a sparse, localized sub-network or a distributed mechanism across the full architecture of the model?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sparse Sub-network Identification via Gradient-Free Sensitivity (Priority: P1)

The researcher needs to execute a gradient-free sensitivity analysis on the frozen OCC-RAG model. to identify which attention heads and feed-forward neurons are critical for maintaining faithfulness on multi-hop QA tasks. This involves iteratively masking a small fraction of parameters per layer and measuring the resulting delta in the Context Faithfulness Score, compared against a baseline of random masking.

**Why this priority**: This is the core scientific inquiry. Without identifying the sparse sub-network, the hypothesis regarding localized vs. distributed mechanisms cannot be tested. This is the primary deliverable of the research phase.

**Independent Test**: Can be fully tested by running the sensitivity analysis script on a subset of the synthetic corpus and verifying that the output CSV correctly lists parameters ranked by sensitivity score, with a clear distinction between high-sensitivity and low-sensitivity parameters compared to random masking.

**Acceptance Scenarios**:

1. **Given** the frozen OCC-RAG-1.7B model and the 50k synthetic multi-hop QA corpus, **When** the sensitivity analysis script masks [deferred] of attention heads and feed-forward neurons per layer in 10 sequential steps and runs inference on a representative set of samples, **Then** the system outputs a CSV file with columns 'layer_id', 'param_id', 'sensitivity_score', 'delta_faithfulness', and 'random_baseline_score', where the row count matches the total number of masked parameters.
2. **Given** the full set of sensitivity scores, **When** the researcher sorts parameters by magnitude of performance drop relative to the random baseline, **Then** the top [deferred] of parameters are identified as the "Critical Sub-network" candidate.
3. **Given** the analysis is running on a CPU-only environment, **When** the script processes the batch, **Then** the memory usage remains within 7 GB RAM and the job completes without GPU acceleration errors.

---

### User Story 2 - Pruned Model Construction and Lightweight Re-mid-training (Priority: P2)

The researcher needs to construct a pruned model (OCC-RAG-Pruned-{retention_pct}B) by retaining only the identified critical parameters and setting others to zero, followed by a lightweight, CPU-only fine-tuning phase on a set of synthetic examples to recover minor accuracy losses.

**Why this priority**: This validates whether the identified sparse sub-network is sufficient for the task. It transforms the theoretical "sparse core" finding into a deployable model artifact.

**Independent Test**: Can be fully tested by loading the pruned model architecture, running inference on the held-out test set, and confirming that the model structure matches the pruning mask (zeroed weights) and that the fine-tuning process completes without CUDA dependency.

**Acceptance Scenarios**:

1. **Given** the list of critical parameters from User Story 1, **When** the pruning script constructs the new model, **Then** the model weights for the identified critical parameters are non-zero, and all other weights are exactly zero, preserving the original architecture topology.
2. **Given** the pruned model and 10k synthetic examples, **When** the lightweight fine-tuning script runs with a low learning rate, **Then** the training loop completes on CPU within 4 hours and the final loss gradient magnitude falls below a negligible threshold for a sustained period of consecutive epochs.
3. **Given** the fine-tuned pruned model, **When** it is evaluated on the held-out test set, **Then** it produces a Context Faithfulness Score that is within 5% of the original model's score.

---

### User Story 3 - Statistical Validation of Pruning Impact (Priority: P3)

The researcher needs to compare the performance of the pruned model against the original 1.7B model using a paired t-test on per-sample faithfulness scores to determine if the performance drop is statistically significant (p < 0.05). This validates performance preservation, a necessary condition for the sparse core hypothesis.

**Why this priority**: This provides the scientific rigor required to accept or reject the hypothesis. It ensures the findings are not due to random variance.

**Independent Test**: Can be fully tested by running the statistical validation script on the results of the original and pruned models and verifying that the p-value is calculated correctly and the conclusion (significant or not) is reported.

**Acceptance Scenarios**:

1. **Given** the per-sample faithfulness scores for both the original and pruned models on the same test set, **When** the paired t-test is executed, **Then** the system outputs a p-value and a confidence interval.
2. **Given** the p-value is < 0.05, **When** the researcher reviews the results, **Then** the system flags the performance drop as statistically significant, indicating the pruning impacted performance (potential dense mechanism or insufficient pruning).
3. **Given** the p-value is ≥ 0.05, **When** the researcher reviews the results, **Then** the system flags the performance drop as not statistically significant, supporting the hypothesis that the retained sub-network preserves performance.

### Edge Cases

- What happens if the sensitivity analysis reveals that *all* parameters are equally critical (no sparse core)? The system must handle the case where the "top [deferred]" selection yields no meaningful performance difference compared to random selection (flagged if sensitivity delta < 0.01).
- How does the system handle the scenario where the pruned model's architecture becomes incompatible with the inference engine due to zeroed-out layers? The pruning script must ensure the architecture remains valid for standard inference (e.g., by retaining layer structure even with zero weights).
- What if the lightweight fine-tuning fails to recover any accuracy and the model collapses? The system must log this failure and report the final faithfulness score without falsely claiming recovery.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a gradient-free activation patching script that iteratively masks [deferred] of attention heads and feed-forward neurons per layer in the frozen OCC-RAG-1.7B model, and MUST run a control baseline of 10 random masking iterations to distinguish specific sensitivity from general capacity loss (See US-1).
- **FR-002**: System MUST calculate the "Context Faithfulness Score" (weighted sum of ConFiQA accuracy and citation precision) for each masked configuration to determine sensitivity relative to the random baseline (See US-1).
- **FR-003**: System MUST construct a pruned model (OCC-RAG-Pruned-{retention_pct}B) by retaining only the top [deferred] of parameters ranked by sensitivity score (relative to random baseline) and setting others to zero (See US-2).
- **FR-004**: System MUST perform a lightweight, CPU-only fine-tuning phase on the pruned model using 10k synthetic examples with a low learning rate and early stopping (gradient magnitude < 1e-4 for 3 epochs) (See US-2).
- **FR-005**: System MUST execute a paired t-test on per-sample faithfulness scores between the original and pruned models to determine statistical significance (p < 0.05) (See US-3).
- **FR-006**: System MUST ensure all computations run on CPU-only hardware without requiring CUDA, GPU accelerators, or 8-bit/4-bit quantization libraries that depend on GPU (See Assumptions).

### Key Entities

- **Sensitivity Score**: A quantitative metric representing the magnitude of performance drop in the Context Faithfulness Score when a specific parameter is masked, calculated as the difference between the masked score and the random baseline average.
- **Critical Sub-network**: The set of parameters (attention heads and feed-forward neurons) identified as top [deferred] by sensitivity score (relative to random baseline), hypothesized to form the "cognitive core".
- **Context Faithfulness Score**: The primary evaluation metric, defined as a weighted sum of ConFiQA accuracy and citation precision, used to measure the model's ability to ground answers in context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage drop in Context Faithfulness Score for the pruned model is measured against the original 1.7B model's score on the held-out test set (See FR-005, US-3).
- **SC-002**: The statistical significance (p-value) of the performance difference is measured against the threshold of 0.05 using a paired t-test (See FR-005, US-3).
- **SC-003**: The memory footprint of the sensitivity analysis and fine-tuning process is measured against the RAM limit of the GitHub Actions free-tier runner (See FR-006, Assumptions).
- **SC-004**: The total compute time for the sensitivity analysis, pruning, and fine-tuning pipeline is measured against the per-job time limit. (See FR-006, Assumptions).
- **SC-005**: The collinearity (Pearson correlation) between the sensitivity scores of the selected sub-network and a random subset of the same size is measured and must be < 0.2 to validate that the selected set is distinct from random noise (See FR-001, US-1).

## Assumptions

- The OCC-RAG model checkpoint and a large-scale synthetic multi-hop QA corpus are available via the original project repository (GitHub/Zenodo) and HuggingFace Datasets without requiring paid access or proprietary keys.
- The "Context Faithfulness Score" metric can be computed entirely on CPU without requiring GPU-accelerated tensor operations, as the underlying models (ConFiQA, citation precision) are lightweight enough for CPU inference.
- The large-scale model parameters, when masked and stored as sparse tensors, fit within the 7 GB RAM limit. of the GitHub Actions free-tier runner; if not, the dataset will be sampled to ensure feasibility.
- The lightweight fine-tuning phase (a representative subset of examples) will converge within the job limit using standard CPU-based optimizers (e.g., AdamW) without requiring mixed-precision or GPU acceleration.
- The "critical sub-network" identified by the sensitivity analysis will be structurally compatible with standard inference engines, even with a majority of parameters set to zero.
- The dataset (a large set of synthetic examples) contains all necessary variables for the analysis (predictors: model parameters; outcome: faithfulness score; covariates: none required beyond the model inputs), and no additional data collection is needed.
- The analysis is observational in nature (no random assignment of parameters), so findings will be framed as associational regarding the relationship between parameter sparsity and faithfulness, not causal.