# Feature Specification: llmXive Follow-up: Physics-Teacher Distillation

**Feature Branch**: `002-llmxive-physics-teacher-distillation`  
**Created**: 2026-08-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Causal Forcing++ with deterministic physics solvers as teachers"

## User Scenarios & Testing

### User Story 1 - Physics-Based Teacher Signal Generation (Priority: P1)

The system must generate a deterministic "teacher" trajectory using a CPU-based physics engine (e.g., Box2D or simplified Navier-Stokes) for a set of synthetic video sequences, providing the ground‑truth causal signal required to train the student model without relying on neural networks.

**Why this priority**: This is the foundational differentiator of the project. Without a valid, deterministic physics‑teacher signal, the core hypothesis (replacing neural teachers with physics solvers) cannot be tested. It is the primary data source for the entire experiment.

**Independent Test**: Can be fully tested by running the data generation script, verifying that the output includes both rendered frames and state vectors (position, velocity) for a substantial set of training sequences, and confirming that the physics solver runs entirely on CPU without GPU errors.

**Acceptance Scenarios**:

1. **Given** a set of initial state vectors for rigid bodies or fluid particles, **When** the physics engine simulates a series of frames of motion, **Then** the system outputs a video sequence and a corresponding trajectory of state vectors that strictly adheres to the defined physical laws (e.g., conservation of momentum) with **deterministic** outcomes (identical results on repeated runs with the same seed).
2. **Given** a request to generate **[deferred]** sequences, **When** the generation process completes, **Then** the system produces valid video files and metadata files, with **zero corruption** and **no NaN** values in any state vector.
3. **Given** a specific physics parameter set (e.g., friction coefficient = 0.5), **When** the simulation runs, **Then** the resulting trajectory reflects the exact deterministic outcome of that parameter, with no stochastic noise introduced by the solver itself.

---

### User Story 2 - Student Model Training with Physics Teacher (Priority: P2)

The system must train a lightweight, 2-step autoregressive diffusion student model using the generated physics trajectories as the teacher signal, minimizing pixel‑space MSE loss to learn the mapping from current frame + physics trajectory to the next frame.

**Why this priority**: This implements the core "distillation" mechanism. It tests whether the student model can successfully learn from the physics‑teacher. It is independent of the baseline comparison but dependent on the data generation from US‑01.

**Independent Test**: Can be fully tested by initiating the training job, monitoring the loss curve to ensure it meets the convergence criteria, and verifying that the trained model can generate a single 16‑frame sequence that visually resembles the physics input without requiring the neural teacher.

**Acceptance Scenarios**:

1. **Given** the physics‑generated dataset (**[deferred]** sequences) and the student model architecture, **When** the training loop executes for the defined epochs, **Then** the final validation MSE meets the convergence criteria defined in **SC‑002** and the relative improvement over the first epoch is at least 10 %.
2. **Given** a trained student model and a new physics trajectory, **When** the model generates a 16‑frame sequence, **Then** the output frames exhibit structural consistency with the input trajectory (e.g., objects move in the correct direction and speed) as verified by a manual visual check **or** a Structural Similarity Index (SSIM) that meets the fidelity criteria defined in **SC‑003**.
3. **Given** the CPU‑only constraint, **When** the training job runs, **Then** it completes within the GitHub Actions time limit and consumes less than 7 GB of RAM, without triggering OOM errors or requiring GPU acceleration.

---

### User Story 3 - Comparative Evaluation and Statistical Significance (Priority: P3)

The system must evaluate the physics‑teacher model against a neural‑teacher baseline using Structural Similarity (SSIM), Peak Signal‑to‑Noise Ratio (PSNR), and LPIPS metrics, and perform a paired t‑test to determine if the performance gap is statistically significant.

**Why this priority**: This provides the empirical answer to the research question. It quantifies the trade‑off between physical plausibility and generative richness. It depends on the successful training of both models (US‑02 and the baseline defined in FR‑007).

