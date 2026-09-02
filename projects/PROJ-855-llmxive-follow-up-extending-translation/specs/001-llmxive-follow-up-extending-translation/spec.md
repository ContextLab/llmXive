# Feature Specification: llmXive follow-up: extending "Translation as a Bridging Action"

**Feature Branch**: `001-llmxive-follow-up`  
**Created**: 2026-09-03  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Translation as a Bridging Action: Transferring Manipulation Skills fro"

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation & Labeling (Priority: P1)

A researcher needs to generate a dataset of bi-manual manipulation episodes using a CPU-based physics engine, where each episode records only monocular translation trajectories and is labeled with a binary stability outcome (success/failure) derived from physics metrics (tipping angle, slippage), ensuring the process handles simulation crashes and produces valid, geometry-disjoint splits.

**Why this priority**: Without a valid, reproducible dataset containing the specific "translation-only" input and "stability" ground truth, no model training or hypothesis testing can occur. This is the foundational data layer and the primary source of truth for the research.

**Independent Test**: The system can be tested by running the data generation script and verifying that the output Parquet files (`data/raw/synthetic_episodes.parquet`, `data/processed/train.parquet`, `data/processed/test.parquet`) exist, contain exactly the required columns (translation vectors, initial object bounds), have a binary label column, and that the test set contains object geometries completely disjoint from the training set.

**Acceptance Scenarios**:

1. **Given** a configuration for ≥ 5,000 episodes with simplified rigid bodies, **When** the generation script executes on a CPU, **Then** the output dataset contains ≥ 5,000 valid rows with translation vectors and a binary stability label, and execution completes within the total 6-hour pipeline budget.
2. **Given** an episode where the simulated object tips beyond the defined threshold (≥ 15°) or slips (≥ 0.02m), **When** the labeling logic runs using `config.yaml` parameters, **Then** the corresponding record is marked as "failure" (0) regardless of the translation trajectory shape.
3. **Given** the requirement to discard specific data types, **When** the dataset is inspected, **Then** no columns containing rotation quaternions, joint torques, or force sensor readings exist in the file.
4. **Given** a physics simulation crash (e.g., numerical instability) mid-episode, **When** the generation loop encounters an exception, **Then** the script logs the failure, discards the incomplete episode, and generates a replacement to ensure the final dataset size meets the ≥ 5,000 target.

---

### User Story 2 - Lightweight Sequence Model Training (Priority: P2)

A researcher needs to train a lightweight sequence model (constrained to <10M parameters, referencing PyramidTNT-Ti architecture) on the generated dataset to predict stability labels using only translation trajectories, ensuring the entire training process runs within 6 hours on a 2-core CPU with 7GB RAM, and persists the model and a parameter count summary.

**Why this priority**: This implements the core hypothesis testing mechanism. It must be feasible on free-tier hardware to be actionable, and the parameter count must be verifiable to ensure it meets the "edge robot" constraint.

**Independent Test**: The system can be tested by initiating the training job on a standard GitHub Actions runner (2 CPU, 7GB RAM), verifying that the job completes without OOM errors, GPU allocation failures, or exceeding the 6-hour time limit, and that the artifact `data/processed/trained_model.pt` and a model summary log are generated.

**Acceptance Scenarios**:

1. **Given** the synthetic dataset and the 4-layer Transformer architecture, **When** training starts on a CPU-only environment, **Then** the process utilizes <7GB RAM and completes within 6 hours.
2. **Given** the constraint to avoid GPU-specific operations, **When** the code executes, **Then** no CUDA or bitsandbytes imports are triggered, `torch.cuda.is_available()` returns False, and the model runs in float32 precision.
3. **Given** the model parameters are capped at <10,000,000, **When** the model summary is printed and logged, **Then** the total parameter count is strictly less than 10,000,000, and this count is recorded in a `model_summary.txt` artifact.
4. **Given** the training loop, **When** it finishes, **Then** the trained weights are saved to `data/processed/trained_model.pt` and are not hard-coded or simulated.

---

### User Story 3 - Statistical Validation & Baseline Comparison (Priority: P3)

A researcher needs to statistically validate that the translation-only model's predictive performance is superior to two baselines: (1) a Geometry-Only Baseline (trained on object bounds) and (2) a Random-Translation Baseline (shuffled input), using McNemar's test on the geometry-disjoint test set. The system must report the accuracy difference relative to a Class Prior baseline to ensure non-triviality, and verify that all metrics are derived from real measurements.

