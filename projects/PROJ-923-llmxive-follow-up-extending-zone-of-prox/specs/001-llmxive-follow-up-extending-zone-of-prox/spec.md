# Feature Specification: llmXive Follow-up: Extending "Zone of Proximal Policy Optimization: Teacher in Prompts, Not Gradient"

**Feature Branch**: `001-llmxive-zppo-extension`  
**Created**: 2026-08-02  
**Status**: Draft  
**Input**: User description: "How does dynamically pruning negative candidates based on student confidence affect the data efficiency and generalization to novel error modes of prompt-based distillation, compared to a static negative candidate set?"

## User Scenarios & Testing

### User Story 1 - Static Baseline Simulation (Priority: P1)

The system must simulate the original Zone of Proximal Policy Optimization (ZPPO) training loop using a static Negative Candidate-included Question (NCQ) prompt to establish a baseline convergence curve.

**Why this priority**: This is the foundational control condition. Without a verified static baseline, no comparison can be made to determine if the dynamic pruning strategy offers any benefit. It validates the data ingestion and the core training loop logic before introducing complexity.

**Independent Test**: The system can be fully tested by loading the pre-computed rollout log, running the static NCQ generation for all buffer cycles, and outputting a convergence curve (accuracy vs. cycles) that matches the expected behavior of the original ZPPO paper (within statistical variance).

**Acceptance Scenarios**:

1. **Given** a pre-computed rollout log containing student model responses for 5 LLM and 5 VLM tasks, **When** the static ZPPO simulation runs with a fixed NCQ prompt containing all known failure modes, **Then** the system outputs a convergence curve showing accuracy increasing over buffer cycles, serving as the control group.
2. **Given** the static simulation completes, **When** the final accuracy is recorded on held-out test data (consisting of tasks *not* in the rollout log), **Then** the result is stored as the `baseline_accuracy` metric for later comparison.

---

### User Story 2 - Confidence-Adaptive Pruning (CAP) Implementation (Priority: P2)

The system must implement the CAP mechanism that dynamically prunes "consistently rejected" negative candidates from the NCQ prompt based on the student's historical prediction probabilities.

**Why this priority**: This is the core innovation of the feature. It directly addresses the research question regarding cognitive load management and data efficiency. Without this, the "dynamic" aspect of the study cannot be tested.

**Independent Test**: The system can be fully tested by running the CAP-ZPPO loop on the same data, verifying that the NCQ prompt content changes at each step (specifically, that candidates with probability < 0.1 are excluded), and that the resulting convergence curve is distinct from the static baseline.

**Acceptance Scenarios**:

1. **Given** the student model's prediction probabilities for negative candidates from previous buffer cycles, **When** the CAP mechanism calculates the mean and variance for each candidate, **Then** candidates with probability < 0.1 ("consistently rejected") are excluded, candidates with probability > 0.9 ("consistently accepted") are retained but marked, and candidates with probability in [0.1, 0.9] ("fluctuating") are retained.
2. **Given** a specific training step where the student has mastered a specific error mode, **When** the CAP-ZPPO loop generates the prompt, **Then** the prompt length is reduced compared to the static baseline, containing only the proximal error modes the student currently struggles with.

---

### User Story 3 - Comparative Statistical Analysis (Priority: P3)

The system must perform a statistical comparison between the static baseline and the CAP-ZPPO variant to determine differences in data efficiency (cycles to target accuracy) and final performance.

**Why this priority**: This provides the empirical evidence required to answer the research question. It transforms the simulation outputs into a scientific conclusion regarding the efficacy of the dynamic pruning strategy.

**Independent Test**: The system can be fully tested by executing the paired t-test on the convergence data from the two variants (generated across 10 random seeds) and generating a report that explicitly states whether the CAP variant achieves target accuracy in significantly fewer cycles.

**Acceptance Scenarios**:

1. **Given** the convergence curves (accuracy vs. buffer cycles) for both the static and CAP variants across 10 selected tasks and 10 random seeds, **When** the statistical analysis module runs a paired t-test, **Then** the system outputs the p-value and the difference in cycles required to reach [deferred] and [deferred] accuracy.
2. **Given** the final accuracy metrics for both variants, **When** the analysis checks for catastrophic forgetting on held-out test data, **Then** the system reports whether the final accuracy of the CAP variant is comparable to or exceeds the static baseline.

### Edge Cases