**Independent Test**: Can be fully tested by running the evaluation script on the held‑out test set (**[deferred]** sequences), generating the metric tables, and verifying that the statistical test (p‑value) is computed correctly to determine significance.

**Acceptance Scenarios**:

1. **Given** the predictions from the physics‑teacher model and the neural‑teacher baseline, **When** the evaluation script runs on the **[deferred]** held‑out test sequences, **Then** it outputs SSIM, PSNR, and LPIPS scores for both models on the same test sequences.
2. **Given** the paired metric scores from both models, **When** the statistical analysis is performed, **Then** a paired t‑test returns a p‑value for SSIM and a p‑value for LPIPS; each p‑value is compared against α = 0.05 (Bonferroni‑adjusted α = 0.025) and the report indicates whether the difference is statistically significant for each metric.
3. **Given** the ablation parameters (e.g., varying friction coefficient), **When** the ablation study is run, **Then** the system performs a linear regression of LPIPS (or FID) against the friction coefficient, reports Pearson r, the corresponding p‑value, and produces a comparison table showing how changes in physical realism correlate with changes in the fidelity (LPIPS) and richness (FID) metrics.

### Edge Cases

- **What happens when** the physics simulation produces a collision or instability that results in NaN (Not a Number) values in the state vectors? **System handles** this by detecting NaNs during data generation, discarding the sequence, and logging a warning to ensure the training set remains clean.
- **How does the system handle** a scenario where the physics solver's time‑step integration drifts significantly from the rendered frame rate? **System handles** this by enforcing a fixed, small time‑step in the solver that aligns exactly with the 16‑frame sequence duration, ensuring temporal consistency.
- **What happens when** the student model fails to converge (validation MSE > 0.07 after 20 epochs)? **System handles** this by switching to a higher learning‑rate schedule for the remaining epochs; if convergence still fails, the run is aborted and the failure is logged for later analysis.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a sufficiently large set of synthetic video sequences of a modest length (e.g., on the order of tens of frames) each using a deterministic CPU physics engine (e.g., Box2D) and record ground‑truth state vectors (See US‑01).
- **FR-002**: System MUST train a 2‑step autoregressive diffusion student model (≈ tens of M parameters) using the physics‑derived trajectories as the teacher signal, optimizing for pixel‑space MSE loss (See US‑02).
- **FR-003**: System MUST execute the entire training and inference pipeline on a CPU‑only environment without requiring CUDA, GPU acceleration, or 8‑bit/4‑bit quantization libraries (See US‑02).
- **FR-004**: System MUST compute Structural Similarity Index (SSIM), Peak Signal‑to‑Noise Ratio (PSNR), and Learned Perceptual Image Patch Similarity (LPIPS) metrics for both the physics‑teacher and neural‑teacher models on the same test set (See US‑03).
- **FR-005**: System MUST perform a paired t‑test on the SSIM and LPIPS scores between the two models to determine statistical significance (See US‑03).
- **FR-006**: System MUST verify that each generated video sequence is reproducibly identical on repeated runs with the same random seed and contains no NaN or corrupted frames (See US‑01).
- **FR-007**: System MUST construct a neural‑teacher baseline by training an identical student model on the same synthetic physics dataset used for the physics‑teacher, noting that the original Causal Forcing++ dataset is unavailable (See US‑03). This ensures both models are evaluated on the same test sequences.
- **FR-008**: System MUST conduct an ablation study varying physics‑simulation complexity (e.g., friction coefficient, elasticity, fluid dynamics) and record the impact on fidelity (LPIPS) and richness (FID) metrics (See US‑03).
- **FR-009**: System MUST compute the Fréchet Inception Distance (FID) between physics‑teacher generated videos and neural‑teacher baseline videos to quantify generative richness (See US‑03).

### Key Entities