**Why this priority**: This confirms the research hypothesis (that translation signals encode physical constraints) and provides the empirical evidence required for the "research_complete" stage. It must explicitly avoid fabricated results and validate against a null hypothesis (random noise).

**Independent Test**: The system can be tested by running the evaluation script on the held-out test set and verifying the output includes the McNemar's test p-values (vs. Geometry and vs. Random baselines), the accuracy of all models, the AUC-ROC, and the calculated accuracy differences, all derived from the `trained_model.pt`, `geometry_baseline.pt`, `random_baseline.pt`, and `class_prior_baseline` artifacts.

**Acceptance Scenarios**:

1. **Given** the translation-only model's predictions and the baselines' predictions for the test set, **When** the statistical test runs, **Then** McNemar's test yields p-values for both comparisons (Translation vs. Geometry, Translation vs. Random) and the system reports whether the models are statistically equivalent or if the translation model is significantly better.
2. **Given** a test set containing object geometries not seen during training, **When** both models predict stability, **Then** the system reports the measured accuracy of all models, the AUC-ROC, and the accuracy difference relative to the Class Prior baseline.
3. **Given** the requirement for methodological rigor, **When** the results are reported, **Then** the report explicitly states the accuracy differences and p-values without claiming causal inference beyond the associational nature of the observational data, and explicitly confirms that all metrics are derived from real measurements on the generated data (no hard-coded values).

---

### Edge Cases

- **What happens when** the physics simulation encounters a numerical instability (e.g., object tunneling) causing a crash mid-episode?
  - *Handling*: The generation script must catch the exception, discard the incomplete episode, log the failure, and generate a replacement to ensure the final dataset size is ≥ 5,000 valid episodes.
- **How does the system handle** a scenario where the translation trajectory is identical for both a success and a failure outcome (ambiguous signal)?
  - *Handling*: The model will learn the probability distribution; the evaluation must report the confusion matrix to show if the model is forced to guess. If the accuracy on this ambiguous subset is < 50% (random chance), it is flagged as a measurable limitation of the "translation-only" modality.
- **What happens if** the 6-hour time limit is exceeded during training?
  - *Handling*: The CI job must fail gracefully with a timeout error, and the `Assumptions` section must note that the current hyperparameters (learning rate, batch size) may need reduction to fit the compute box.
- **What happens if** the baseline models fail to converge?
  - *Handling*: The evaluation script must detect a baseline accuracy near random chance (e.g., < 55%) and flag the comparison as potentially invalid due to an underpowered baseline, rather than fabricating a result.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a synthetic dataset of bi-manual manipulation episodes using PyBullet, recording only relative wrist translation vectors and initial object bounding box coordinates, while explicitly discarding rotation and force data. (See US-1)
- **FR-002**: System MUST label each generated episode with a binary stability outcome (1=success, 0=failure) based on physics-derived metrics: tipping angle ≥ 15° or slippage distance ≥ 0.02m, with these thresholds loaded from `config.yaml`. (See US-1)
- **FR-003**: System MUST implement a lightweight Transformer encoder with a parameter count strictly constrained to <10,000,000 parameters (referencing PyramidTNT-Ti, arXiv:2201.00978). (See US-2)
- **FR-004**: System MUST train the model using binary cross-entropy loss on a CPU-only environment without utilizing CUDA, bitsandbytes, or GPU-specific acceleration libraries. (See US-2)
- **FR-005**: System MUST evaluate the trained model on a held-out test set of novel object geometries (geometry-disjoint split) and compute accuracy, ensuring the process completes within 6 hours on a 2-core CPU runner with 7GB RAM. (See US-2, US-3)
- **FR-006**: System MUST train a "Geometry-Only Baseline" (a lightweight MLP using only initial object bounds) and persist it as `data/processed/geometry_baseline.pt` for comparison. (See US-3)
- **FR-007**: System MUST train a "Random-Translation Baseline" (a model trained on shuffled/noise translation sequences of the same length) and persist it as `data/processed/random_baseline.pt` to test the null hypothesis. (See US-3)
- **FR-008**: System MUST perform McNemar's test to compare the translation-only model against BOTH the Geometry-Only Baseline and the Random-Translation Baseline, outputting p-values and accuracy metrics derived from real model predictions. (See US-3)
- **FR-009**: System MUST perform a sensitivity analysis on the labeling thresholds by injecting Gaussian noise (σ=0.5°) into the computed tipping angle value before applying the threshold, sweeping the noise level to simulate sensor uncertainty and reporting the variance in model accuracy to ensure ground truth robustness (justification: essential to validate labeling logic against physics engine numerical precision and simulated sensor noise). (See US-3)
- **FR-010**: System MUST train a "Class Prior Baseline" (predicting the majority class frequency) and report its accuracy to ensure the translation model's improvement is not trivial. (See US-3)
- **FR-011**: System MUST report results associatively, explicitly avoiding causal claims about translation causing stability, acknowledging the observational nature of the data. (See US-3)
- **FR-012**: System MUST generate and persist a `model_summary.txt` artifact containing the exact parameter count of the trained model before saving. (See US-2)

