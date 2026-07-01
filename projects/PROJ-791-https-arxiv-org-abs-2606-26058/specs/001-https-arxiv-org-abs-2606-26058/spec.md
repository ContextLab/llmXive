# Feature Specification: DomainShuttle Reproduction & Validation

**Feature Branch**: `791-domainshuttle-reproduction`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: DomainShuttle: Freeform Open Domain Subject-driven Text-to-video Generation"

## User Scenarios & Testing

### User Story 1 - Environment Setup & Dependency Resolution (Priority: P1)

**Journey**: The CI runner successfully clones the vendored `DomainShuttle` submodule, resolves all Python dependencies, and configures the environment to run inference scripts without GPU acceleration.

**Why this priority**: Without a runnable environment, no validation can occur. This is the foundational step that unblocks all subsequent testing.

**Independent Test**: Can be fully tested by executing the `install.py` script and verifying that all required Python packages are installed and importable in a CPU-only context.

**Acceptance Scenarios**:

1. **Given** a clean GitHub Actions runner (2 CPU, 7GB RAM, no GPU), **When** the `install.py` script is executed, **Then** all dependencies listed in `requirements.txt` are installed successfully without CUDA/GPU-specific errors (e.g., `bitsandbytes` installation failures).
2. **Given** the installed environment, **When** a minimal Python script imports the core `DomainShuttle` modules, **Then** the import succeeds without `ImportError` or `ModuleNotFoundError`.

---

### User Story 2 - CPU-Tractable Inference Execution (Priority: P2)

**Journey**: The system executes a single, short-form Subject-to-Video (S2V) or Text-to-Video (T2V) generation using a quantized or lightweight model configuration on the CPU-only runner, producing a valid video artifact.

**Why this priority**: This validates the core claim that the vendored code can actually run and produce artifacts within the strict compute constraints (no GPU, <6h).

**Independent Test**: Can be tested by running a specific inference script (e.g., `examples/wan2.2_fun/predict_s2v.py` with a small sample) and verifying the output video file exists and is playable.

**Acceptance Scenarios**:

1. **Given** a valid reference image and text prompt, **When** the `predict_s2v.py` script is executed with `--cpu-only` flags and a reduced frame count (e.g., 16 frames), **Then** the process completes within 6 hours and outputs a `.mp4` file of non-zero size.
2. **Given** the execution environment, **When** the script attempts to load the model, **Then** it explicitly avoids loading 8-bit/4-bit quantization layers that require CUDA (e.g., `load_in_8bit=False`) and runs in standard float32/float16 precision on CPU.

---

### User Story 3 - Artifact Validation & Reproducibility Reporting (Priority: P3)

**Journey**: The system validates that the generated video artifacts meet the basic structural requirements (duration, resolution, format) and generates a report comparing the results against the paper's qualitative claims.

**Why this priority**: This confirms the "reproduction" aspect of the project, ensuring the artifacts are not just generated but are valid representations of the method.

**Independent Test**: Can be tested by running a validation script that checks video metadata and generates a summary report.

**Acceptance Scenarios**:

1. **Given** a generated video file, **When** the validation script analyzes the file, **Then** the video duration is ≥ 2 seconds, resolution matches the config (e.g., 512x512 or 832x480), and the file format is `.mp4` or `.gif`.
2. **Given** the generated artifacts, **When** a summary report is generated, **Then** it explicitly states whether the output visually demonstrates "subject fidelity" or "cross-domain flexibility" as claimed in the paper's abstract, based on the specific test case used.

---

### Edge Cases

- **Memory Overflow**: What happens when the model loading exceeds the 7GB RAM limit? The system must catch `MemoryError` and gracefully exit with a specific error code, logging the memory peak.
- **Missing Reference Data**: How does the system handle the `datasets/put datasets here.txt` placeholder? The script must fail gracefully with a clear message indicating that reference images are missing, rather than crashing with a generic file-not-found error.
- **CPU Timeout**: If the inference exceeds the 6-hour limit (unlikely for a single short clip but possible for large models), the job must be terminated and marked as "Timeout" rather than hanging indefinitely.

## Requirements

### Functional Requirements

- **FR-001**: System MUST install and configure the `DomainShuttle` codebase from the vendored submodule without requiring GPU-specific dependencies (e.g., `bitsandbytes`, `cuda`), ensuring compatibility with CPU-only runners (See US-1).
- **FR-002**: System MUST execute a subject-driven text-to-video inference script using a lightweight model configuration (e.g., `wan2.2_fun` with reduced frames) on a CPU-only environment, completing the task within 6 hours (See US-2).
- **FR-003**: Users MUST be able to trigger the generation process via a command-line interface that accepts a reference image path, a text prompt, and a configuration file (See US-2).
- **FR-004**: System MUST validate the output artifact by checking file existence, format (`.mp4`), resolution, and duration against the configuration parameters (See US-3).
- **FR-005**: System MUST generate a reproduction report that documents the execution time, memory usage peak, and a qualitative assessment of the generated video against the paper's claims (See US-3).
- **FR-006**: System MUST explicitly disable any CUDA-specific acceleration flags (e.g., `device_map="cuda"`, `load_in_8bit`) during model loading to prevent runtime crashes on CPU-only runners (See US-2).

### Key Entities

- **Reference Image**: A static image file serving as the subject for the video generation.
- **Text Prompt**: A natural language string describing the desired action or scene.
- **Generated Video**: The output artifact (`.mp4`) produced by the inference engine.
- **Reproduction Report**: A structured output (Markdown/JSON) summarizing the run's success metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Inference execution time is measured against the 6-hour CI job limit to ensure feasibility on free-tier runners (See FR-002).
- **SC-002**: Memory usage peak is measured against the 7GB RAM limit of the GitHub Actions runner to confirm the model fits within the constraint (See FR-002, FR-006).
- **SC-003**: Artifact validity rate is measured against the requirement that [deferred] of generated videos must be non-corrupt, playable, and match the configured resolution (See FR-004).
- **SC-004**: Dependency resolution success is measured against the absence of `ImportError` or `ModuleNotFoundError` for core `DomainShuttle` modules in a CPU-only environment (See FR-001).

## Assumptions

- **Assumption about compute constraints**: The `DomainShuttle` codebase, when configured for CPU execution (disabling 8-bit quantization), will fit within the 7GB RAM and 14GB disk limits of the GitHub Actions free-tier runner for a single short-form generation task.
- **Assumption about model availability**: The necessary model weights (e.g., `wan2.2`, `flux`) are either available via Hugging Face Hub or can be downloaded during the run within the 14GB disk limit; if weights are too large, the spec assumes a "smoke test" using a smaller, pre-downloaded subset or a different lightweight model variant is acceptable for validation.
- **Assumption about dataset scope**: The reproduction does not require the full training dataset mentioned in `datasets/put datasets here.txt`; only a single reference image and a text prompt are required to validate the inference pipeline.
- **Assumption about paper claims**: The paper's claims regarding "subject fidelity" and "cross-domain flexibility" are qualitative and will be assessed via visual inspection in the reproduction report rather than automated quantitative metrics (e.g., FID, CLIP score) which may require additional computational overhead or specific datasets not present.
- **Assumption about code stability**: The vendored code in the `DomainShuttle` submodule is stable and does not contain hard-coded paths or dependencies that are specific to the original author's local environment.
