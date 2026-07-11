# Feature Specification: llmXive follow-up: extending "SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diff"

**Feature Branch**: `001-symbolic-geometric-priors`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "To what extent does the geometric consistency of SANA-WM's minute-scale video generation depend on learned semantic priors versus its architectural inductive biases when driven exclusively by symbolic, rule-based 6-DoF camera trajectories?"

## User Scenarios & Testing

### User Story 1 - Synthetic Trajectory Generation (Priority: P1)

The system MUST generate a synthetic dataset of rigid-body motion trajectories using kinematic equations (constant velocity, sinusoidal oscillation, chaotic, and high-frequency oscillation) to create ground-truth 6-DoF pose sequences without relying on real-world video data. The dataset MUST contain a sufficient number of trajectories, each with a duration of 10 seconds.

**Why this priority**: This is the foundational data layer; without ground-truth symbolic trajectories, the symbolic encoder has no input, and the geometric consistency cannot be measured against a known standard. The reduced sample size (N=50) and duration (10s) are explicitly chosen to ensure the experiment completes within the 6-hour hardware constraint while maintaining statistical power for a pilot study. Including complex motions ensures the test is not trivial.

**Independent Test**: Can be fully tested by executing the data synthesis script and verifying that the output file contains a representative set of sequences where each sequence's pose at time $t$ matches the deterministic kinematic equation used to generate it, with zero deviation, and includes at least 10 sequences of chaotic/high-frequency motion. The total generation time for all 50 trajectories MUST be logged and verified to be < 30 minutes.

**Acceptance Scenarios**:

1. **Given** the kinematic equation parameters (velocity, frequency, chaos factor), **When** the synthesis script runs, **Then** the output file contains a set of distinct trajectory files, each with a timestamped pose sequence matching the equation.
2. **Given** a specific trajectory ID, **When** the ground-truth pose at $t=5s$ is retrieved, **Then** the value matches the result of the kinematic equation within a floating-point tolerance.
3. **Given** the texture generation requirement, **When** the synthetic video frames are generated, **Then** the background contains temporally coherent Perlin noise with a fixed seed, ensuring trackable features for COLMAP.

---

### User Story 2 - Symbolic Encoder & CPU Inference (Priority: P2)

The system MUST replace the learned text-to-image encoder with a hard-coded symbolic function mapping kinematic rules to camera condition vectors, and execute the generation loop using low-bit quantized weights on a CPU-only environment with constrained memory resources (2 cores, 7GB RAM).

**Why this priority**: This isolates the architectural inductive bias by removing semantic priors and enforces the compute constraints required for the study. Without this, the experiment tests the full model, not the specific hypothesis.

**Independent Test**: Can be fully tested by running the inference pipeline with a single symbolic trajectory and verifying that the output video is generated without CUDA errors, without loading any text-embedding model, and within the time limit. Wall-clock time MUST be measured using the system `time` utility or a high-resolution timer and logged to a JSON report for verification. GPU utilization MUST be logged and verified to be negligible (≤ 1%).

**Acceptance Scenarios**:

1. **Given** a symbolic trajectory input, **When** the generation loop starts, **Then** the system loads the 4-bit quantized model weights and bypasses the text-encoder module entirely.
2. **Given** the CPU environment constraints (2 cores, 7GB RAM), **When** a 10-second 720p sequence is generated, **Then** the process completes without OOM errors and within a logged wall-clock time of < 6 minutes per sequence.
3. **Given** the CPU-only constraint, **When** the system checks for CUDA devices, **Then** it MUST report zero active CUDA devices and log a confirmation of CPU-only execution with GPU utilization logged as ≤ 1%.

---

### User Story 3 - Geometric Consistency Evaluation (Priority: P3)

The system MUST calculate camera trajectory error (Euclidean distance between generated and ground-truth poses) after Sim3 Procrustes alignment and perform a paired t-test to determine statistical significance (p < 0.05). The evaluation MUST exclude trajectories where the pose estimator fails for >80% of frames. The study compares symbolic-driven generation directly to ground truth; no 'Learned' baseline with text-conversion is included to avoid confounds.

**Why this priority**: This delivers the final scientific answer to the research question. It quantifies the "extent" of dependency on architectural bias by measuring geometric consistency against ground truth. The exclusion protocol ensures the statistical test operates on valid paired observations.

**Independent Test**: Can be fully tested by running the evaluation script on the generated videos and verifying that the output includes a p-value and that the geometric error is calculated against the ground-truth poses from User Story 1 after Procrustes alignment. The output MUST be a JSON object containing 'p_value', 't_statistic', 'degrees_of_freedom', 'test_type' (paired t-test), and 'frame_validity_rate'.

