# Feature Specification: llmXive follow-up: extending "MolmoMotion: Forecasting Point Trajectories in 3D with Language Instru"

**Feature Branch**: `001-llmxive-motion-scaling`  
**Created**: 2026-09-05  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'MolmoMotion: Forecasting Point Trajectories in 3D with Language Instru'"

## User Scenarios & Testing

### User Story 1 - Dataset Subsampling and Instruction Synthesis (Priority: P1)

A researcher needs to prepare a computationally feasible dataset by subsampling the MolmoMotion-1M corpus to fit within 7GB RAM limits and generating two distinct instruction modalities (coarse natural language and structured kinematic parameters) for every trajectory instance to enable controlled comparison.

**Why this priority**: Without a valid, memory-constrained dataset and the dual-modality instruction pairs, the core experiment cannot run at all. This is the foundational data engineering step.

**Independent Test**: Can be fully tested by executing the data loading script and verifying that the output contains [deferred] trajectory records, each with two valid instruction modalities (one text, one structured vector/duration), and that the total memory footprint of the loaded data object is ≤ 7GB.

**Acceptance Scenarios**:

1. **Given** the MolmoMotion-1M dataset is available, **When** the subsampling script runs, **Then** [deferred] instances are selected and stored in a memory-efficient format, and the process completes without OOM errors.
2. **Given** a selected trajectory instance, **When** the instruction synthesis module runs, **Then** it produces a "coarse" natural language string (e.g., "move left") and a "structured" kinematic string (e.g., "velocity [-0.5, 0, 0], duration 2s") derived strictly from the ground-truth metadata.

---

### User Story 2 - CPU-Optimized Inference Pipeline Execution (Priority: P2)

A researcher needs to execute the lightweight, non-autoregressive linear projection model on the prepared dataset using both instruction modalities, strictly enforcing CPU-only execution to simulate edge-device constraints and measure the resulting trajectory predictions.

**Why this priority**: This is the core computational experiment. It validates whether the simplified architecture can actually run on free-tier CI resources and generate predictions for analysis.

**Independent Test**: Can be fully tested by running the inference script on a standard GitHub Actions runner (2 CPU, 7GB RAM) and verifying that it processes all [deferred] instances, outputs prediction files, and never attempts to access a GPU device.

**Acceptance Scenarios**:

1. **Given** the subsampled dataset and the non-autoregressive linear projection model, **When** the inference script is executed with `torch.set_device('cpu')`, **Then** all [deferred] predictions are generated within the 6-hour job limit and the script reports zero GPU usage.
2. **Given** a specific trajectory instance, **When** the non-autoregressive linear projection model processes the "coarse" natural language instruction, **Then** it outputs a predicted 3D point sequence that yields a higher Average Trajectory Error (ATE) than the sequence generated when processing the "structured" kinematic instruction for the same ground truth.

---

### User Story 3 - Metric Calculation and Statistical Comparison (Priority: P3)

A researcher needs to calculate the Average Trajectory Error (ATE) for all predictions, then perform a paired t-test to determine if the structured instructions significantly outperform natural language instructions under the reduced capacity model.

**Why this priority**: This transforms raw model outputs into scientific findings, directly answering the research question about the trade-off between instruction precision and model capacity.

**Independent Test**: Can be fully tested by running the analysis script on the generated prediction files and verifying that it outputs a summary table with ATE values for both groups, a calculated p-value from the t-test, and a report on the statistical significance.

**Acceptance Scenarios**:

1. **Given** the ground-truth trajectories and the two sets of predicted trajectories, **When** the metric calculation script runs, **Then** it computes the ATE (in meters) for every instance.
2. **Given** the collected ATE distributions for natural language vs. structured instructions, **When** the statistical test runs, **Then** it produces a p-value and a clear conclusion ("significant" if p < 0.05, else "not significant") regarding the performance gap.

---

### Edge Cases

- What happens if the MolmoMotion-1M dataset download fails or the file is corrupted? (System should retry up to 3 times, then fail fast with a clear error code).
- How does the system handle a trajectory instance where the ground-truth metadata does not allow for unambiguous kinematic parameterization? (The script should log a warning and skip the structured instruction generation for that specific instance, excluding it from the paired test).
- What occurs if the linear projection model produces NaN or Inf values during inference? (The pipeline must detect these values, flag the instance as failed, and exclude it from the final statistical analysis rather than crashing).

## Requirements

### Functional Requirements

- **FR-001**: System MUST subsample the MolmoMotion-1M dataset to [deferred] instances to ensure the data fits within the 7GB RAM constraint of the CI runner (See US-001).
- **FR-002**: System MUST generate two distinct instruction modalities for every trajectory: one coarse natural language description and one structured kinematic specification (velocity vector + duration) derived from ground-truth metadata (See US-001).
- **FR-003**: System MUST execute the inference pipeline using a learned, non-autoregressive linear projection model with `torch.set_device('cpu')` enforced, ensuring no GPU acceleration is used (See US-002).
- **FR-004**: System MUST compute the Average Trajectory Error (ATE) in meters for every prediction against the independent ground-truth 3D points (See US-003).
- **FR-005**: System MUST perform a paired t-test on the ATE distributions between the natural language and structured instruction groups, where pairs are defined as (NL Prediction, Structured Prediction) for the same trajectory instance, to determine statistical significance (See US-003).
- **FR-006**: System MUST record inference latency and peak memory usage for every batch to verify compliance with the 6-hour time and 7GB RAM limits (See US-002).

### Key Entities

- **Trajectory Instance**: A single motion event containing ground-truth 3D point sequences and associated metadata.
- **Instruction Modality**: A representation of the input command, either as a text string (Natural Language) or a structured parameter set (Kinematic).
- **Prediction Output**: The sequence of 3D points generated by the model in response to an instruction.
- **Error Metric**: A quantitative measure (ATE) representing the geometric deviation between prediction and ground truth.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Average Trajectory Error (ATE) for the structured instruction group is measured against the ATE of the natural language group; success is defined as the structured group ATE being lower by at least 5% (See FR-004, FR-005).
- **SC-002**: The statistical significance of the performance gap is measured against the standard alpha threshold of 0.05 using a paired t-test (See FR-005).
- **SC-003**: The memory footprint of the data pipeline is measured against the 7GB RAM limit of the CI runner to ensure feasibility (See FR-001, FR-006).
- **SC-004**: The total execution time of the inference and analysis pipeline is measured against the 6-hour CI job limit to ensure feasibility (See FR-006).
- **SC-005**: The statistical power of the paired t-test is measured against the effect size required to detect a [deferred] ATE reduction with [deferred] samples (See FR-005).

## Assumptions

- The MolmoMotion-1M dataset is publicly available and contains sufficient metadata to derive both coarse natural language descriptions and precise kinematic parameters (velocity, duration) for at least 5,000 instances.
- The "coarse" natural language descriptions generated by the rule-based parser are representative of the ambiguity found in real-world user commands for edge robotics.
- The non-autoregressive linear projection model architecture is sufficient to approximate the "reduced capacity" scenario described in the research question, acting as a learned approximation rather than a deterministic kinematic solver, even though it lacks the full transformer attention mechanisms of the original MolmoMotion model.
- The ground-truth trajectories in the dataset are accurate enough to serve as an independent reference for calculating ATE without significant measurement noise.
- The free-tier GitHub Actions runner provides stable multiple CPU cores and ~7GB RAM for the duration of the job without resource throttling.
- The statistical power of the paired t-test with [deferred] samples is sufficient to detect the expected effect size; the sample size is fixed at [deferred] to balance computational cost and statistical validity.