### Key Entities

- **ManipulationEpisode**: A single data record containing a sequence of translation vectors, initial object bounds, and a binary stability label.
- **StabilityMetric**: A derived value (tipping angle, slippage distance) used to determine the ground-truth label.
- **SequenceModel**: The lightweight Transformer architecture trained to map translation sequences to stability probabilities.
- **GeometryBaseline**: A lightweight classifier trained on object bounds only.
- **RandomBaseline**: A classifier trained on shuffled/noise translation sequences.
- **ClassPriorBaseline**: A predictor that always outputs the majority class.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Dataset validity is measured against the requirement of ≥ 5,000 valid episodes with no rotation/force columns and a geometry-disjoint split, verified by schema inspection and checksum validation of `data/processed/train.parquet` and `data/processed/test.parquet`. (See FR-001, FR-002)
- **SC-002**: Compute feasibility is measured against the constraint of ≤6 hours execution time and ≤7GB RAM usage on a standard 2-core CPU runner, verified by CI logs. (See FR-004, FR-005)
- **SC-003**: Predictive performance is measured by calculating and reporting the accuracy difference between the translation-only model and the Geometry-Only Baseline, the Random-Translation Baseline, and the Class Prior Baseline, along with the AUC-ROC metric. (See FR-008, FR-010)
- **SC-004**: Statistical significance is measured against the threshold of p < 0.05 via McNemar's test for BOTH comparisons (Translation vs. Geometry AND Translation vs. Random); both must pass to support the hypothesis. (See FR-008)
- **SC-005**: Model complexity is measured against the constraint of <10,000,000 parameters, verified by `model_summary.txt`. (See FR-003)
- **SC-006**: Result authenticity is measured by verifying that all reported metrics (accuracy, p-value) are derived from the `trained_model.pt`, `geometry_baseline.pt`, and `random_baseline.pt` artifacts, verified by static analysis of the evaluation code for constant return statements and log inspection for artifact file paths. (See FR-008, FR-011)

## Assumptions

- **Assumption about data source**: The PyBullet physics engine is assumed to be sufficient for generating realistic rigid-body dynamics where translation trajectories implicitly contain signals related to tipping and slippage, even without explicit force sensors.
- **Assumption about compute constraints**: The 6-hour time limit and 7GB RAM limit on the GitHub Actions free-tier are sufficient for training a <10M parameter Transformer on ≥ 5,000 episodes; if not, the batch size or sequence length will be reduced to fit.
- **Assumption about methodological framing**: Since the data is generated from a simulation (no random assignment of physical laws), all findings regarding the relationship between translation and stability will be framed as associational, not causal.
- **Assumption about threshold justification**: The tipping angle (15°) and slippage distance (0.02m) thresholds are fixed constants based on standard rigid-body stability criteria. The sensitivity analysis (FR-009) simulates sensor noise by injecting Gaussian noise (σ=0.5°) into the computed angle to test robustness.
- **Assumption about multiplicity**: As only one primary hypothesis (translation sufficiency) is being tested against two baselines, the requirement is that both McNemar comparisons must yield p < 0.05.
- **Assumption about measurement validity**: The "success" and "failure" labels derived from simulation physics metrics are assumed to be valid proxies for real-world stability, acknowledging that sim-to-real transfer may introduce a domain gap not addressed in this specific scope.
- **Assumption about baseline definition**: The baselines for statistical comparison are defined as (1) a Geometry-Only classifier, (2) a Random-Translation classifier, and (3) a Class Prior predictor, to ensure valid statistical comparison via McNemar's test.
- **Assumption about data integrity**: All performance metrics reported in the final evaluation must be derived from real measurements on generated data; fabricated, simulated, or hard-coded results are strictly prohibited.
- **Assumption about architecture**: The <10M parameter constraint is based on the PyramidTNT-Ti architecture (arXiv:2201.00978) as a community standard for efficient deployment on edge devices.
- **Assumption about sample size**: The target of ≥ 5,000 episodes is a minimum sample size calculated to provide sufficient statistical power for the hypothesis test, not an arbitrary scope constraint.