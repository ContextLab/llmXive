# Feature Specification: llmXive Follow-up: Physics-Teacher Distillation

**Feature Branch**: `002-llmxive-physics-teacher-distillation`  
**Created**: 2026-08-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Causal Forcing++ with deterministic physics solvers as teachers"

## User Scenarios & Testing

### User Story 1 - Physics-Based Teacher Signal Generation (Priority: P1)

The system must generate a deterministic "teacher" trajectory using a CPU-based physics engine (e.g., Box2D or simplified Navier-Stokes) for a set of synthetic video sequences, providing the ground-truth causal signal required to train the student model without relying on neural networks.

**Why this priority**: This is the foundational differentiator of the project. Without a valid, deterministic physics signal, the core hypothesis (replacing neural teachers with physics solvers) cannot be tested. It is the primary data source for the entire experiment.

**Independent Test**: Can be fully tested by running the data generation script, verifying that the output includes both rendered frames and state vectors (position, velocity) for [deferred] sequences, and confirming that the physics solver runs entirely on CPU without GPU errors.

**Acceptance Scenarios**:

1. **Given** a set of initial state vectors for rigid bodies or fluid particles, **When** the physics engine simulates 16 frames of motion, **Then** the system outputs a video sequence and a corresponding trajectory of state vectors that strictly adheres to the defined physical laws (e.g., conservation of momentum).
2. **Given** a request to generate [deferred] sequences, **When** the generation process completes, **Then** the system produces [deferred] valid video files and metadata files, with zero corruption or simulation crashes.
3. **Given** a specific physics parameter set (e.g., friction coefficient = 0.5), **When** the simulation runs, **Then** the resulting trajectory reflects the exact deterministic outcome of that parameter, with no stochastic noise introduced by the solver itself.

---

### User Story 2 - Student Model Training with Physics Teacher (Priority: P2)

The system must train a lightweight, 2-step autoregressive diffusion student model using the generated physics trajectories as the teacher signal, minimizing pixel-space MSE loss to learn the mapping from current frame + physics trajectory to the next frame.

**Why this priority**: This implements the core "distillation" mechanism. It tests whether the student model can successfully learn from the physics teacher. It is independent of the baseline comparison but dependent on the data generation from US-01.

**Independent Test**: Can be fully tested by initiating the training job, monitoring the loss curve to ensure it decreases, and verifying that the trained model can generate a single 16-frame sequence that visually resembles the physics input without requiring the neural teacher.

**Acceptance Scenarios**:

1. **Given** the physics-generated dataset and the student model architecture, **When** the training loop executes for the defined epochs, **Then** the Mean Squared Error (MSE) loss on the validation set decreases monotonically and converges below a threshold of 0.05.
2. **Given** a trained student model and a new physics trajectory, **When** the model generates a 16-frame sequence, **Then** the output frames exhibit structural consistency with the input trajectory (e.g., objects move in the correct direction and speed) as verified by a manual visual check or SSIM > 0.8.
3. **Given** the CPU-only constraint, **When** the training job runs, **Then** it completes within the 6-hour GitHub Actions limit and consumes less than 7 GB of RAM, without triggering OOM errors or requiring GPU acceleration.

---

### User Story 3 - Comparative Evaluation and Statistical Significance (Priority: P3)

The system must evaluate the physics-teacher model against a neural-teacher baseline using Structural Similarity (SSIM), PSNR, and LPIPS metrics, and perform a paired t-test to determine if the performance gap is statistically significant.

**Why this priority**: This provides the empirical answer to the research question. It quantifies the trade-off between physical plausibility and generative richness. It depends on the successful training of both models (US-02 and the baseline).

**Independent Test**: Can be fully tested by running the evaluation script on the held-out test set, generating the metric tables, and verifying that the statistical test (p-value) is computed correctly to determine significance.

**Acceptance Scenarios**:

1. **Given** the predictions from the physics-teacher model and the neural-teacher baseline, **When** the evaluation script runs, **Then** it outputs SSIM, PSNR, and LPIPS scores for both models on the same [deferred] test sequences.
2. **Given** the paired metric scores from both models, **When** the statistical analysis is performed, **Then** a paired t-test returns a p-value < 0.05 (or > 0.05) indicating whether the difference in performance is statistically significant.
3. **Given** the ablation parameters (e.g., varying friction), **When** the ablation study is run, **Then** the system produces a comparison table showing how changes in physical realism correlate with changes in the LPIPS texture metric.

### Edge Cases

