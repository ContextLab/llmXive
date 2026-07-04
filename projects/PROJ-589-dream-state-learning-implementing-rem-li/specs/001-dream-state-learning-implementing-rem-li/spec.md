# Feature Specification: Dream-State Learning: Implementing REM-like Consolidation in Language Models

**Feature Branch**: `001-dream-state-learning-rem-consolidation`  
**Created**: 2026-05-28  
**Status**: Draft  
**Input**: User description: "Dream-State Learning: Implementing REM-like Consolidation in Language Models"

## User Scenarios & Testing

### User Story 1 - Core Wake/Dream Training Cycle (Priority: P1)

**Description**: As a researcher, I want to train a small language model using an alternating schedule of "wake" (standard supervised fine-tuning) and "dream" (generative replay with noise) phases so that I can measure if this bio-inspired schedule improves few-shot generalization compared to continuous training.

**Why this priority**: This is the fundamental mechanism being tested. Without a functional implementation of the alternating cycle, no comparison or hypothesis testing is possible. It delivers the primary experimental capability.

**Independent Test**: Can be fully tested by running a 100-step training job on a single GLUE subset, verifying that the model alternates between loss calculation on real data and loss calculation on generated pseudo-samples, and outputs a final checkpoint.

**Acceptance Scenarios**:
1. **Given** a small transformer model (≤100M params) and a GLUE subset, **When** the training loop executes 100 steps with a 4:1 wake-to-dream ratio, **Then** the system must generate pseudo-samples during exactly 20 of those steps and update weights on both real and generated data.
2. **Given** the same setup, **When** the training completes, **Then** the final model checkpoint must exist and be loadable for downstream evaluation without errors.

---

### User Story 2 - Comparative Evaluation Baseline (Priority: P2)

**Description**: As a researcher, I want to run a parallel continuous-training baseline with identical total token exposure so that I can isolate the effect of the consolidation phases from general training progress.

**Why this priority**: A positive result is meaningless without a controlled comparison. This ensures the observed effect is due to the "dream" mechanism, not just the passage of training time or data volume.

**Independent Test**: Can be tested by running the baseline script on the same dataset and seed, then comparing the final loss and accuracy metrics against the wake/dream run.

**Acceptance Scenarios**:
1. **Given** a specific random seed and dataset split, **When** the baseline script runs for the same number of steps as the experimental run, **Then** the baseline must consume the exact same number of real training tokens as the experimental run.
2. **Given** both models are trained, **When** evaluated on the held-out few-shot task, **Then** the system must output a comparative report showing the accuracy difference and the paired t-test p-value.

---

### User Story 3 - Resource Constraint Verification (Priority: P3)

**Description**: As a project maintainer, I want the training script to automatically verify it fits within the GitHub Actions free-tier limits (2 CPU, 7GB RAM, 6h time) so that the experiment is reproducible without specialized hardware.

**Why this priority**: The project's feasibility depends entirely on running in this constrained environment. If the method requires GPU or excessive RAM, the research cannot be executed.

**Independent Test**: Can be tested by running the script on a local machine with resource limiting (e.g., `ulimit` or Docker) or a CI runner, verifying no OOM errors occur and execution time stays under the threshold.

**Acceptance Scenarios**:
1. **Given** the training script is launched on a CPU-only environment with 7GB RAM, **When** the script runs, **Then** the peak memory usage must not exceed 6.5 GB.
2. **Given** the full experimental pipeline (training + evaluation), **When** executed on a standard CI runner, **Then** the total wall-clock time must complete within 5 hours.

---

### Edge Cases

