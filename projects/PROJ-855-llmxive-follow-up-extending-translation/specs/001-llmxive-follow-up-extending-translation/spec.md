# Feature Specification: llmXive follow-up: extending "Translation as a Bridging Action"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Translation as a Bridging Action: Transferring Manipulation Skills fro"

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation & Labeling (Priority: P1)

A researcher needs to generate a dataset of bi-manual manipulation episodes using a CPU-based physics engine, where each episode records only monocular translation trajectories and is labeled with a binary stability outcome (success/failure) derived from physics metrics (tipping angle, slippage).

**Why this priority**: Without a valid dataset containing the specific "translation-only" input and "stability" ground truth, no model training or hypothesis testing can occur. This is the foundational data layer.

**Independent Test**: The system can be tested by running the data generation script and verifying that the output CSV/Parquet files contain exactly the required columns (translation vectors, initial object bounds) and a binary label column, with no rotation or force data present.

**Acceptance Scenarios**:

1. **Given** a configuration for ≥ 5,000 episodes with simplified rigid bodies, **When** the generation script executes on a CPU, **Then** the output dataset contains ≥ 5,000 rows with translation vectors and a binary stability label, and execution completes within 2 hours (a hard sub-constraint of the total 6-hour pipeline budget).
2. **Given** an episode where the simulated object tips beyond the defined threshold, **When** the labeling logic runs, **Then** the corresponding record is marked as "failure" (0) regardless of the translation trajectory shape.
3. **Given** the requirement to discard specific data types, **When** the dataset is inspected, **Then** no columns containing rotation quaternions, joint torques, or force sensor readings exist in the file.

---

### User Story 2 - Lightweight Sequence Model Training (Priority: P2)

A researcher needs to train a lightweight sequence model (constrained to <10M parameters) on the generated dataset to predict stability labels using only translation trajectories, ensuring the entire training process runs within 6 hours on a 2-core CPU with 7GB RAM.

**Why this priority**: This implements the core hypothesis testing mechanism. It must be feasible on free-tier hardware to be actionable.

**Independent Test**: The system can be tested by initiating the training job on a standard GitHub Actions runner (2 CPU, 7GB RAM) and verifying that the job completes without OOM errors, GPU allocation failures, or exceeding the 6-hour time limit.

**Acceptance Scenarios**:

1. **Given** the synthetic dataset and the 4-layer Transformer architecture, **When** training starts on a CPU-only environment, **Then** the process utilizes <7GB RAM and completes within 6 hours.
2. **Given** the constraint to avoid GPU-specific operations, **When** the code executes, **Then** no CUDA or bitsandbytes imports are triggered, and the model runs in default floating-point precision.
3. **Given** the model parameters are capped at <10M, **When** the model summary is printed, **Then** the total parameter count is strictly less than 10,000,000.

---

### User Story 3 - Statistical Validation & Baseline Comparison (Priority: P3)

A researcher needs to statistically validate that the translation-only model's predictive performance is significantly better than a geometry-only baseline using McNemar's test, and verify that the model achieves a ≥ 5% absolute accuracy improvement over the baseline on held-out novel object geometries.

**Why this priority**: This confirms the research hypothesis (that translation signals encode physical constraints) and provides the empirical evidence required for the "research_complete" stage.

**Independent Test**: The system can be tested by running the evaluation script on the held-out test set and verifying the output includes the McNemar's test p-value, the accuracy of both models, and the calculated accuracy difference.

**Acceptance Scenarios**:

1. **Given** the translation-only model's predictions and the geometry-only baseline's predictions for the test set, **When** the statistical test runs, **Then** McNemar's test yields a p-value < 0.05, indicating the translation-only model is significantly better than the geometry-only baseline.
2. **Given** a test set containing object geometries not seen during training, **When** both models predict stability, **Then** the translation-only model achieves an absolute accuracy improvement of ≥ 5% over the geometry-only baseline, with a secondary target of ≥ 80% absolute accuracy on the held-out set.
3. **Given** the requirement for methodological rigor, **When** the results are reported, **Then** the report explicitly states the accuracy difference and p-value without claiming causal inference beyond the associational nature of the observational data.

---

### Edge Cases

- **What happens when** the physics simulation encounters a numerical instability (e.g., object tunneling) causing a crash mid-episode?
 - *Handling*: The generation script must catch the exception, discard the incomplete episode, and log the failure, ensuring the final dataset size is ≥ 5,000 valid episodes by generating replacements.
