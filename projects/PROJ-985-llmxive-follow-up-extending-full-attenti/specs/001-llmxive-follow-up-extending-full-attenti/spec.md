# Feature Specification: llmXive Follow-up: Extending "Full Attention Strikes Back"

**Feature Branch**: `001-llmxive-static-sparsification`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Full Attention Strikes Back: Transferring Full Attention into Sparse w' - investigating if static linguistic features predict retrieval tokens"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ground Truth Extraction & Static Feature Computation (Priority: P1)

The research pipeline MUST be able to process a corpus of long-context documents to generate two parallel datasets: (1) the ground-truth "RTPurbo-selected tokens" derived from a frozen Llama-3-8B full-attention model using the RTPurbo algorithm, and (2) a corresponding set of static, non-differentiable linguistic features (token entropy, POS tags, position, local perplexity) for every token.

**Why this priority**: This is the foundational data generation step. Without accurate ground truth labels and the corresponding feature vectors, no predictive modeling or hypothesis testing can occur. It establishes the "signal" vs. "noise" baseline.

**Independent Test**: Can be fully tested by running the data processing script on a small sample (e.g., 100 documents) and verifying that the output CSV contains matching token indices, valid entropy values, and binary labels for "RTPurbo-selected token" status, with no GPU memory errors.

**Acceptance Scenarios**:

1. **Given** a subset of 100 documents from the RULER benchmark, **When** the extraction pipeline runs, **Then** it outputs a structured dataset where every token has a computed entropy, POS tag, and a binary label indicating if it was selected by the RTPurbo indexer.
2. **Given** the frozen Llama-3-8B model, **When** processing a document with >4k tokens, **Then** the system completes the full attention map generation and RTPurbo extraction.

---

### User Story 2 - Static Predictor Training & Heuristic Derivation (Priority: P2)

The system MUST train a CPU-based machine learning model (Decision Tree or Logistic Regression) to predict the "RTPurbo-selected token" label using only the static features, and subsequently derive a hard, rule-based heuristic (e.g., "Select if Entropy > X AND POS in {NOUN, PROPN}") from the model's feature importance or decision boundaries.

**Why this priority**: This directly addresses the core research hypothesis: whether static features can replace learned indexing. It transforms the data into a testable static policy.

**Independent Test**: Can be fully tested by training the model on a training split and evaluating it on a validation split; the system must output a specific set of rules (thresholds and conditions) and a baseline accuracy metric for the static predictor.

**Acceptance Scenarios**:

1. **Given** the feature-labeled dataset, **When** the training script executes, **Then** it produces a trained scikit-learn model and a derived rule set (e.g., specific entropy threshold and POS list) that outputs the achieved precision metric on the validation set.
2. **Given** the derived rule set, **When** applied to a held-out test set, **Then** the system can reconstruct the "RTPurbo-selected tokens" using *only* these static rules without accessing the LLM or the RTPurbo indexer.

---

### User Story 3 - Sparsification Evaluation & Statistical Comparison (Priority: P3)

The system MUST evaluate the performance of the static-heuristic sparsification against the original learned RTPurbo and full-attention baselines on downstream tasks (perplexity, needle retrieval), and perform statistical significance testing to determine if the performance drop is negligible or substantial. The learned baseline must be averaged over multiple runs to ensure statistical validity.

**Why this priority**: This is the final validation step that answers the research question. It quantifies the trade-off between the efficiency of static rules and the accuracy of learned attention.

**Independent Test**: Can be fully tested by running the evaluation suite on the test set and generating a report comparing the three methods (Full, Learned Sparse, Static Sparse) with p-values from paired t-tests.

**Acceptance Scenarios**:

1. **Given** the static-heuristic policy, **When** it is integrated into the attention mechanism for the test set, **Then** the resulting perplexity and exact-match scores are recorded and compared to the baselines.
2. **Given** the performance metrics for all three methods (where the Learned Sparse baseline is an average of 5 seeds), **When** the statistical analysis runs, **Then** it outputs a p-value indicating whether the difference between "Static Sparse" and the "Learned Sparse" average is statistically significant (α = 0.05).

---

### Edge Cases

