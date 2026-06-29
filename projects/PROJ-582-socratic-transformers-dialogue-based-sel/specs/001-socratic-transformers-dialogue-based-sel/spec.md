# Feature Specification: Socratic Transformers: Dialogue-Based Self-Teaching Through Adversarial Questioning

**Feature Branch**: `582-socratic-transformers-dialogue-based-self-teaching`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Socratic Transformers: Dialogue-Based Self-Teaching Through Adversarial Questioning"

## User Scenarios & Testing

### User Story 1 - Adversarial Dialogue Data Generation (Priority: P1)

The system MUST generate two distinct training datasets: one composed of static QA pairs and one composed of multi-turn self-dialogues where the model critiques and revises its own answers.

**Why this priority**: This is the core intervention of the research. Without the dialogue data, the comparison between static and Socratic training cannot occur.

**Independent Test**: Run the generation script on a small subset (e.g., 50 samples) and verify the output files contain both static tuples and dialogue tuples with critique fields populated.

**Acceptance Scenarios**:

1. **Given** a source QA dataset (e.g., GSM8K), **When** the generation script processes a sample, **Then** it outputs a static tuple (question, answer).
2. **Given** a source QA dataset, **When** the generation script processes a sample in dialogue mode, **Then** it outputs a dialogue tuple (question, initial_answer, critique, revised_answer).
3. **Given** a generated dialogue tuple, **When** inspected, **Then** the critique section explicitly addresses the reliability or logic of the initial_answer (per Turing/Kahneman feedback on over-confidence).

---

### User Story 2 - CPU-Constrained Fine-Tuning and Evaluation (Priority: P2)

The system MUST fine-tune the base model on both datasets using LoRA and evaluate performance on held-out reasoning benchmarks within the free-tier compute limits.

**Why this priority**: This validates the learning signal. It is the primary experimental step that links data generation to downstream performance.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

**Acceptance Scenarios**:

1. **Given** the Static training dataset, **When** training runs for 3 epochs, **Then** the process completes without OOM errors and within 6 hours.
2. **Given** the Dialogue training dataset, **When** training runs for 3 epochs, **Then** the process completes without OOM errors and within 6 hours.
3. **Given** a fine-tuned model, **When** evaluated on GSM8K test split, **Then** accuracy is recorded and logged.

---

### User Story 3 - Statistical Analysis and Ablation (Priority: P3)

The system MUST perform statistical comparison between the two conditions and ablate the self-critique component to isolate its effect.

**Why this priority**: This establishes the validity of the "Socratic" contribution. Without ablation, we cannot claim the critique loop is the source of improvement.

**Independent Test**: Run the analysis script on the logged metrics from 5 seeds and verify the statistical test output.

**Acceptance Scenarios**:

1. **Given** accuracy results from 5 seeds per condition, **When** a paired t-test is run, **Then** a p-value is generated.
2. **Given** results from the ablation run (question → answer only), **When** compared to the full dialogue condition, **Then** the difference in accuracy is reported.
3. **Given** multiple benchmark results (e.g., GSM8K and MMLU), **When** significance is assessed, **Then** a multiple-comparison correction is applied.

---

### Edge Cases

- **What happens when** the model generation fails or times out during dialogue creation?
  - **System handles** this by retrying the generation up to 3 times before skipping the sample and logging a warning.
- **How does system handle** Out-of-Memory (OOM) errors during fine-tuning on the 7GB RAM runner?
  - **System handles** this by falling back to a smaller model size (e.g., 1.5B parameters) or higher quantization (4-bit) as defined in Assumptions.
- **What happens when** the critique loop enters a degenerate state (repeating the same text)?
  - **System handles** this by detecting repetition (n-gram overlap > 0.9) and truncating the dialogue after 2 turns.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate static QA tuples and dialogue tuples (question, answer, critique, revised_answer) from source datasets (e.g., GSM8K, MATH) using the base model. (See US-1)
- **FR-002**: System MUST include a reliability assessment step in the critique phase where the model evaluates confidence or evidence for its initial answer. (See US-1)
- **FR-003**: System MUST fine-tune both datasets using LoRA with a maximum of 3 epochs and a batch size ≤ 8 on a CPU-only runner. (See US-2)
- **FR-004**: System MUST evaluate fine-tuned models on held-out benchmarks (GSM8K test split, MMLU STEM subset) and log accuracy. (See US-2)
- **FR-005**: System MUST run the experiment with at least 5 random seeds per condition to enable statistical power analysis. (See US-3)
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) when testing significance across ≥ 2 benchmarks. (See US-3)
- **FR-007**: System MUST implement an ablation condition that omits the critique/revision step (question → answer only) to isolate the self-critique effect. (See US-3)
- **FR-008**: System MUST enforce a hard timeout of a predefined duration per training job to comply with CI limits. (See US-2)

### Key Entities

- **Dialogue Tuple**: A structured record containing the prompt, initial response, self-critique text, and revised response.
- **Training Condition**: A label indicating whether the model was trained on Static or Dialogue data.
- **Benchmark Metric**: A quantitative score (e.g., accuracy %) on a held-out test set.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dialogue-condition accuracy is measured against Static-condition accuracy on the same benchmark. (See US-2)
- **SC-002**: Statistical significance (p-value) is measured against a threshold of 0.05 with correction for multiple comparisons. (See US-3)
- **SC-003**: Total compute time per training job is measured against the 6-hour limit. (See US-2)
- **SC-004**: Sensitivity of the error-threshold mechanism is measured against a sweep of values {0.01, 0.05, 0.1} as per Turing's suggestion. (See US-3)

## Assumptions

- The base model weights are available in a quantized format (e.g., 4-bit GGUF or equivalent CPU-compatible loader) that fits within 7 GB RAM, as full 7B FP16 weights exceed runner capacity.
- HuggingFace Datasets (`gsm8k`, `MATH`, `HumanEval`) are accessible via standard API without authentication restrictions during the CI window.
- The GitHub Actions free-tier runner provides at least 2 CPU cores and ~7 GB RAM as specified.
- The self-critique mechanism distinguishes instruction acquisition from memorization by requiring a prediction error exceeding a threshold (e.g., 0.05) before updating internal representations, per Turing's feedback.
- The Socratic dialogue generation does not require GPU acceleration; CPU inference latency is acceptable for the dataset size (≤ 500 samples).
- The "reliability assessment" in the critique phase (FR-002) will be implemented via a prompt instruction rather than a learned confidence head, to maintain model-agnostic design.
- [NEEDS CLARIFICATION: Does the chosen 4-bit quantization library support CPU-only training without CUDA dependencies?]
- [NEEDS CLARIFICATION: Is the 7B parameter size strictly required, or can a 1.5B/3B parameter model suffice for the CPU feasibility constraint?]
- [NEEDS CLARIFICATION: What is the specific community-standard basis for the error-threshold value (e.g., 0.05) used in the ablation sensitivity analysis?]
