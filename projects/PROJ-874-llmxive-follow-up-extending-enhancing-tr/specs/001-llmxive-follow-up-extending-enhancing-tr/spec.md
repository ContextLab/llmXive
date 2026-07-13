# Feature Specification: llmXive Follow-up: Extending "Enhancing Train-Free Infinite-Frame Generation for Consistent Long Vid"

**Feature Branch**: `[001-llmxive-flow-correction]`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Enhancing Train-Free Infinite-Frame Generation for Consistent Long Vid'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproducible Baseline Execution (Priority: P1)

The researcher needs to execute the standard MIGA pipeline with self-reflection enabled (Condition A) and without it (Condition B) on a CPU-only environment to establish a performance and consistency baseline for comparison.

**Why this priority**: This is the foundational step. Without a verified, reproducible baseline of the iterative generative method and the naive uncorrected output, no comparison of the proposed flow-based correction can be made. It validates the environment and the data pipeline.

**Independent Test**: Can be fully tested by running the generation script with the `--mode baseline` flag and verifying that output video files are generated for all prompts, and that wall-clock time is recorded in the logs, without requiring the optical flow module to be functional.

**Acceptance Scenarios**:

1. **Given** the NarrLV/VBench dataset is available, **When** the researcher executes the MIGA pipeline with `--mode baseline-full`, **Then** A set of video files is generated., and the log records a total wall-clock time per video.
2. **Given** the same dataset, **When** the researcher executes the MIGA pipeline with `--mode baseline-naive` (self-reflection disabled), **Then** A set of video files is generated., and the log records a significantly lower wall-clock time than the full baseline.

---

### User Story 2 - Deterministic Flow-Based Correction (Priority: P2)

The researcher needs to apply a CPU-tractable optical flow estimation (RAFT-Small) and non-differentiable warping/smoothing to the naive baseline outputs (Condition C) to assess if deterministic priors can substitute for iterative refinement.

**Why this priority**: This is the core experimental intervention. It directly addresses the research question regarding the extent to which 2D motion regularization can correct 3D drift. It is the "new" functionality being proposed.

**Independent Test**: Can be fully tested by running the correction script on the naive baseline videos, verifying that the flow fields are computed and applied, and that the resulting "corrected" videos are generated without requiring the iterative self-reflection module.

**Acceptance Scenarios**:

1. **Given** a naive baseline video file, **When** the flow correction module is executed with `--raft-model small`, **Then** an optical flow field is computed, a warped video is generated, and the process completes within 6 hours on a 2-core CPU.
2. **Given** a sequence of naive baseline videos, **When** the smoothing operation is applied, **Then** the output video maintains a VBench temporal consistency score ≥ 0.95 of the naive baseline score, ensuring no significant degradation in 2D perceptual quality.

---

### User Story 3 - Comparative Analysis and 3D Drift Limitation Mapping (Priority: P3)

The researcher needs to compute VBench temporal consistency scores, object permanence metrics, and Fréchet Video Distance (FVD) for all three conditions, perform statistical significance testing (with normality checks), and identify specific failure cases where 2D flow fails to correct 3D structural drift.

**Why this priority**: This is the validation and analysis phase. It determines the success or failure of the hypothesis and provides the theoretical boundaries requested in the research question.

**Independent Test**: Can be fully tested by running the evaluation script on the three sets of generated videos (Condition A, B, C) and verifying that a summary report is produced containing statistical test results (p-values), power analysis, and a qualitative report of 2D perceptual failure modes.

**Acceptance Scenarios**:

1. **Given** the three sets of generated videos, **When** the evaluation script runs, **Then** a CSV report is generated containing VBench consistency scores, FVD, and object permanence metrics for each video ID.
2. **Given** the metric scores, **When** the statistical analysis module runs, **Then** a paired t-test or Wilcoxon signed-rank test result is reported (based on normality check) indicating if the difference between Condition A and Condition C is significant (p < 0.05).
3. **Given** videos with high 3D motion (rotation), **When** the failure analysis runs, **Then** specific video IDs are flagged where the object permanence score drops by ≥ 5% compared to the naive baseline, indicating a failure of 2D flow to maintain object visibility.

### Edge Cases

