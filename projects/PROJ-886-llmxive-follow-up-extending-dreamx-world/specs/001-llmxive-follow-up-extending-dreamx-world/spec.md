# Feature Specification: llmXive follow-up: extending "DreamX-World 1.0: A General-Purpose Interactive World Model"

**Feature Branch**: `001-dreamx-lite-geometric-priors`  
**Created**: 2026-09-03  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending DreamX-World 1.0 to test if deterministic geometric constraints can replace learned positional encodings for 3D consistency"

## User Scenarios & Testing

### User Story 1 - Deterministic Geometric Injection Pipeline (Priority: P1)

**Description**: As a researcher, I want to replace the learned E-PRoPE module in the DreamX-World 1.0 DiT backbone with a fixed, non-trainable linear projection layer that projects 4x4 camera pose matrices into the token embedding space, so that I can isolate the information contribution of deterministic geometric priors from learned positional representations.

**Why this priority**: This is the core experimental intervention. Without successfully implementing and disabling the learned module while injecting the deterministic alternative, the comparative study cannot proceed. It directly addresses the "What is known" vs "What is NOT known" gap regarding the sufficiency of geometric priors.

**Independent Test**: Can be fully tested by loading the pre-trained DreamX-World 1.0 weights, applying the architectural modification to swap the positional encoding module, and verifying via a forward pass that the model accepts camera matrices as input without error and produces output tensors of the expected shape, without requiring video generation.

**Acceptance Scenarios**:
1. **Given** the pre-trained DreamX-World 1.0 DiT weights are loaded in a CPU-only environment, **When** the E-PRoPE module is disabled and replaced with a fixed 4x4 camera projection layer, **Then** the model initialization completes without CUDA/GPU library errors and the parameter count decreases by the size of the removed E-PRoPE module.
2. **Given** a batch of ground-truth 4x4 camera extrinsic matrices is provided, **When** passed through the modified injection layer, **Then** the resulting token embeddings are deterministic (identical outputs for identical inputs) and do not require gradient updates during inference.

---

### User Story 2 - Long-Horizon Rollout & Metric Computation (Priority: P2)

**Description**: As a researcher, I want to generate 10-second video rollouts for both the baseline and "DreamX-Lite" variants under identical camera prompts, recover the camera trajectory from these videos using a frozen external SfM module, and compute the Mean Absolute Error (MAE) between the recovered trajectory and ground-truth extrinsics, so that I can quantify the 3D consistency and camera control accuracy of the deterministic approach.

**Why this priority**: This provides the primary quantitative evidence for the research question. It measures the "outcome" variable (3D consistency) against the "predictor" (deterministic vs learned). It is independent of the statistical aggregation but essential for the raw data collection.

**Independent Test**: Can be fully tested by running the inference pipeline on a subset of 5 trajectories, generating video files, running the SfM recovery, and verifying that the script outputs a JSON or CSV file containing the calculated MAE for position and rotation for each trajectory, without needing the full 50-trajectory dataset or statistical testing.

**Acceptance Scenarios**:
1. **Given** a set of 5 distinct camera control prompts and their corresponding ground-truth extrinsics, **When** the inference pipeline executes on a CPU-only runner, **Then** the system generates valid video files (MP4) for both the baseline and modified models.
2. **Given** the generated video frames and the ground-truth extrinsics, **When** the metric calculation script runs (including SfM recovery and normalization), **Then** it outputs a numeric MAE value for position (normalized units) and rotation (degrees) for each trajectory, with no circular dependency on the model's internal states.

---

### User Story 3 - Statistical Significance & Sensitivity Analysis (Priority: P3)

**Description**: As a researcher, I want to perform a McNemar's test on the SfM convergence rates and a Wilcoxon signed-rank test on the shape-consistency MAE scores across 50 trajectories, and sweep the consistency threshold over a defined range (e.g., MAE ∈ {0.01, 0.05, 0.1}), so that I can determine if the performance difference is statistically significant and robust to threshold selection.

**Why this priority**: This addresses the methodological soundness requirements for multiplicity, power, and threshold justification. It transforms raw data into a defensible scientific conclusion, ensuring the results are not artifacts of a single arbitrary cutoff.