- **PhysicsTrajectory**: A sequence of state vectors (position, velocity, deformation) generated deterministically by the physics engine, serving as the causal prior.
- **StudentModel**: A lightweight autoregressive diffusion model trained to predict future frames given the current frame and the PhysicsTrajectory.
- **EvaluationMetrics**: A dataset containing SSIM, PSNR, LPIPS, and FID scores paired with the corresponding video sequence ID for statistical comparison.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data‑generation validity: deterministic reproducibility (identical outputs on repeated runs) and zero‑corruption rate (≤ 0 % NaN or broken files) for all **[deferred]** sequences (See US‑01).
- **SC-002**: Convergence of student model training: final validation MSE ≤ 0.05 (pixels normalized to [0,1]) and ≥ 10 % relative improvement over the first epoch (See US‑02).
- **SC-003**: Fidelity of generated frames: SSIM ≥ 0.80 and LPIPS ≤ 0.30 when compared against ground‑truth physics frames (See US‑03).
- **SC-004**: Statistical significance of performance gap: paired t‑test on sequence‑level SSIM and LPIPS scores with Bonferroni‑adjusted α = 0.025; report p‑values and significance decisions (See US‑03).
- **SC-005**: Computational feasibility: total wall‑clock time ≤ 6 hours and peak RAM usage ≤ 7 GB on GitHub Actions free tier (See US‑02).
- **SC-006**: Ablation study reporting: linear regression results (Pearson r, p‑value) for LPIPS (and FID) versus physics‑complexity parameters, plus a comparison table summarising metric trends (See US‑03).
- **SC-007**: Richness assessment: FID computed between physics‑teacher generated videos and neural‑teacher baseline videos; lower FID indicates higher similarity to baseline richness (See US‑03).
- **SC-008**: Baseline model training success: neural‑teacher baseline achieves validation MSE ≤ 0.05 within the same compute constraints (See FR‑007).
- **SC-009**: Fréchet Inception Distance (FID) measurement: compute FID between the set of physics‑teacher generated videos (**[deferred]** sequences) and the corresponding neural‑teacher baseline videos; report the numeric FID value and interpret lower values as higher generative richness (See US‑03).

## Assumptions

- **Dataset sufficiency**: The selected CPU physics engine (Box2D or simplified Navier‑Stokes) can generate sufficient state vectors (position, velocity) to fully define the causal trajectory for the 16‑frame sequences; if the engine lacks deformation variables, a rigid‑body approximation is used, and this limitation is noted as a scope boundary.
- **Synthetic‑only scope**: Findings regarding “causal signal” are strictly associational within the context of the synthetic simulation; no claims of real‑world causal inference are made.
- **Statistical power**: With **[deferred]** generated sequences and a **[deferred]**‑sequence held‑out test set, the paired t‑test attains ≥ 0.8 power to detect a medium effect size (Cohen’s d is anticipated to be of medium magnitude.) for SSIM; if power is lower, results are interpreted as exploratory.
- **Threshold justification & sensitivity**: The α = 0.05 significance threshold follows community standards; a sensitivity analysis sweeps α over {0.01, 0.05, 0.10} to verify robustness of conclusions.
- **Metric validity**: LPIPS is used as a fidelity metric against ground‑truth physics frames, reflecting how closely generated frames match the deterministic source. FID is used as a richness metric, capturing perceptual diversity relative to the neural‑teacher baseline (Zhang et al.; Heusel et al., 2017).
- **Predictor singularity**: Since the physics trajectory is the sole predictor for the dynamic signal, there is no risk of collinearity between predictors; correlation between the physics signal and final pixel output is treated as the primary dependent relationship.
- **Compute feasibility**: The a multi‑million‑parameter student model and the **[deferred]**‑sequence dataset fit within the ~7 GB RAM and ~14 GB disk constraints of the GitHub Actions free runner, allowing the entire pipeline to complete within 6 hours without GPU acceleration.