# Feature Specification: LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing

**Feature Branch**: `807-liveedit-real-time-diffusion-bas`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing (Paper #408)"

## User Scenarios & Testing

### User Story 1 - Validate End-to-End Execution (Priority: P1)

The researcher MUST be able to execute the vendored `author-kit` submodule code on a standard CPU-only CI runner (GitHub Actions free tier) and confirm that the pipeline completes without runtime errors, producing valid output artifacts (edited video frames or benchmark metrics) that match the paper's reported format.

**Why this priority**: This is the foundational step. Without a successful end-to-end execution, no validation of the paper's claims (real-time performance, visual quality) is possible. It verifies the code is runnable and the environment is correctly configured.

**Independent Test**: Run the provided entry script with default parameters; verify the exit code is 0 and output files exist.

**Acceptance Scenarios**:

1. **Given** the `external/author-kit` submodule is cloned and dependencies are installed, **When** the researcher executes the primary inference script with a sample input video and mask, **Then** the process terminates successfully (exit code 0) and generates at least one output video file or metric log within the 6-hour CI timeout.
2. **Given** the execution environment has no GPU (CPU-only), **When** the script runs, **Then** it must complete using only CPU resources without attempting to load CUDA kernels or failing due to missing GPU drivers.

---

### User Story 2 - Reproduce Quantitative Benchmarks (Priority: P2)

The researcher MUST be able to run the specific benchmark suite defined in the codebase to reproduce the quantitative claims (specifically the inference speed and stability metrics) using the provided sample data or a small representative subset.

**Why this priority**: The core contribution of the paper is the performance improvement (real-time speed). Validating this number is essential to confirming the "Real-Time" claim.

**Independent Test**: Execute the benchmarking script and parse the output log to extract the FPS metric; compare against the paper's reported value (allowing for minor hardware variance).

**Acceptance Scenarios**:

1. **Given** the benchmark configuration is loaded, **When** the evaluation script processes a 5-second video clip, **Then** the output log reports an inference speed (FPS) that is within ±20% of the paper's reported 12.66 FPS (accounting for CPU vs. GPU hardware differences, or confirming the paper's CPU claim if applicable).
2. **Given** the benchmark runs, **When** the stability of non-edited regions is measured, **Then** the system outputs a quantitative metric (e.g., PSNR or SSIM) for background preservation that matches the order of magnitude reported in the paper's results table.

---

### User Story 3 - Validate Qualitative Artifacts (Priority: P3)

The researcher MUST be able to inspect the generated video artifacts to confirm that the "three-stage distillation pipeline" and "AR-oriented mask cache" produce visually stable edits with preserved backgrounds, as claimed in the abstract.

**Why this priority**: While quantitative metrics are critical, the visual quality (content preservation, lack of flickering) is the ultimate proof of the "streaming" and "editing" capabilities.

**Independent Test**: Generate a video output from the script and perform a visual inspection or automated frame-difference analysis to confirm background stability.

**Acceptance Scenarios**:

1. **Given** a video with a static background and a moving mask, **When** the editing pipeline processes the stream, **Then** the generated output video shows the edited region changing while the background remains static (no flickering or drifting) for at least 10 consecutive frames.
2. **Given** the output video, **When** the researcher compares it to the input video using a frame-difference tool, **Then** the difference map shows negligible changes in regions outside the defined mask.

---

### Edge Cases

- **What happens when the input video exceeds the memory limit?** The system MUST handle video loading by processing in chunks or downscaling, failing gracefully with a clear error message rather than crashing the runner (OOM).
- **How does the system handle missing mask inputs?** If the mask cache or input mask is missing, the system MUST default to a "no-op" or a safe failure mode, logging the error and exiting cleanly.
- **What happens if the distillation weights are corrupted?** The validation step MUST detect corrupted model weights (via checksum or load error) and abort with a specific "Model Integrity Failed" error.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `author-kit` inference pipeline on a CPU-only environment without requiring CUDA or GPU acceleration (See US-1).
- **FR-002**: System MUST generate output artifacts (video files or JSON metric logs) that conform to the directory structure defined in the `README.md` of the submodule (See US-1).
- **FR-003**: System MUST report inference speed (FPS) and stability metrics in a machine-readable format for automated benchmarking (See US-2).
- **FR-004**: System MUST maintain background stability in generated frames, ensuring non-masked regions do not exhibit temporal flickering (See US-3).
- **FR-005**: System MUST handle input video files up to 720p resolution within the 7 GB RAM constraint of the CI runner by utilizing chunked processing if necessary (See US-1).

### Key Entities

- **Input Stream**: The raw video file and associated mask definitions provided to the pipeline.
- **Distillation Model**: The lightweight, unidirectional streaming editor model weights loaded from the submodule.
- **Benchmark Result**: The structured output containing FPS, PSNR, and SSIM metrics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The reproduction script completes end-to-end within 6 hours on a GitHub Actions free-tier runner (2 CPU, 7 GB RAM) with [deferred] failure rate across 3 consecutive runs (See US-1).
- **SC-002**: The measured inference speed (FPS) on the reference sample is within ±20% of the paper's reported 12.66 FPS, or explicitly documents the hardware variance if the paper's claim was GPU-based and this run is CPU-only (See US-2).
- **SC-003**: The background preservation metric (PSNR/SSIM) for non-edited regions is ≥ 30 dB (or matches the paper's reported baseline within 5%), confirming the "stable background" claim (See US-2).
- **SC-004**: The generated output video contains no visible flickering artifacts in non-masked regions over a 10-second sequence, as verified by automated frame-difference analysis (See US-3).
- **SC-005**: The system successfully processes the provided sample input without triggering an Out-Of-Memory (OOM) error or exceeding the disk storage limit (See US-1).

## Assumptions

- **Assumption about hardware**: The paper's claim of "12.66 FPS" may have been achieved on a GPU; the reproduction on a CPU-only runner may result in lower FPS, but the *relative* performance improvement and stability claims will remain valid.
- **Assumption about data**: The `author-kit` submodule contains all necessary pre-trained weights and sample data required to run the benchmark without external downloads that might timeout or fail.
- **Assumption about environment**: The GitHub Actions runner has sufficient disk space to unpack the model weights. and process the video samples without needing external storage mounting.
- **Assumption about dependencies**: All Python dependencies listed in the submodule's `requirements.txt` are compatible with the default Python version on the CI runner and do not require compilation from source that would exceed the 6-hour build time.
