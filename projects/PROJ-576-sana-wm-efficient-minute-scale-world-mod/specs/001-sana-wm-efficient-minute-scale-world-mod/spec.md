# Feature Specification: Reproduce & Validate SANA-WM

**Feature Branch**: `576-reproduce-validate-sana-wm`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diffusion Transformer. The code is vendored in external/Sana. Task is to run, validate, and reproduce the shipped implementation end-to-end."

## User Scenarios & Testing

### User Story 1 - Execute Minimum Viable Inference Pipeline (Priority: P1)

The researcher MUST be able to trigger the core SANA-WM inference pipeline using a pre-trained checkpoint and a sample prompt to verify the system initializes, loads the model, and generates a video artifact without crashing on the CPU-only runner.

**Why this priority**: This is the absolute baseline for a reproduction project. If the code cannot execute a single forward pass or inference step, the project cannot proceed to validation or benchmarking. It confirms the environment setup, dependency resolution, and model loading logic work.

**Independent Test**: Execute the entry point `diffusion/longsana/pipeline/sana_inference_pipeline.py` (or the equivalent CLI wrapper) with a minimal configuration and a fixed text prompt. The test passes if a video file (`.mp4` or `.webm`) is written to the output directory and the process exits with code 0.

**Acceptance Scenarios**:

1. **Given** the `external/Sana` submodule is initialized and dependencies are installed, **When** the researcher runs the inference CLI with a sample prompt "A cat walking on a leash" and a short duration (e.g., 4 seconds), **Then** a video file is generated in the output folder and no CUDA/GPU errors are raised.
2. **Given** the environment has no GPU available (CPU-only runner), **When** the inference script is launched with default precision settings (bf16/fp32) but explicitly disabled GPU flags, **Then** the script successfully offloads to CPU and completes the generation within the 6-hour job limit.

---

### User Story 2 - Validate 6-DoF Camera Control & Trajectory Adherence (Priority: P2)

The researcher MUST be able to generate a video using specific camera pose parameters (intrinsic/extrinsic matrices) provided in the demo data and verify that the output video visually adheres to the specified camera trajectory.

**Why this priority**: The paper's core claim is "precise 6-DoF trajectory adherence." Validating this distinguishes a generic video generator from the specific "World Model" claims of SANA-WM. This requires running the specific camera-control pipeline and comparing the output against the provided ground-truth pose data.

**Independent Test**: Run the `sana_wm` specific pipeline using the demo `.npy` pose files (`demo_0_pose.npy`, etc.) and verify the output video frames correspond to the expected camera motion path (e.g., pan, tilt, zoom) without significant drift or hallucination of incorrect geometry.

**Acceptance Scenarios**:

1. **Given** the demo dataset containing `demo_0_pose.npy` and `demo_0_intrinsics.npy`, **When** the researcher runs the SANA-WM inference with these pose inputs, **Then** the generated video shows a camera movement consistent with the pose trajectory (e.g., smooth rotation/translation) rather than a static or random camera path.
2. **Given** a set of 5 distinct camera trajectories from the demo data, **When** the system generates videos for each, **Then** at least 4 out of 5 videos demonstrate successful adherence to the input trajectory without catastrophic failure (e.g., warping, color shifts, or freezing).

---

### User Story 3 - Benchmark Throughput & Resource Usage on CPU (Priority: P3)

The researcher MUST measure the inference time and peak memory usage of generating a standard-length clip (e.g., 4-10 seconds) on the CI runner to establish a baseline for the "efficient" claims, even if the full minute-scale generation is deferred due to resource constraints.

**Why this priority**: The paper claims "minute-scale generation" and high throughput. While generating a full 60s clip on a 2-core CPU runner may be infeasible within 6 hours, measuring the throughput on a shorter segment (e.g., 4s) provides the necessary data to extrapolate feasibility and validate the "efficient" aspect of the model architecture.

**Independent Test**: Run a timed inference job for a 4-second clip. Record the wall-clock time and peak RAM usage. Compare the time-per-frame or frames-per-second against the paper's reported metrics (scaled for CPU vs GPU).

**Acceptance Scenarios**:

1. **Given** a 4-second generation request with 720p resolution, **When** the job completes on the CPU runner, **Then** the total execution time is recorded and does not exceed 4 hours (allowing for CI overhead).
2. **Given** the process completes, **When** the resource logs are parsed, **Then** the peak RAM usage is documented and confirmed to be under 7 GB (the runner limit).

---

### Edge Cases

- **Memory Exhaustion**: If the model loading or batch processing exceeds 7 GB RAM, the system MUST fail gracefully with a clear error message suggesting downsampling or frame-skipping, rather than a silent OOM crash.
- **Missing Checkpoints**: If the required pre-trained weights for SANA-WM are not present in the submodule (e.g., due to LFS limits), the system MUST detect this and halt with a specific instruction to download the weights, rather than attempting to train from scratch.
- **CUDA Fallback Failure**: If the code attempts to initialize CUDA and fails (expected on CPU runner), it MUST automatically fallback to CPU execution mode without requiring manual code modification.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the SANA-WM model architecture and weights from the `external/Sana` submodule without requiring manual code refactoring for CPU execution. (See US-1)
- **FR-002**: System MUST support inference with explicit CPU-only execution flags, disabling all CUDA/GPU initialization paths. (See US-1)
- **FR-003**: System MUST accept external 6-DoF camera pose matrices (`.npy` files) as input and apply them to the generation process. (See US-2)
- **FR-004**: System MUST generate video output in a standard format (`.mp4` or `.webm`) with a minimum resolution of 480p and duration of at least 4 seconds. (See US-1)
- **FR-005**: System MUST log runtime metrics including total inference time, frames generated, and peak memory usage to a JSON report file upon completion. (See US-3)
- **FR-006**: System MUST validate that the input camera pose files exist and match the expected dimensions before starting generation. (See US-2)

### Key Entities

- **CameraPose**: A data structure containing intrinsic and extrinsic matrices defining the camera's position and orientation in 3D space for each frame.
- **GeneratedVideo**: The output artifact containing the synthesized video frames adhering to the input prompt and camera trajectory.
- **InferenceConfig**: A configuration object specifying resolution, duration, sampling steps, and hardware target (CPU/GPU).

## Success Criteria

### Measurable Outcomes

- **SC-001**: Inference success rate is measured against the total number of attempted runs; target is ≥ 100% successful completion of the P1 test case (US-1) without runtime errors. (See FR-001, FR-002)
- **SC-002**: Camera adherence accuracy is measured by visual inspection of the output video against the input pose trajectory; target is ≥ 80% of generated videos (4 out of 5) showing correct motion direction and smoothness (US-2). (See FR-003, FR-006)
- **SC-003**: Resource feasibility is measured by peak RAM usage; target is < 7 GB for the 4-second generation task (US-3). (See FR-005)
- **SC-004**: Execution time is measured against the 6-hour CI limit; target is completion of the 4-second generation task within ≤ 4 hours to allow for retries and logging (US-3). (See FR-005)
- **SC-005**: Artifact validity is measured by the presence of a non-empty video file with the correct extension; target is [deferred] of runs producing a valid video file (US-1). (See FR-004)

## Assumptions

- **Assumption about model weights**: The required pre-trained SANA-WM checkpoint files are available via the submodule's Git LFS or a direct download link provided in the `external/Sana` repository, and will be successfully fetched during the CI setup phase.
- **Assumption about hardware constraints**: The GitHub Actions free-tier runner (vCPU, 7 GB RAM) is sufficient to run a *reduced* inference pass (e.g., 4 seconds, lower resolution, or fewer sampling steps) of the B parameter model, even if the full 60s generation is computationally prohibitive.
- **Assumption about software dependencies**: The `external/Sana` repository's `requirements.txt` or `pyproject.toml` lists all necessary dependencies that are compatible with the Python version and OS of the standard GitHub Actions runner.
- **Assumption about dataset availability**: The demo data (`.npy` pose files, sample prompts) included in the `asset/sana_wm` directory of the submodule is complete and valid for running the validation tests.
- **Assumption about CPU performance**: The multi-core CPU runner can execute the diffusion denoising steps for a short clip within the 6-hour limit, even if it takes significantly longer than the paper's reported GPU time (e.g., seconds on RTX 5090 vs. several hours on CPU).