- **What happens when** the student model's confidence is uniformly low or uniformly high across all candidates? (The system must handle edge cases where no candidates are pruned or all are pruned, defaulting to the full set or a minimal set to avoid empty prompts).
- **How does the system handle** a scenario where the pre-computed rollout log is missing specific tasks or has corrupted probability data? (The system must fail gracefully with a clear error message indicating the missing data source).
- **What happens when** the dynamic pruning leads to a prompt with zero negative candidates? (The system must enforce a minimum prompt size or fallback to the static set to ensure the training signal remains valid).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and parse the pre-computed rollout log containing student model responses and prediction probabilities for the specified set of tasks, including both LLM and VLM modalities. (See US-1)
- **FR-002**: System MUST implement a static NCQ generator that includes all known failure modes for every training step to establish the baseline. (See US-1)
- **FR-003**: System MUST calculate the mean prediction probability and variance for each negative candidate across historical buffer cycles to classify them as "consistently rejected" (< 0.1), "fluctuating" ([0.1, 0.9]), or "consistently accepted" (> 0.9). (See US-2)
- **FR-004**: System MUST dynamically generate the NCQ prompt for each step by excluding candidates classified as "consistently rejected" while retaining "fluctuating" and "consistently accepted" candidates. (See US-2)
- **FR-005**: System MUST execute a paired t-test to compare the number of buffer cycles required to reach a high threshold of accuracy between the static and CAP variants. (See US-3)
- **FR-006**: System MUST record the final accuracy of both variants on held-out test data (unseen tasks) to verify that pruning does not lead to performance degradation. (See US-3)
- **FR-007**: System MUST enforce a minimum threshold of negative candidates in the prompt to prevent empty prompts during high-confidence phases. (See Edge Cases)
- **FR-008**: System MUST run the simulation multiple times with distinct random seeds to generate a distribution of convergence curves, where the seed controls the sampling of log entries and noise injection in the update rule. (See US-3)

### Key Entities

- **Rollout Log**: A dataset containing the history of student model responses, prediction probabilities, and ground truth labels for the 10 selected tasks.
- **Negative Candidate**: A specific failure mode or error type included in the NCQ prompt, characterized by its historical rejection probability.
- **Training Buffer Cycle**: A discrete iteration in the simulation where the student model processes a batch of prompts and updates its internal state (simulated).
- **Convergence Curve**: A time-series representation of the student model's accuracy over buffer cycles.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in buffer cycles required to reach [deferred] accuracy between CAP and Static variants is measured against the baseline static convergence curve. (See US-3)
- **SC-002**: The difference in buffer cycles required to reach [deferred] accuracy between CAP and Static variants is measured against the baseline static convergence curve. (See US-3)
- **SC-003**: The final accuracy of the CAP variant is measured against the final accuracy of the static baseline on held-out test data to detect catastrophic forgetting. (See US-3)
- **SC-004**: The statistical significance (p-value) of the cycle difference is measured against the standard alpha threshold of 0.05. (See US-3)
- **SC-005**: The average prompt length (number of negative candidates) during mid-training steps (defined as the interval from [deferred] to [deferred] of total cycles to target) is measured against the static baseline to verify cognitive load reduction. (See US-2)
- **SC-006**: The baseline convergence curve (accuracy vs. cycles) is measured against the expected behavior of the original ZPPO paper to validate the control condition. (See US-1)

## Assumptions

- The pre-computed rollout log from the original ZPPO paper (or a simulated equivalent using a frozen student model on a representative set of LLM and VLM tasks) is available and contains valid prediction probabilities for all negative candidates.
- The analysis will run on a CPU-only environment (GitHub Actions free tier) using Python libraries (e.g., `scikit-learn`, `pandas`, `numpy`) without GPU acceleration.
- The "consistently rejected" classification threshold ($\epsilon$) is set to a fixed value determined by community standards for high-confidence rejection in similar distillation tasks.
- A representative set of tasks spanning both LLM and VLM domains is selected to ensure sufficient statistical power in a paired t-test when combined with multiple random seeds.
- The simulation uses a stochastic update rule seeded by the pre-computed logs, where the random seed controls the sampling of log entries and noise injection, ensuring variance in convergence curves.
- The held-out test data consists of tasks *not* present in the rollout log, ensuring no data leakage or circular validation.
- The static ZPPO baseline behavior in the simulation will closely match the original paper's reported convergence rates, assuming the same hyperparameters and data.
- The "cognitive load" of the student model is inversely proportional to the number of negative candidates in the prompt, a hypothesis that the simulation will test but is assumed for the purpose of the pruning logic design.