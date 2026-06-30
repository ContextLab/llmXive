# Feature Specification: Reproduce & Validate LongLive-2.0 NVFP4 Infrastructure

**Feature Branch**: `001-reproduce-longlive-2-0`  
**Created**: 2025-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

## User Scenarios & Testing

### User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1)

The research engineer MUST successfully initialize the project environment on a CPU-only CI runner (GitHub Actions free tier: vCPU, 7GB RAM) by resolving all Python dependencies and verifying the `fouroversix` library is importable without requiring GPU-specific CUDA kernels to be active for basic validation.

**Why this priority**: Without a functional environment, no code execution or validation can occur. This is the foundational step; if the environment fails to build due to GPU-only requirements (e.g., mandatory CUDA compilation for `fouroversix`), the project cannot proceed to the `research_complete` stage on the target infrastructure.

**Independent Test**: A `pip install -r requirements.txt` and a `python -c "import fouroversix"` command run in a clean CPU-only container must complete without error, confirming the library is loadable in the target environment.

**Acceptance Scenarios**:

1. **Given** a clean GitHub Actions runner (2 vCPU, 7GB RAM, no GPU), **When** the user executes `pip install -r requirements.txt`, **Then** the installation completes with exit code 0 and no errors related to missing CUDA libraries (unless optional).
2. **Given** the installed dependencies, **When** the user runs `python -c "import fouroversix"`, **Then** the import succeeds without triggering `ImportError` or `RuntimeError` regarding missing CUDA devices.
3. **Given** the environment is initialized, **When** the user runs `python -c "from fouroversix.quantize import fp4_quant"`, **Then** the module loads, confirming the quantization backend is available for CPU fallback testing.

---

### User Story 2 - Inference Pipeline Execution on Sample Data (Priority: P2)

The researcher MUST execute the `inference.py` script (or `inference_sp.py` if sequence parallel is required for memory) using a minimal, synthetic, or downsampled video prompt to verify the model pipeline runs end-to-end and produces a valid video artifact (e.g., `.mp4` or `.webm`) without crashing due to out-of-memory (OOM) errors or missing checkpoints.

**Why this priority**: The core value proposition is the ability to *run* the LongLive-2.0 infrastructure. Generating a single video artifact confirms the pipeline logic, VAE decoding, and diffusion sampling steps function correctly on the target hardware.

**Independent Test**: Run the inference script with a configuration pointing to a small test prompt (e.g., `example/long_example.txt` or a synthetic 2-frame sequence) and verify a video file is written to the output directory.

**Acceptance Scenarios**:

1. **Given** a valid inference configuration (`configs/inference.yaml`) and a test prompt, **When** the user executes `python inference.py`, **Then** the process completes within 60 minutes and writes a video file to `outputs/`.
2. **Given** the video file is generated, **When** the user inspects the file metadata, **Then** the file is a valid video format (e.g., MP4) with a duration of at least 1 second.
3. **Given** the inference runs on CPU, **When** the process executes, **Then** it does not request GPU memory (no `cudaMalloc` calls) and completes without OOM errors on the GB RAM limit.

---

### User Story 3 - Validation of NVFP4 Quantization and Performance Claims (Priority: P3)

The researcher MUST validate that the NVFP4 quantization path (if available on CPU via fallback or emulation) or the standard precision path produces results consistent with the paper's claimed behavior (e.g., no NaNs, reasonable frame generation) and document the performance metrics (FPS, memory usage) to compare against the paper's reported baseline performance. (noting the hardware difference).

**Why this priority**: This validates the *scientific* claim of the paper. While exact FPS replication is impossible on CPU vs. Blackwell GPUs, the structural validity of the quantization and the absence of numerical instability are required to confirm the "infrastructure" works as described.

**Independent Test**: Execute the inference with NVFP4 configuration (if supported) or standard precision, capture memory usage and frame generation time, and log these metrics to a report file.

**Acceptance Scenarios**:

1. **Given** the inference script runs, **When** the user enables NVFP4 quantization (via `configs/nvfp4/inference_nvfp4.yaml`), **Then** the system logs the quantization mode and produces output without numerical instability (NaNs).
2. **Given** the video generation completes, **When** the user queries the memory profile, **Then** the peak RAM usage is recorded and reported in `results/metrics.json`.
3. **Given** the results are generated, **When** the user compares them to the paper's abstract, **Then** the report explicitly states the hardware difference (CPU vs. Blackwell) and notes that FPS is not directly comparable but structural validity is confirmed.

### Edge Cases

- **What happens when CUDA is unavailable?** The system MUST gracefully degrade to CPU execution or fail with a clear error message indicating GPU requirements are not met, rather than crashing silently.
- **How does the system handle missing pre-trained weights?** If the checkpoint files (e.g., `LongLive-2.0-5B`) are not present in the submodule, the script MUST fail immediately with a "Checkpoint not found" error, preventing partial execution.
- **What happens if RAM exceeds 7GB?** The inference MUST be configured to use sequence parallelism (`inference_sp.py`) or downsampled frames to stay within the 7GB limit; if it exceeds, it MUST raise an OOM error rather than swapping to disk (which would exceed the 6h time limit).

## Requirements

### Functional Requirements

- **FR-001**: System MUST initialize the Python environment and install all dependencies defined in `requirements.txt` without requiring GPU drivers to be present. (See US-1)
- **FR-002**: System MUST successfully import the `fouroversix` library and its quantization modules on a CPU-only runtime. (See US-1)
- **FR-003**: System MUST execute the `inference.py` entry point using a provided configuration file and a text prompt. (See US-2)
- **FR-004**: System MUST generate a valid video artifact (e.g., `.mp4`) as the final output of the inference pipeline. (See US-2)
- **FR-005**: System MUST log peak memory usage and execution time for the inference run to a structured report file. (See US-3)
- **FR-006**: System MUST handle the absence of pre-trained checkpoints by failing gracefully with an explicit error message rather than proceeding with random weights. (See US-2)
- **FR-007**: System MUST support sequence parallelism (`inference_sp.py`) as a fallback path if standard inference exceeds memory limits. (See US-2)

### Key Entities

- **Configuration**: YAML files defining model architecture, quantization mode (NVFP4 vs. FP16), and inference parameters.
- **Checkpoint**: Pre-trained model weights (e.g., `LongLive-2.0-5B`) required for inference.
- **Artifact**: The generated video file produced by the pipeline.
- **Metric**: Structured data recording memory usage, FPS, and runtime.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Environment initialization success rate is measured against the requirement of zero `ImportError` or `CUDA` dependency failures on a standard CPU-only runner. (See FR-001, FR-002)
- **SC-002**: Video generation success rate is measured against the requirement that a valid video file is produced for all valid prompt inputs within the -hour CI limit. (See FR-003, FR-004)
- **SC-003**: Memory efficiency is measured against the constraint of peak RAM usage ≤ 7 GB during inference execution. (See FR-005)
- **SC-004**: Numerical stability is measured against the absence of NaN or Inf values in the generated video latent space or pixel output. (See FR-005)
- **SC-005**: Reproducibility fidelity is measured by the ability to run the provided `example/long_example.txt` prompt and produce an artifact matching the expected format (MP4/WebM) as described in the paper's demo. (See FR-003)

## Assumptions

- The `fouroversix` library provides a CPU-compatible fallback for NVFP4 quantization or the project accepts running in standard precision (FP16) on CPU for validation purposes, as true NVFP4 hardware acceleration is Blackwell-specific.
- Pre-trained checkpoints (e.g., `LongLive-2.0-5B`) are either available in the submodule or can be downloaded from the official source without violating CI bandwidth limits.
- The "long video" generation capability is validated via a short, synthetic sequence (e.g., -4 seconds) due to the A defined time limit for the experimental phase. and memory constraints of the free-tier runner, rather than full-length generation.
- The `inference_sp.py` script is functional and correctly implements sequence parallelism for CPU execution, or the standard `inference.py` is sufficient for the memory profile of the test sequence.
- The GitHub Actions runner provides sufficient disk space (≥14 GB) to store the model weights and temporary artifacts.