- What happens when the optical flow estimation fails for a specific frame (e.g., extreme motion blur or occlusion)? The system MUST handle this by falling back to a nearest-neighbor interpolation of flow vectors for that frame rather than crashing.
- How does the system handle videos where the 3D drift is so severe that warping creates invalid pixel artifacts (e.g., tearing)? The system MUST detect and flag these frames in the error log for manual review, rather than silently producing a corrupted video.
- What happens if the NarrLV dataset download is incomplete? The system MUST abort the run with a clear error message listing missing files, rather than proceeding with a partial dataset which would invalidate the statistical power.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache a diverse set of video prompts and ground-truth sequences from the NarrLV dataset and VBench benchmarks via HuggingFace, ensuring all required files are present before generation begins. (See US-1)
- **FR-002**: System MUST execute the MIGA generation pipeline in two distinct modes: (A) `--mode baseline-full` with full self-reflection enabled and (B) `--mode baseline-naive` with self-reflection disabled, recording wall-clock time for each. (See US-1)
- **FR-003**: System MUST compute optical flow fields between consecutive frames of the naive baseline (Condition B) using the RAFT-Small model in FP16 precision on CPU. (See US-2)
- **FR-004**: System MUST apply a non-differentiable warping and smoothing operation to the naive baseline frames based on the computed flow fields to generate Condition C outputs. (See US-2)
- **FR-005**: System MUST calculate VBench temporal consistency scores, object permanence metrics, and Fréchet Video Distance (FVD) for all three conditions using pre-trained evaluation models independent of the generator. (See US-3)
- **FR-006**: System MUST perform a Shapiro-Wilk test for normality on the differences of metric scores; if normality is rejected (p < 0.05), the system MUST default to a Wilcoxon signed-rank test, otherwise use a paired t-test, to determine statistical significance (p < 0.05) between Condition A and Condition C. (See US-3)
- **FR-007**: System MUST identify and log specific failure cases where 2D flow regularization fails to maintain 2D perceptual stability, defined as: (a) object permanence score drops by ≥ 5% compared to the naive baseline, OR (b) VBench temporal consistency score drops by ≥ 0.1 compared to the naive baseline. The system MUST also log a note that these are 2D perceptual proxies and do not guarantee 3D geometric correctness. (See US-3)

### Key Entities

- **VideoSequence**: A collection of frames generated by the MIGA pipeline, associated with a specific prompt and condition (A, B, or C).
- **FlowField**: A 2D vector field representing pixel displacement between two consecutive frames, computed by RAFT-Small.
- **ConsistencyMetric**: A quantitative score (e.g., VBench score, FVD) representing the temporal coherence or visual quality of a VideoSequence.
- **FailureCase**: A specific VideoSequence identified where the 2D perceptual coherence is degraded significantly compared to the naive baseline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Temporal consistency scores (VBench) for Condition C are measured against Condition A to determine the percentage degradation or improvement. (See US-3)
- **SC-002**: Inference latency (wall-clock time) for Condition C is measured against Condition A to quantify the computational trade-off. (See US-3)
- **SC-003**: 2D perceptual stability (object permanence score) is measured against the naive baseline (Condition B) to identify failure modes, defined as a score drop ≥ 5%. (See US-3)
- **SC-004**: Statistical significance of the difference between Condition A and Condition C is measured against a standard significance threshold using a normality-aware test (t-test or Wilcoxon). (See US-3)
- **SC-005**: The total computational resource usage (CPU time, RAM peak) is measured against the free-tier CI limits (multi-core CPU, gigabyte-scale RAM, multi-hour duration) to ensure feasibility. (See US-2)
- **SC-006**: A power analysis report is generated confirming whether N=50 samples provide sufficient statistical power (≥ 0.8) to detect a medium effect size (Cohen's d = 0.5) for the chosen metrics. (See US-3)

## Assumptions

- The NarrLV and VBench datasets are fully available and accessible via HuggingFace without requiring authentication.
- The CI runner disk space is limited to a constrained capacity.
- The RAFT-Small model can be loaded and run in FP16 precision on a CPU-only environment without requiring CUDA or GPU acceleration.
- The MIGA pipeline code is available and compatible with the CPU-only environment, and the self-reflection module can be toggled via command-line arguments.
- The 50 sampled video prompts are sufficient to achieve statistical power for a paired t-test, or the power limitation is explicitly acknowledged in the final report if the sample size is deemed insufficient.
- The pre-trained evaluation models (VBench, FVD) are compatible with the video formats generated by the MIGA pipeline and do not require additional GPU resources to run.
- The 2D optical flow approach is assumed to be insufficient for correcting 3D structural drift in non-planar scenes, and the experiment aims to quantify this limitation via 2D perceptual proxies rather than proving 3D geometric correctness.