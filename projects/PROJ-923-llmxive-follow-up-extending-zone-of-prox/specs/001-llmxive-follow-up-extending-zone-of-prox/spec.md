# Feature Specification: llmXive Follow-up: Extending "Zone of Proximal Policy Optimization: Teacher in Prompts, Not Gradient"

**Feature Branch**: `001-llmxive-zppo-extension`  
**Created**: 2026-08-02  
**Status**: Draft  
**Input**: User description: "How does dynamically pruning negative candidates based on student confidence affect the data efficiency and generalization to novel error modes of prompt-based distillation, compared to a static negative candidate set?"

## User Scenarios & Testing

### User Story 1 - Static Baseline Simulation (Priority: P1)

The system must simulate the original Zone of Proximal Policy Optimization (ZPPO) training loop using a static Negative Candidate-included Question (NCQ) prompt to establish a baseline convergence curve.

**Why this priority**: This is the foundational control condition. Without a verified static baseline, no comparison can be made to determine if the dynamic pruning strategy offers any benefit. It validates the data ingestion and the core training loop logic before introducing complexity.

**Independent Test**: The system can be fully tested by loading the generated synthetic rollout log, running the static NCQ generation for all buffer cycles, and outputting a convergence curve (accuracy vs. cycles) that matches the expected behavior of the original ZPPO paper (within statistical variance).

**Acceptance Scenarios**:

1. **Given** a generated synthetic rollout log containing student model responses for 10 LLM and VLM tasks, **When** the static ZPPO simulation runs with a fixed NCQ prompt containing all known failure modes, **Then** the system outputs a convergence curve showing accuracy increasing over buffer cycles, serving as the control group.
2. **Given** the static simulation completes, **When** the final accuracy is recorded on held-out test data (consisting of tasks *not* in the rollout log), **Then** the result is stored as the `baseline_accuracy` metric for later comparison.

---

### User Story 2 - Confidence-Adaptive Pruning (CAP) Implementation (Priority: P2)

The system must implement the CAP mechanism that dynamically prunes "consistently rejected" negative candidates from the NCQ prompt based on the student's historical confidence scores.

**Why this priority**: This is the core innovation of the feature. It directly addresses the research question regarding cognitive load management and data efficiency. Without this, the "dynamic" aspect of the study cannot be tested.

**Independent Test**: The system can be fully tested by running the CAP-ZPPO loop on the same data, verifying that the NCQ prompt content changes at each step (specifically, that candidates with confidence < configurable threshold are excluded), and that the resulting convergence curve is distinct from the static baseline.

**Acceptance Scenarios**:

1. **Given** the student model's confidence scores for negative candidates from previous buffer cycles, **When** the CAP mechanism calculates the mean and variance for each candidate, **Then** candidates with confidence below a configurable threshold are excluded, candidates with confidence above a configurable threshold are excluded as 'mastered', and candidates with confidence within the intermediate range are retained.
2. **Given** a specific training step where the student has mastered a specific error mode, **When** the CAP-ZPPO loop generates the prompt, **Then** the prompt length is reduced compared to the static baseline, containing only the proximal error modes the student currently struggles with.

---

### User Story 3 - Comparative Statistical Analysis (Priority: P3)

The system must perform a statistical comparison between the static baseline and the CAP-ZPPO variant to determine differences in data efficiency (Area Under the Convergence Curve) and final performance.

**Why this priority**: This provides the empirical evidence required to answer the research question. It transforms the simulation outputs into a scientific conclusion regarding the efficacy of the dynamic pruning strategy.

**Independent Test**: The system can be fully tested by executing the paired t-test on the Area Under the Convergence Curve (AUCC) data from the two variants (generated across 100 random runs) and generating a report that explicitly states whether the CAP variant achieves a significantly higher AUCC.

**Acceptance Scenarios**:

1. **Given** the convergence curves (accuracy vs. buffer cycles) for both the static and CAP variants across 10 selected tasks and 10 random seeds per task (100 total runs), **When** the statistical analysis module runs a paired t-test, **Then** the system outputs the p-value and the difference in AUCC between the two variants.
2. **Given** the final accuracy metrics for both variants, **When** the analysis checks for catastrophic forgetting on held-out test data, **Then** the system reports whether the final accuracy of the CAP variant is comparable to or exceeds the static baseline.

### Edge Cases