- **What happens when** the generated pseudo-samples are nonsensical or collapse to a single token? The system must detect low-entropy outputs (average entropy < 0.5 bits per token) during the dream phase and trigger a re-sampling retry up to 3 times before discarding the batch to prevent training on garbage data.
- **How does the system handle** a scenario where the model has not learned enough during the wake phase to generate meaningful pseudo-samples in the first dream cycle? The system must implement a "warm-up" period of 10 wake-only steps before enabling the dream phase.
- **What happens when** the few-shot evaluation task has insufficient samples for a statistically significant t-test (n < 5)? The system must flag the result as "insufficient power" and report the observed effect size without claiming statistical significance if the held-out evaluation set contains fewer than 5 samples for a specific seed.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a training loop that alternates between "wake" phases (standard cross-entropy on real data) and "dream" phases (generative replay with masked inputs) with a fixed 4:1 step ratio (See US-1).
- **FR-002**: System MUST generate pseudo-samples during dream phases using the current model state with a temperature of 0.7 and apply random token masking (masking [deferred] of tokens, consistent with standard BERT masking strategies) before retraining on the original input for reconstruction (See US-1).
- **FR-003**: System MUST run a parallel baseline training job using continuous supervised fine-tuning with the exact same total number of gradient steps and data tokens as the experimental run (See US-2).
- **FR-004**: System MUST evaluate both the experimental and baseline models on the same held-out GLUE/SuperGLUE few-shot subsets and compute the accuracy difference (See US-2).
- **FR-005**: System MUST enforce a hard memory limit check that aborts the job if peak RSS (measured via /proc/self/status) exceeds a predefined threshold. (chosen to leave 0.5 GB headroom for OS overhead within the 7 GB environment limit), saves the current model checkpoint and training state to allow reproducible debugging, and logs the peak usage for audit (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis on the dream-phase temperature parameter by sweeping values across a representative range. and reporting the variance in final accuracy to isolate the consolidation effect from generic regularization (See US-1).
- **FR-007**: System MUST implement a "warm-up" protocol that delays the first dream phase until after 10 wake steps to ensure initial representation stability (See US-1).

### Key Entities

- **TrainingCycle**: The sequence of alternating wake and dream steps, defined by the total step count and the wake/dream ratio.
- **PseudoSample**: A synthetic data point generated by the model during the dream phase, containing masked input tokens where the target is the original input tokens for reconstruction.
- **EvaluationMetric**: The accuracy score on the held-out few-shot task, used as the primary outcome variable.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The relative improvement in few-shot accuracy of the Wake/Dream model over the Continuous Baseline is measured against the baseline accuracy (See US-2).
- **SC-002**: The statistical significance of the improvement is measured against a paired t-test threshold of α=0.05 across 5 random seeds (See US-2).
- **SC-003**: The peak memory consumption during training is measured against the predefined system limit to verify CPU-only feasibility. (See US-3).
- **SC-004**: The total wall-clock execution time is measured against a standard time limit per GitHub Actions job. (See US-3).
- **SC-005**: The variance in final accuracy across the temperature sweep {0.5, 0.7, 0.9} is measured to determine the sensitivity of the consolidation mechanism to hyperparameters (See US-1).

## Assumptions

- The HuggingFace `transformers` library version installed in the CI environment supports CPU-only inference and training without requiring CUDA-specific backends.
- The GLUE/SuperGLUE datasets used for few-shot evaluation are small enough (≤1000 samples) to fit entirely in RAM during the evaluation phase.
- The "dream" phase is implemented as a generative replay mechanism using the model's own predictions for input generation, but the training target is the original input (denoising autoencoder style), not a biological simulation of synaptic pruning, which is computationally intractable on CPU.
- The random seed for the experiment is fixed for reproducibility, with multiple additional seeds used for statistical aggregation.
- The model architecture is limited to DistilBERT or TinyLlama (≤100M parameters) to ensure the training loop completes within the 6-hour time budget on a 2-core runner.
- The "temperature" hyperparameter for the dream phase is assumed to be the primary control knob for the "dreaming" intensity, with 0.7 serving as the community-standard default for text generation.
- The memory abort threshold is selected to provide a buffer for operating system overhead within the GitHub Actions runner limit..