- What happens if the static features (e.g., POS tags) are ambiguous or missing for certain tokens (e.g., special characters, emojis)? The system must handle these by assigning a default "neutral" category or excluding them from the heuristic logic, ensuring no runtime crashes.
- How does the system handle documents where the RTPurbo algorithm fails to identify *any* RTPurbo-selected tokens (e.g., extremely uniform attention)? The pipeline must flag these as anomalies and exclude them from the statistical comparison to avoid skewing the results.
- What if the dataset size exceeds the 7 GB RAM limit of the CI runner? The system must implement a chunking strategy or sampling mechanism to process documents sequentially without loading the entire corpus into memory at once.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess a diverse subset of [deferred] long-context documents from the RULER and Needle-in-Haystack benchmarks to serve as the evaluation corpus (See US-1).
- **FR-002**: System MUST run a frozen Llama-3-8B model to generate full attention maps and apply the RTPurbo algorithm to extract ground-truth "RTPurbo-selected tokens" for every sequence (See US-1).
- **FR-003**: System MUST compute static linguistic features (Shannon entropy, POS tags via spaCy, positional encodings, local semantic density) for every token without using GPU acceleration (See US-1).
- **FR-004**: System MUST train a CPU-based classifier (Decision Tree or Logistic Regression) using scikit-learn to predict RTPurbo-selected token labels and derive a deterministic rule-based heuristic from the model (See US-2).
- **FR-005**: System MUST execute the sparsified attention mechanism using the static heuristic and measure perplexity and downstream task accuracy (exact match) against the full-attention and learned-sparse baselines (See US-3).
- **FR-006**: System MUST perform a paired t-test or Wilcoxon signed-rank test to determine if the performance difference between the static heuristic and the learned sparse model (averaged over 5 seeds) is statistically significant (See US-3).
- **FR-007**: System MUST implement a memory-efficient data loader that processes documents in chunks to ensure the total RAM usage does not exceed 7 GB during the full pipeline execution (See Assumption A6).
- **FR-008**: System MUST evaluate the Learned Sparse baseline (RTPurbo) over 5 independent random seeds and use the mean performance as the baseline for statistical comparison to account for training variance (See US-3).

### Key Entities

- **TokenUnit**: Represents a single token in the corpus, containing attributes: `text`, `position`, `entropy`, `pos_tag`, `is_rtpurbo_selected` (ground truth), `predicted_retrieval` (static).
- **AttentionMap**: Represents the full attention weights for a sequence, used to derive the ground truth RTPurbo selection set.
- **StaticHeuristic**: A set of derived rules (e.g., thresholds, sets) used to select tokens without model inference.
- **EvaluationMetric**: A structured record containing `perplexity`, `exact_match`, and `statistical_p_value` for a specific method (Full, Learned, Static).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy of the static predictor (precision/recall) is measured against the ground-truth RTPurbo-selected tokens derived from the RTPurbo algorithm (See FR-004, US-2).
- **SC-002**: The perplexity of the static-heuristic sparsified model is measured against the full-attention baseline and the learned RTPurbo sparse model (averaged over 5 seeds) to quantify performance degradation (See FR-005, US-3).
- **SC-003**: The downstream task accuracy (exact match on needle retrieval) is measured against the baseline performance of the full-attention model to assess task-level impact (See FR-005, US-3).
- **SC-004**: The statistical significance of the performance difference between static and learned methods is measured using a paired t-test or Wilcoxon test (α=0.05) to determine if the drop is negligible (See FR-006, US-3).
- **SC-005**: The total execution time of the full pipeline (data extraction, training, evaluation) is measured against the 6-hour CI time limit to ensure feasibility on free-tier runners (See FR-007, Assumption A6).

## Assumptions

- **Assumption A1**: The RULER and Needle-in-Haystack datasets are accessible via public URLs and the [deferred]-document subset fits within the 14 GB disk limit when processed sequentially.
- **Assumption A2**: The Llama-3-8B model weights are available in a format compatible with CPU inference (e.g., via `transformers` library) and can be loaded without requiring 8-bit quantization or CUDA-specific libraries.
- **Assumption A3**: The analysis relies on the assumption that static features (entropy, POS) are computationally inexpensive to derive compared to the attention mechanism, ensuring the feature engineering step does not dominate the runtime.
- **Assumption A4**: The "RTPurbo-selected tokens" identified by RTPurbo are treated as the ground truth for the hypothesis test, acknowledging that this validates the static heuristic's ability to mimic RTPurbo behavior rather than discovering an absolute linguistic necessity, as RTPurbo itself is a learned model proxy.
- **Assumption A5**: The performance drop threshold for "negligible" is defined as [deferred] relative drop in perplexity or exact match, based on the project's expected results section; this value will be used as the decision boundary for hypothesis falsification.
- **Assumption A6**: The CI runner environment has a hard memory limit of 7 GB RAM, requiring the pipeline to process data in chunks to avoid Out of Memory errors.