**Methodological Justification**: The original idea suggested a paired t-test. We use the non-parametric Wilcoxon signed-rank test because geometric errors in generative models are typically non-Gaussian and heavy-tailed (outliers from SfM failures). The switch to McNemar's test for convergence rates is required because SfM failure is a binary event (converged/did not converge) and cannot be treated as a continuous variable.

**Independent Test**: Can be fully tested by providing a CSV of 50 paired scores (baseline vs. lite) and verifying that the script outputs the McNemar statistic (for convergence), the Wilcoxon statistic (for error), p-values, and a sensitivity table showing how the "success rate" changes across the specified MAE values.

**Acceptance Scenarios**:
1. **Given** a dataset of 50 paired convergence flags and MAE scores (baseline vs. DreamX-Lite), **When** the statistical analysis script runs, **Then** it outputs a McNemar test result for convergence and a Wilcoxon signed-rank test result for error, explicitly stating the null hypotheses.
2. **Given** a defined set of threshold values (e.g., MAE ≤ 0.01, 0.05, 0.1), **When** the sensitivity analysis runs, **Then** it reports the percentage of trajectories passing the threshold for both models at each level, demonstrating the stability of the performance gap.

---

### User Story 4 - Evaluation Integrity & Independence (Priority: P1)

**Description**: As a researcher, I want to ensure that the metric calculation pipeline (SfM recovery and MAE computation) is strictly decoupled from the generative model's internal state, so that the evaluation results are not biased by the model's own representations.

**Why this priority**: This is a fundamental scientific requirement. If the evaluation metric relies on the model's internal states, the test is circular and invalid. This story ensures the "blindness" of the evaluation.

**Independent Test**: Can be fully tested by inspecting the metric script's imports and input arguments to verify it contains no references to the DiT backbone, attention maps, or latent vectors, and only accepts video frames and ground-truth extrinsics.

**Acceptance Scenarios**:
1. **Given** the metric calculation script, **When** reviewed by a static analyzer, **Then** it must not import any modules related to the generative model's internal architecture (e.g., `dit_attention`, `latent_space`).
2. **Given** the metric calculation function signature, **When** invoked, **Then** it must accept only video frames (numpy arrays) and ground-truth extrinsics (4x4 matrices) as inputs, returning only scalar error metrics.

### Edge Cases

- What happens when the ground-truth camera extrinsics contain singularities or extreme rotations (e.g., gimbal lock) that the fixed projection layer cannot represent?
- How does the system handle video generation failures (e.g., out-of-memory crashes) on the CPU-only runner during long-horizon rollouts?
- What occurs if the pre-trained DreamX-World 1.0 weights are incompatible with the CPU-only inference environment (e.g., require specific GPU-optimized kernels)?
- What happens if the external SfM module fails to converge on a generated video (indicating extreme lack of 3D consistency)?

## Requirements

### Functional Requirements

- **FR-001**: System MUST replace the learned E-PRoPE module in the DiT backbone with a fixed, non-trainable linear projection layer that projects 4x4 camera pose matrices into the token embedding space (See US-1).
- **FR-002**: System MUST execute inference on a CPU-only runner; verification involves confirming the process completes without CUDA errors (e.g., by setting `CUDA_VISIBLE_DEVICES=""` or using `--device cpu`), regardless of whether GPU hardware is present (See US-2).
- **FR-003**: System MUST generate 10-second video rollouts for both the baseline and "DreamX-Lite" variants using identical camera control prompts to ensure a fair comparison (See US-2).
- **FR-004**: System MUST compute the Mean Absolute Error (MAE) for position (normalized units) and rotation (degrees) between the *recovered* camera trajectory (via external SfM) and the ground-truth extrinsics. If the SfM module fails to converge, the system MUST record a binary flag `convergence=false` and a sentinel MAE value indicating divergence. (See US-2).
- **FR-005**: System MUST perform a two-part statistical analysis on a set of distinct trajectories: (1) A McNemar's test on the binary `convergence` flags, and (2) A Wilcoxon signed-rank test on the MAE scores for the subset of trajectories where `convergence=true` (See US-3).
- **FR-006**: System MUST execute a sensitivity analysis sweeping the consistency threshold over a range of low MAE values. and report the variation in success rates (See US-3).
- **FR-007**: System MUST ensure that the metric calculation script is mathematically independent of the model's internal inputs by explicitly forbidding imports of internal model state variables and restricting inputs to only video frames and ground-truth extrinsics (See US-4).
- **FR-008**: System MUST compute and report the "Scale Drift" metric, defined as the ratio of the mean depth of the recovered trajectory to the mean depth of the ground-truth trajectory, to assess absolute scale consistency (See US-2).
- **FR-009**: System MUST record the exact reason for any SfM failure (e.g., "insufficient features", "optimization divergence") in the output log to enable qualitative analysis of failure modes (See US-2).