- **What happens when** the physics simulation produces a collision or instability that results in NaN (Not a Number) values in the state vectors? **System handles** this by detecting NaNs during data generation, discarding the sequence, and logging a warning to ensure the training set remains clean.
- **How does the system handle** a scenario where the physics solver's time-step integration drifts significantly from the rendered frame rate? **System handles** this by enforcing a fixed, small time-step in the solver that aligns exactly with the 16-frame sequence duration, ensuring temporal consistency.
- **What happens when** the student model fails to converge due to the physics signal being too "rigid" (lacking gradient information for texture)? **System handles** this by implementing a fallback to a higher learning rate schedule or adding a small amount of synthetic noise to the teacher signal to provide a gradient, recorded as an assumption in the methodology.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate 5,000 synthetic video sequences of 16 frames each using a deterministic CPU physics engine (e.g., Box2D) and record ground-truth state vectors (See US-01).
- **FR-002**: System MUST train a 2-step autoregressive diffusion student model (approx. 50M parameters) using the physics-derived trajectories as the teacher signal, optimizing for pixel-space MSE loss (See US-02).
- **FR-003**: System MUST execute the entire training and inference pipeline on a CPU-only environment without requiring CUDA, GPU acceleration, or 8-bit/4-bit quantization libraries (See US-02).
- **FR-004**: System MUST compute Structural Similarity Index (SSIM), Peak Signal-to-Noise Ratio (PSNR), and Learned Perceptual Image Patch Similarity (LPIPS) metrics for both the physics-teacher and neural-teacher models on the same test set (See US-03).
- **FR-005**: System MUST perform a paired t-test on the SSIM and LPIPS scores between the two models to determine statistical significance at a threshold of p < 0.05 (See US-03).

### Key Entities

- **PhysicsTrajectory**: A sequence of state vectors (position, velocity, deformation) generated deterministically by the physics engine, serving as the causal prior.
- **StudentModel**: A lightweight autoregressive diffusion model trained to predict future frames given the current frame and the PhysicsTrajectory.
- **EvaluationMetrics**: A dataset containing SSIM, PSNR, and LPIPS scores paired with the corresponding video sequence ID for statistical comparison.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The convergence rate of the physics-teacher student model (measured by validation MSE loss) is measured against the baseline neural-teacher model to assess learning efficiency (See US-02).
- **SC-002**: The structural fidelity of generated frames (measured by SSIM and PSNR) is measured against the ground-truth physics frames to validate dynamic consistency (See US-03).
- **SC-003**: The loss of generative richness (measured by LPIPS) is measured against the neural-teacher baseline to quantify the trade-off between physical plausibility and texture synthesis (See US-03).
- **SC-004**: The statistical significance of the performance gap (measured by p-value from paired t-test) is measured against the standard alpha threshold of 0.05 to determine if the observed differences are non-random (See US-03).
- **SC-005**: The computational feasibility (measured by total wall-clock time and peak RAM usage) is measured against the GitHub Actions free-tier constraints (≤6 hours, ≤7 GB RAM) to ensure the method is deployable on edge devices (See US-02).

## Assumptions

- **Assumption about dataset-variable fit**: The selected CPU physics engine (Box2D or simplified Navier-Stokes) can generate sufficient state vectors (position, velocity) to fully define the causal trajectory for the 16-frame sequences; if the engine lacks a specific variable (e.g., deformation for soft bodies), the simulation will use a rigid-body approximation, and this limitation is noted as a scope boundary.
- **Assumption about inference framing**: Since the study uses synthetic data generated by a deterministic engine, the findings regarding "causal signal" are strictly associational within the context of the simulation; no claims of real-world causal inference are made for physical phenomena outside the simulation parameters.
- **Assumption about multiplicity & power**: The sample size of [deferred] sequences is assumed to provide sufficient statistical power (≥0.8) to detect a medium effect size in the paired t-test; if the power is lower, the results will be interpreted as exploratory with a limitation noted.
- **Assumption about threshold justification & sensitivity**: The decision cutoff for "statistical significance" is fixed at p < 0.05 based on community standards; a sensitivity analysis will sweep the alpha threshold over {0.01, 0.05, 0.1} to verify that the headline conclusion (significant vs. not significant) remains stable across this range.
- **Assumption about measurement validity**: The LPIPS metric is assumed to be a valid proxy for "generative richness" and "texture loss" in this context, as it is a standard perceptual metric validated in prior literature (e.g., Zhang et al., 2018).
- **Assumption about predictor collinearity**: Since the physics trajectory is the sole predictor for the dynamic signal, there is no risk of collinearity between predictors; however, the correlation between the physics signal and the final pixel output is treated as the primary dependent relationship, not independent effects.
- **Assumption about compute feasibility**: The 50M parameter student model and the [deferred] sequence dataset will fit within the ~7 GB RAM and ~14 GB disk constraints of the GitHub Actions free runner, allowing the entire training and evaluation pipeline to complete within 6 hours without GPU acceleration.