- **What happens when** the student model's confidence is uniformly low or uniformly high across all candidates? (The system must handle edge cases where no candidates are pruned or all are pruned, defaulting to the full set or a minimal set to avoid empty prompts).
- **How does the system handle** a scenario where the generated rollout log is missing specific tasks or has corrupted confidence data? (The system must fail gracefully with a clear error message indicating the missing data source).
- **What happens when** the dynamic pruning leads to a prompt with zero negative candidates? (The system must enforce a minimum prompt size or fallback to the static set to ensure the training signal remains valid).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load and parse the generated synthetic rollout log containing student model responses and confidence scores for the specified set of tasks, including both LLM and VLM modalities. (See US-1)
- **FR-002**: System MUST implement a static NCQ generator that includes all known failure modes for every training step to establish the baseline. (See US-1)
- **FR-003**: System MUST calculate the mean confidence and variance for each negative candidate across historical buffer cycles to classify them as "consistently rejected" (< configurable threshold, default 0.1), "fluctuating" ([configurable threshold, 1-configurable threshold], default [0.1, 0.9]), or "consistently accepted" (> configurable threshold, default 0.9). Candidates classified as "consistently accepted" are excluded from the prompt as they represent mastered error modes, aligning with Constitution Principle VI which defines the proximal zone strictly as the fluctuating range. (See US-2)
- **FR-004**: System MUST dynamically generate the NCQ prompt for each step by excluding candidates classified as "consistently rejected" or "consistently accepted", retaining only "fluctuating" candidates. (See US-2)
- **FR-005**: System MUST execute a paired t-test to compare the Area Under the Convergence Curve (AUCC) over multiple cycles between the static and CAP variants. (See US-3)
- **FR-006**: System MUST record the final accuracy of both variants on held-out test data (unseen tasks) to verify that pruning does not lead to performance degradation. (See US-3)
- **FR-007**: System MUST enforce a minimum threshold of negative candidates in the prompt to prevent empty prompts during high-confidence phases. (See US-2)
- **FR-008**: System MUST run the simulation multiple times with distinct random seeds to generate a distribution of convergence curves, where the seed controls the sampling of log entries and injects Gaussian noise (σ=0.05) into the confidence scores at each step to ensure statistical variance. (See US-3)

### Key Entities

- **Rollout Log**: A dataset containing the history of student model responses, confidence scores, and ground truth labels for the 10 selected tasks.
- **Negative Candidate**: A specific failure mode or error type included in the NCQ prompt, characterized by its historical confidence score.
- **Training Buffer Cycle**: A discrete iteration in the simulation where the student model processes a batch of prompts and updates its internal state (simulated).
- **Convergence Curve**: A time-series representation of the student model's accuracy over buffer cycles.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in Area Under the Convergence Curve (AUCC) over 50 cycles between CAP and Static variants is measured against the baseline static convergence curve. (See US-3)
- **SC-002**: The Standard Deviation of the AUCC over 50 cycles between CAP and Static variants is measured against the baseline static convergence curve. (See US-3)
- **SC-003**: The final accuracy of the CAP variant is measured against the final accuracy of the static baseline on held-out test data to detect catastrophic forgetting. (See US-3)
- **SC-004**: The statistical significance (p-value) of the AUCC difference is measured against the standard alpha threshold of 0.05. (See US-3)
- **SC-005**: The average prompt length (number of negative candidates) during mid-training steps (defined as the interval from cycle 20 to cycle 40 of total cycles) is measured against the static baseline to verify cognitive load reduction. (See US-2)
- **SC-006**: The baseline convergence curve (accuracy vs. cycles) is measured against the expected behavior of the original ZPPO paper to validate the control condition. (See US-1)

## Assumptions

- The rollout log is generated at runtime via a stochastic simulation engine using a synthetic probability generator seeded by the spec, rather than being loaded from a pre-computed static file. This ensures the student state can evolve dynamically based on the pruning intervention.
- The analysis will run on a CPU-only environment (GitHub Actions free tier) using Python libraries (e.g., `scikit-learn`, `pandas`, `numpy`) without GPU acceleration.
- The "consistently rejected" classification threshold (ε) is a configurable parameter with a default value of 0.1, and the "consistently accepted" threshold (1-ε) is 0.9, as defined in Constitution Principle VI.
- A representative set of tasks spanning both LLM and VLM domains is selected to ensure sufficient statistical power in a paired t-test when combined with multiple random seeds.
- The simulation uses a stochastic update rule seeded by the pre-computed logs, where the random seed controls the sampling of log entries and injects Gaussian noise (σ=0.05) into the confidence scores at each step, ensuring variance in convergence curves.
- The held-out test data consists of tasks *not* present in the rollout log (specifically, MMLU dataset tasks with negative candidates generated synthetically based on the task schema), ensuring no data leakage or circular validation.
- The static ZPPO baseline behavior in the simulation will closely match the original paper's reported convergence rates, assuming the same hyperparameters and data.
- The "cognitive load" of the student model is inversely proportional to the number of negative candidates in the prompt. This hypothesis is validated by measuring the correlation between prompt length and student confidence variance across multiple runs.
- The study is a proof-of-concept simulation to validate the *algorithm's behavior* under controlled conditions. The synthetic ground truth is derived from a separate, fixed "expert model" confidence distribution, ensuring the student's learning update is based on the difference between its own confidence and the expert's confidence, breaking circularity.