### Non-Functional Requirements

- **NFR-001**: The entire evaluation pipeline (video generation, SfM recovery, metric computation) for a single job MUST complete within 6 hours on the specified CPU-only hardware configuration.

### Key Entities

- **Camera Pose Matrix**: A 4x4 homogeneous transformation matrix representing the ground-truth camera extrinsics (position and orientation) for a specific frame, used as the input signal for the deterministic injection.
- **Rollout Trajectory**: A sequence of generated video frames corresponding to a specific camera control prompt, used to evaluate long-horizon consistency.
- **Camera Trajectory**: The sequence of 4x4 camera extrinsic matrices *recovered* from the generated video frames using an external Structure-from-Motion (SfM) algorithm, used for MAE calculation.
- **Consistency Score**: A derived metric (MAE) quantifying the deviation between the recovered camera trajectory and the ground-truth path, used for statistical comparison.
- **Scale Drift**: A ratio metric quantifying the difference in absolute scale between the ground-truth and recovered trajectories, used to detect scale ambiguity failures.
- **Dataset**: The collection of source data, specifically the DreamX-World subset (Unreal Engine renders with ground-truth camera extrinsics) and the ScanNet dataset, used for training and evaluation.
- **SfM Module**: A frozen, external Structure-from-Motion algorithm (e.g., COLMAP) used to infer camera poses from generated video frames without access to the generative model's internal states.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in "SfM Convergence Rate" and "Scale Drift" between the baseline and "DreamX-Lite" models is measured against the ground-truth extrinsics from the rendering engine metadata (See US-2).
- **SC-002**: The statistical significance of the performance difference is measured against the null hypothesis of no difference in convergence (McNemar) and no difference in median error (Wilcoxon) on 50 trajectories (See US-3).
- **SC-003**: The robustness of the performance claim is measured against a sensitivity analysis sweeping the decision threshold over the set {0.01, 0.05, 0.1} MAE (See US-3).
- **SC-004**: The computational efficiency (inference latency) is measured against the baseline model's runtime on the same CPU-only hardware configuration (See US-2).
- **SC-005**: The information-theoretic sufficiency of the geometric priors is measured by the ratio of the "DreamX-Lite" success rate to the baseline success rate across the thresholds defined in SC-003 (See US-3).

## Assumptions

- **Assumption about data availability**: The DreamX-World subset (Unreal Engine renders with ground-truth camera extrinsics) and ScanNet dataset are available for download from HuggingFace and the official repository without requiring new data collection or proprietary access.
- **Assumption about hardware constraints**: The entire analysis (model loading, inference, metric calculation) can complete within the GitHub Actions free-tier limits (2 CPU cores, ~7 GB RAM, ≤6 hours) by using a CPU-tractable approximation of the DiT backbone and sampling the dataset if necessary.
- **Assumption about model compatibility**: The pre-trained DreamX-World 1.0 weights can be loaded and executed in a CPU-only environment without requiring CUDA-specific optimizations or GPU-accelerated kernels.
- **Assumption about geometric sufficiency**: The 4x4 camera extrinsic matrices provided in the dataset contain sufficient information to define the camera pose without ambiguity (e.g., no singularities in the provided subset).
- **Assumption about threshold justification**: The threshold set {0.01, 0.05, 0.1} MAE is a defensible community-standard range for evaluating 3D consistency in video generation tasks, covering the transition from "exact" to "visually acceptable" consistency.
- **Assumption about statistical power**: A sample size sufficient to provide statistical power to detect a medium effect size in the Wilcoxon signed-rank test will be employed., or the limitation is explicitly acknowledged in the final report.
- **Assumption about scale normalization**: The 4x4 camera extrinsic matrices can be normalized to a canonical scale (e.g., mean distance to origin = 1.0) to resolve the inherent scale ambiguity in monocular video generation for *shape* comparison, but the "Scale Drift" metric (FR-008) is required to detect failures in absolute scale consistency.