- **How does the system handle** a scenario where the translation trajectory is identical for both a success and a failure outcome (ambiguous signal)?
 - *Handling*: The model will learn the probability distribution; the evaluation must report the confusion matrix to show if the model is forced to guess. If the accuracy on this ambiguous subset is < 50% (random chance), it is flagged as a measurable limitation of the "translation-only" modality.
- **What happens if** the 6-hour time limit is exceeded during training?
  - *Handling*: The CI job must fail gracefully with a timeout error, and the `Assumptions` section must note that the current hyperparameters (learning rate, batch size) may need reduction to fit the compute box.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a synthetic dataset of bi-manual manipulation episodes using PyBullet, recording only relative wrist translation vectors and initial object bounding box coordinates, while explicitly discarding rotation and force data. (See US-1)
- **FR-002**: System MUST label each generated episode with a binary stability outcome (1=success, 0=failure) based on physics-derived metrics: tipping angle ≥ 15° or slippage distance ≥ 0.02m. (See US-1)
- **FR-003**: System MUST implement a lightweight Transformer encoder with a parameter count constrained to a magnitude suitable for efficient deployment to process translation sequences. (See US-2)
- **FR-004**: System MUST train the model using binary cross-entropy loss on a CPU-only environment without utilizing CUDA, bitsandbytes, or GPU-specific acceleration libraries. (See US-2)
- **FR-005**: System MUST evaluate the trained model on a held-out test set of novel object geometries and compute accuracy, ensuring the process completes within 6 hours on a 2-core CPU runner with 7GB RAM. (See US-2, US-3)
- **FR-006**: System MUST perform McNemar's test to compare the translation-only model against a geometry-only baseline (a model using only initial object bounds), requiring a p-value < 0.05 for statistical significance. (See US-3)
- **FR-007**: System MUST report results associatively, explicitly avoiding causal claims about translation causing stability, acknowledging the observational nature of the data. (See US-3)
- **FR-008**: System MUST perform a sensitivity analysis on the labeling thresholds (tipping angle and slippage distance) by sweeping ±5% around the baseline values and reporting the variance in model accuracy to ensure ground truth robustness. (See US-3)

### Key Entities

- **ManipulationEpisode**: A single data record containing a sequence of translation vectors, initial object bounds, and a binary stability label.
- **StabilityMetric**: A derived value (tipping angle, slippage distance) used to determine the ground-truth label.
- **SequenceModel**: The lightweight Transformer architecture trained to map translation sequences to stability probabilities.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Dataset validity is measured against the requirement of ≥ 5,000 valid episodes with no rotation/force columns, verified by schema inspection. (See FR-001, FR-002)
- **SC-002**: Compute feasibility is measured against the constraint of ≤6 hours execution time and ≤7GB RAM usage on a standard 2-core CPU runner, verified by CI logs. (See FR-004, FR-005)
- **SC-003**: Predictive performance is measured against the target of a ≥ 5% absolute accuracy improvement over the geometry-only baseline on the held-out test set, with a secondary feasibility target of ≥ 80% absolute accuracy. (See FR-005)
- **SC-004**: Statistical significance is measured against the threshold of p < 0.05 via McNemar's test comparing the translation-only model to the geometry-only baseline. (See FR-006)
- **SC-005**: Model complexity is measured against the constraint of <10,000,000 parameters, verified by model summary output. (See FR-003)

## Assumptions

- **Assumption about data source**: The PyBullet physics engine is assumed to be sufficient for generating realistic rigid-body dynamics where translation trajectories implicitly contain signals related to tipping and slippage, even without explicit force sensors.
- **Assumption about compute constraints**: The 6-hour time limit and 7GB RAM limit on the GitHub Actions free-tier are sufficient for training a <10M parameter Transformer on ≥ 5,000 episodes; if not, the batch size or sequence length will be reduced to fit.
- **Assumption about methodological framing**: Since the data is generated from a simulation (no random assignment of physical laws), all findings regarding the relationship between translation and stability will be framed as associational, not causal.
- **Assumption about threshold justification**: The tipping angle and slippage distance thresholds are based on standard rigid-body stability criteria in robotics literature (e.g., center of mass projection). A sensitivity analysis (FR-008) will sweep these thresholds by ±5% to ensure robustness.
- **Assumption about multiplicity**: As only one primary hypothesis (translation sufficiency) is being tested against a single baseline (geometry-only), no family-wise error rate correction beyond the standard p < 0.05 threshold is required.
- **Assumption about measurement validity**: The "success" and "failure" labels derived from simulation physics metrics are assumed to be valid proxies for real-world stability, acknowledging that sim-to-real transfer may introduce a domain gap not addressed in this specific scope.