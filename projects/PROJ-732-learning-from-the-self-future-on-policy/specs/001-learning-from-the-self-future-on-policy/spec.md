# Feature Specification: Learning from the Self-future: On-policy Self-distillation for dLLMs

**Feature Branch**: `[001-on-policy-self-distillation-dLLMs]`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "How does incorporating on‑policy self‑distillation during training affect the reasoning accuracy and sample‑efficiency of diffusion language models on standard benchmark tasks?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Implement OPSD Training Pipeline (Priority: P1)

A researcher can train a diffusion language model using on-policy self-distillation (OPSD) as an alternative to standard diffusion loss, enabling comparison against baseline fine-tuning.

**Why this priority**: This is the core research intervention; without a working OPSD training pipeline, no downstream evaluation or comparison is possible.

**Independent Test**: Can be fully tested by running the training script on a small held-out subset and verifying that the loss converges without GPU acceleration.

**Acceptance Scenarios**:

1. **Given** a diffusion model checkpoint and training dataset, **When** the OPSD training script is executed with λ=0.5, **Then** the training loop completes within 6 hours on a CPU-only runner and produces a student checkpoint.
2. **Given** identical dataset splits and random seeds, **When** OPSD and baseline training are run separately, **Then** both produce checkpoints of comparable file size (±10%) and training duration (±15%).
3. **Given** a training batch, **When** the self-teacher generates outputs, **Then** the KL divergence loss is computed and combined with the original diffusion loss at the specified weight λ.

---

### User Story 2 - Benchmark Evaluation Suite (Priority: P2)

A researcher can evaluate both baseline and OPSD-trained models on GSM8K, MATH, Sudoku, and Countdown using pass@k metrics and sample-efficiency measurements.

**Why this priority**: Evaluation is required to answer the research question; without standardized metrics, improvements cannot be quantified.

**Independent Test**: Can be fully tested by running the evaluation script on a pre-trained checkpoint and verifying that pass@k scores are computed for k∈{1,5,10}.

**Acceptance Scenarios**:

1. **Given** a trained model checkpoint and test split, **When** the evaluation script is executed with seed=42, **Then** pass@k scores are generated for all k∈{1,5,10} within 2 hours.
2. **Given** multiple diffusion steps (T=10,20,[deferred]), **When** sample-efficiency analysis is run, **Then** the number of steps required to reach [deferred] of final pass@1 score is recorded for each model.
3. **Given** three independent training runs with seeds {[deferred]6}, **When** evaluation is aggregated, **Then** mean and standard deviation of pass@k are computed across seeds.

---

### User Story 3 - Statistical Significance Testing (Priority: P3)

A researcher can perform bootstrap resampling and paired significance tests to determine whether OPSD improvements are statistically distinguishable from baseline performance.

**Why this priority**: Statistical validation is necessary to support claims about method effectiveness; null results must also be interpretable.

**Independent Test**: Can be fully tested by running the statistical analysis script on evaluation results and verifying confidence intervals and p-values are produced.

**Acceptance Scenarios**:

1. **Given** pass@k scores from baseline and OPSD runs, **When** bootstrap resampling (a sufficient number of samples) is executed, **Then** 95% confidence intervals are computed for the mean difference.
2. **Given** paired results across three seeds, **When** a paired significance test is run, **Then** a p-value is reported with p<0.05 threshold for significance.
3. **Given** multiple benchmark tasks (4 tasks), **When** family-wise error is considered, **Then** a multiple-comparison correction (Bonferroni or Benjamini-Hochberg) is applied and documented.

---

### Edge Cases

- What happens when the diffusion model produces token distributions with near-zero entropy (KL divergence becomes unstable)?
- How does the system handle dataset samples that fail to parse or contain malformed answers (e.g., MATH problems with LaTeX errors)?
- What happens when the self-teacher generates outputs that are identical to the student (KL divergence = 0, no distillation signal)?
- How does the system handle out-of-memory conditions during batch processing on the 7 GB RAM limit?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download GSM8K, MATH, Sudoku, and Countdown datasets from their official HuggingFace mirrors and cache them locally (See US-1)
- **FR-002**: System MUST implement on-policy self-distillation training that computes step-wise KL divergence between teacher and student token distributions at each diffusion step (See US-1)
- **FR-003**: System MUST combine the KL loss with the original diffusion loss using weight λ=0.5, with sensitivity analysis sweeping λ∈{0.3, 0.5, 0.7} (See US-1)
- **FR-004**: System MUST evaluate models on held-out test splits using ancestral sampling with fixed random seeds to compute pass@k for k∈{1,5,10} (See US-2)
- **FR-005**: System MUST measure sample-efficiency by recording the number of diffusion steps required to reach [deferred] of the final pass@1 score (See US-2)
- **FR-006**: System MUST perform bootstrap resampling with 10,000 samples to compute 95% confidence intervals for performance metrics (See US-3)
- **FR-007**: System MUST apply multiple-comparison correction when evaluating across four benchmark tasks to control family-wise error rate (See US-3)
- **FR-008**: System MUST run all training and evaluation on CPU-only infrastructure without GPU/CUDA dependencies (See US-1)
- **FR-009**: System MUST limit total compute time per job to ≤6 hours and memory usage to ≤7 GB RAM (See US-1)
- **FR-010**: System MUST log random seeds (42, 123, 2026) and use them for three independent runs per condition (See US-2)

### Key Entities

- **Model Checkpoint**: Represents a trained diffusion language model state, including weights and optimizer state; key attributes are parameter count (≈150M), training condition (baseline vs OPSD), and random seed.
- **Benchmark Result**: Represents evaluation output for a single model on a single task; key attributes are pass@k scores for k∈{1,5,10}, diffusion steps to [deferred] performance, and seed identifier.
- **Training Configuration**: Represents the hyperparameter set controlling training behavior; key attributes are loss weight λ, number of diffusion steps T, batch size, and epoch count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Training completion rate is measured against the 6-hour time budget and 7 GB RAM limit (See US-1)
- **SC-002**: Pass@k score difference between OPSD and baseline is measured against the bootstrap 95% confidence interval (See US-3)
- **SC-003**: Sample-efficiency improvement is measured against the number of diffusion steps required to reach [deferred] of final pass@1 score (See US-2)
- **SC-004**: Statistical significance is measured against p<0.05 threshold with multiple-comparison correction applied (See US-3)
- **SC-005**: Reproducibility is measured against consistency across three independent runs with seeds {42, 123, 2026} (See US-2)

## Assumptions

- The diffusion-gpt-small model (compact parameter scale) from HuggingFace is accessible via the public API and compatible with CPU-only inference
- Dataset samples that fail to parse (e.g., malformed MATH LaTeX) will be excluded from evaluation rather than causing pipeline failure
- The [NEEDS CLARIFICATION: does the diffusion-gpt-small model support the vocabulary required for GSM8K/MATH numerical outputs?]
- Observational comparison between baseline and OPSD training conditions will frame performance differences as associational rather than causal
- Family-wise error correction will use Benjamini-Hochberg procedure for four benchmark tasks (α=0.05)
- The 150M parameter model will fit within 7 GB RAM when using default precision (float32) without 8-bit or 4-bit quantization
- Sensitivity analysis for λ will sweep {0.3, 0.5, 0.7} with step size 0.2, reporting how pass@1 varies across thresholds
- Power considerations for the bootstrap test are deferred to implementation; the design acknowledges potential limitations with only three seeds per condition
- All citations are verbatim from the idea markdown; no fabricated URLs or citations are introduced