**Acceptance Scenarios**:

1. **Given** the generated video and the ground-truth trajectory, **When** the trajectory error is computed, **Then** the result is a single scalar value representing the mean Euclidean distance over the sequence, AFTER applying Sim3 Procrustes alignment to the COLMAP poses, excluding frames where the pose estimator failed.
2. **Given** the symbolic generation results, **When** the paired t-test is executed on the distribution of 50 error differences (excluding pairs with >10% mismatched valid frame counts or <80% valid frames), **Then** the output includes a p-value and a clear statement of whether the difference is statistically significant at $\alpha = 0.05$.
3. **Given** the exclusion protocol, **When** a trajectory has >80% invalid frames, **Then** the trajectory is excluded from the t-test, and the exclusion reason is logged.

### Edge Cases

- What happens if the symbolic encoder produces a trajectory that exceeds the model's maximum context window? (System MUST clamp or truncate the sequence to the model's limit and log the truncation event).
- How does the system handle a failure in the 4-bit quantization loading process? (System MUST abort with a clear "Quantization not supported on this hardware" error code `ERR_QUANT_UNSUPPORTED` and exit; NO fallback to FP16 is permitted as it violates the CPU-only constraint).
- What if the generated video frames are completely black (indicating a failure in the symbolic mapping)? (System MUST detect zero-variance frames, defined as standard deviation of pixel intensities < 1e-5 across all channels, and flag the run as "Invalid Generation" rather than computing metrics on noise. If >80% of frames are invalid, the trajectory is excluded from the t-test).
- What if the pose estimator fails to recover a pose (returns NaN or low confidence)? (System MUST flag the frame as "Invalid" and exclude it from the mean error calculation; the frame is not treated as high error. If >80% of frames are invalid, the trajectory is excluded from the t-test).
- What if the texture generation fails to produce trackable features? (System MUST verify the presence of Perlin noise features in the first frame; if not found, abort generation and log `ERR_TEXTURE_INVALID`).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a set of 50 synthetic 6-DoF camera trajectories using kinematic equations (constant velocity, sinusoidal oscillation, chaotic, and high-frequency oscillation) with a duration of 10 seconds per sequence. (See US-1)
- **FR-002**: System MUST replace the SANA-WM text-to-image encoder with a deterministic symbolic function that maps kinematic rules directly to camera condition vectors. (See US-2)
- **FR-003**: System MUST execute the generation pipeline using 4-bit quantized weights on a CPU-only runtime (2 cores, 7GB RAM) without requiring CUDA or GPU accelerators. The system MUST verify the absence of CUDA devices before starting inference and log GPU utilization as ≤ 1%. (See US-2)
- **FR-004**: System MUST compute the Euclidean distance between the generated camera poses (extracted via COLMAP) and the ground-truth symbolic poses for every frame in the sequence. Frames where the pose estimator fails (returns NaN or confidence < 0.8) MUST be excluded from the mean error calculation. If >80% of frames in a trajectory are invalid, the entire trajectory MUST be excluded from the statistical analysis. (See US-3)
- **FR-005**: System MUST perform a single paired t-test comparing the geometric consistency metrics (mean error) of the symbolic-driven generation against the ground-truth kinematic poses. (See US-3)
- **FR-006**: System MUST compute the distribution of error differences (one per trajectory) and perform a paired t-test on this distribution to determine statistical significance. Trajectory pairs with mismatched valid frame counts (>10% difference) or either run having <80% valid frames MUST be excluded from the test. (See US-3)
- **FR-007**: System MUST use COLMAP as the pose estimator with the following configuration: feature extraction method = 'AKAZE', matching strategy = 'exhaustive', and minimum inlier ratio = 0.8 for a valid pose. This configuration MUST be applied identically to ALL runs. The configuration MUST be logged to a JSON file at the start of every run. (See US-3)
- **FR-008**: System MUST use a FIXED, STATIC text prompt ("A static scene with no motion") for any baseline comparison if one were to be added, but currently the study compares symbolic drive directly to ground truth. (See US-3)
- **FR-009**: System MUST perform a Sim3 Procrustes alignment to align the relative COLMAP poses to the absolute ground-truth kinematic poses before calculating the Euclidean distance error. (See US-3)
- **FR-010**: System MUST generate background textures using temporally coherent Perlin noise with a fixed seed and a suitable frequency band to ensure trackable features for COLMAP. (See US-1)
- **FR-011**: System MUST exclude any trajectory from the t-test if the number of valid frames is <80% of the total frames. (See US-3)
- **FR-012**: System MUST implement a 'feasibility gate' that checks for the existence of *any* -bit quantized SANA-WM weights (NVFP4, GPTQ, or QLoRA) and CPU inference capability before the main experiment runs. If the weights are missing or CPU inference fails, the system MUST abort with error code `ERR_FEASIBILITY_FAIL`. (See US-2)
- **FR-013**: System MUST verify the 'CPU-only' constraint by checking for the absence of CUDA devices and logging GPU utilization (must be ≤ 1%) during inference. (See US-2)

