# Feature Specification: Socratic Transformers: Dialogue-Based Self-Teaching Through Adversarial Questioning

**Feature Branch**: `582-socratic-transformers-dialogue-based-sel`  
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
3. **Given** a generated dialogue tuple, **When** inspected, **Then** the critique section explicitly identifies logical contradictions or unsupported assumptions in the initial_answer (per Turing/Kahneman feedback on over-confidence and Krakauer on negative selection).

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

**Independent Test**: Run the analysis script on the logged metrics from 10 seeds and verify the statistical test output.

**Acceptance Scenarios**:

1. **Given** accuracy results from 10 seeds per condition, **When** a paired t-test is run, **Then** a p-value is generated.
2. **Given** results from the ablation run (question → answer + neutral text), **When** compared to the full dialogue condition, **Then** the difference in accuracy is reported.
3. **Given** multiple benchmark results (e.g., GSM8K and MMLU), **When** significance is assessed, **Then** a multiple-comparison correction is applied.

---

### Edge Cases

- **What happens when** the model generation fails or times out during dialogue creation?
  - **System handles** this by retrying the generation up to 3 times before skipping the sample and logging a warning.
- **How does system handle** Out-of-Memory (OOM) errors during fine-tuning on the 7GB RAM runner?
  - **System handles** this by falling back to a smaller model size (e.g., 1.5B parameters) or higher quantization (4-bit) as defined in Assumptions.
- **What happens when** the critique loop enters a degenerate state (repeating the same text)?
  - **System handles** this by detecting repetition (n-gram overlap > 0.9) and truncating the dialogue after 2 turns. The system MUST output a structured JSON log line to stdout: `{"event": "DEGENERATE_DIALOGUE_TRUNCATED", "sample_id": "<uuid>", "overlap_score": <float>}`.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate static QA tuples and dialogue tuples (question, answer, critique, revised_answer) from source datasets (e.g., GSM8K, MATH) using the base model. (See US-1)
- **FR-002**: System MUST generate a self-critique that explicitly identifies logical contradictions or unsupported assumptions in the initial answer, serving as a negative selection signal. The output MUST be a structured JSON object containing `confidence_score` (0.0-1.0) and `reasoning_snippet`. (See US-1)
- **FR-003**: System MUST fine-tune both datasets using LoRA with a maximum of 3 epochs, `batch_size ≤ 2`, and `gradient_accumulation_steps = 4` on a CPU-only runner to ensure memory safety within 7GB RAM. (See US-2)
- **FR-004**: System MUST evaluate fine-tuned models on held-out benchmarks (GSM8K test split, MMLU STEM subset) and log accuracy. (See US-2)
- **FR-005**: System MUST run the experiment with at least 10 random seeds per condition to enable robust statistical power analysis. (See US-3)
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) when testing significance across ≥ 2 benchmarks. (See US-3)
- **FR-007**: System MUST implement an ablation condition that omits the critique/revision step by replacing the critique text with neutral placeholder text of equivalent token length. The ablation tuple format MUST be (question, answer, neutral_placeholder). (See US-3)
- **FR-008**: System MUST enforce a hard timeout of 6 hours per training job to comply with CI limits. (See US-2)

### Key Entities

- **Dialogue Tuple**: A structured record containing the prompt, initial response, self-critique text (with confidence_score and reasoning_snippet), and revised response.
- **Training Condition**: A label indicating whether the model was trained on Static, Dialogue, or Ablation data.
- **Benchmark Metric**: A quantitative score (e.g., accuracy %) on a held-out test set.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dialogue-condition accuracy is measured against Static-condition accuracy on the same benchmark. (See US-2)
- **SC-002**: Statistical significance (p-value) is measured against a threshold of 0.05 with correction for multiple comparisons. (See US-3)
- **SC-003**: Total compute time per training job is measured against the 6-hour limit. (See US-2)
- **SC-004**: Sensitivity of the prediction error threshold mechanism is measured against a sweep of values {0.01, 0.05, 0.1} as per Turing's suggestion. (See US-3)

## Assumptions

- The base model weights are available in a quantized format (e.g., 4-bit GGUF or equivalent CPU-compatible loader) that fits within 7 GB RAM, as full 7B FP16 weights exceed runner capacity.
- HuggingFace Datasets (`gsm8k`, `MATH`, `HumanEval`) are accessible via standard API without authentication restrictions during the CI window.
- The GitHub Actions free-tier runner provides at least 2 CPU cores and ~7 GB RAM as specified.
- The system MUST use `bitsandbytes` with the `cpu` backend flag or `llama.cpp` (GGUF format) for 4-bit quantization. Reference: `bitsandbytes` documentation confirms CPU backend support for LoRA fine-tuning; `llama.cpp` is explicitly designed for CPU execution. (See FR-003)
- The system MUST use a 1.5B parameter model (e.g., Phi-1.5 or Mistral-1.5B) for the primary feasibility run to strictly comply with the 7 GB RAM constraint. A 7B parameter model is only permitted if quantized to 4-bit and loaded via `llama.cpp` with strict memory profiling confirming < 7 GB usage; otherwise, the 1.5B model is the default. (See US-2, FR-003)
- The default prediction error threshold value of 0.05 is adopted as a community-standard baseline for detecting significant prediction discrepancies in probabilistic reasoning tasks. This threshold is configurable and will be swept over {0.01, 0.05, 0.1} in the sensitivity analysis (SC-004) to validate robustness. This threshold is distinct from the statistical significance level (alpha ≤ 0.05) used in hypothesis testing. (See US-3, SC-004)
- The "prediction error" used in the self-critique mechanism is proxied by the log-probability of the top token normalized by sequence length. This is a methodological assumption required to generate a scalar error metric for categorical reasoning tasks without a learned confidence head, acknowledging the known limitations of log-prob as a calibrated confidence measure. (See FR-002, SC-004)
- The self-critique mechanism distinguishes instruction acquisition from memorization by requiring a prediction error exceeding the configured threshold before updating internal representations, per Turing's feedback. (See FR-002)