### Key Entities

- **SyntheticTrajectory**: A data structure representing a sequence of 6-DoF poses (position x,y,z; rotation roll,pitch,yaw) generated by kinematic equations.
- **GeneratedVideo**: A video file (720p) produced by the SANA-WM model driven by a SyntheticTrajectory.
- **GeometricMetric**: A numerical value representing the deviation between the GeneratedVideo's inferred pose and the SyntheticTrajectory's ground truth, calculated after Procrustes alignment.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The mean Euclidean trajectory error is measured against the ground-truth kinematic poses to determine the geometric consistency of the symbolic-driven generation. (See FR-004, US-3)
- **SC-002**: The statistical significance of the difference in geometric metrics is measured against the threshold of p < 0.05 (no multiple-comparison correction required as only one aggregate test is performed). (See FR-005, FR-006, US-3)
- **SC-003**: The total inference time per sequence is measured against a maximum job limit of 6 minutes per sequence, with a total experiment time limit of 6 hours for all 50 trajectories. (See FR-003, US-2)
- **SC-004**: The memory footprint during inference is measured against the available RAM constraint of 7GB to ensure the quantized model fits within the free-tier runner limits. (See FR-003, US-2)
- **SC-005**: The COLMAP configuration log file MUST exist and contain the exact parameters specified in FR-007 (AKAZE, exhaustive, 0.8 inlier) for all runs. (See FR-007)
- **SC-006**: The feasibility gate MUST execute and report 'PASS' before the main experiment begins. (See FR-012)
- **SC-007**: The Frame Validity Rate MUST be reported for the symbolic condition to assess the bias of the error metric. (See US-3)

## Assumptions

- **Assumption about dataset-variable fit**: The COLMAP pose estimator can accurately recover 6-DoF camera poses from the generated synthetic videos, even when texture fidelity is low, provided the frames are not completely black (std dev < 1e-5) and contain temporally coherent Perlin noise. If the pose estimator fails (confidence < 0.8), the frame is excluded from the metric.
- **Assumption about inference framing**: Since the study uses synthetic data and symbolic inputs rather than randomized human subjects, findings regarding "geometric consistency" are framed as **associational** properties of the model architecture under specific symbolic conditions, not as causal claims about general world understanding.
- **Assumption about compute feasibility**: The 4-bit quantized weights of SANA-WM (or nearest available 4-bit variant such as GPTQ/QLoRA) can be loaded and run on a multi-core CPU with sufficient RAM within the 6-hour limit for 50 trajectories of 10 seconds duration. If the specific NVFP4 weights are not available, the experiment will use the nearest available 4-bit quantized variant to maintain feasibility, with a note that this is a deviation from the ideal NVFP4 target.
- **Assumption about threshold justification**: The threshold for "statistical significance" is fixed at $\alpha = 0.05$ based on standard scientific convention. A sensitivity analysis will sweep $\alpha$ over a range of small values to report how the conclusion changes.
- **Assumption about measurement validity**: The "geometric consistency" metric (Euclidean trajectory error), calculated after Sim3 Procrustes alignment, is a valid proxy for the model's structural inductive bias, distinct from semantic fidelity. The metric is conditional on successful feature generation; trajectories with >80% invalid frames are excluded.
- **Assumption about predictor collinearity**: The symbolic kinematic equations (constant velocity vs. sinusoidal) are treated as distinct experimental conditions; the analysis will not claim independent predictive effects of specific motion types on geometric error without a collinearity diagnostic, as the motion parameters may be mathematically related.
- **Assumption about data constraints**: A set of 50 synthetic trajectories (10s each) fits within the GB disk limit of the CI runner, including intermediate video frames and logs.
- **Assumption about quantization**: The 4-bit quantization format is supported by the chosen inference library (e.g., `llama.cpp` or `diffusers` with specific commit) on CPU without requiring CUDA-specific kernels.
- **Assumption about model availability**: The SANA-WM model weights (or a suitable 4-bit equivalent) are accessible via a public HuggingFace repository and can be downloaded within the CI runner's network constraints.