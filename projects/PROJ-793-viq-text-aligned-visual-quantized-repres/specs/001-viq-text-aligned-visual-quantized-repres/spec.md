# Feature Specification: Reproduce & validate: ViQ: Text-Aligned Visual Quantized Representations at Any Resolution

**Feature Branch**: `793-viq-text-aligned-visual-quantized-repres`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: ViQ: Text-Aligned Visual Quantized Representations at Any Resolution"

## User Scenarios & Testing

### User Story 1 - Environment Setup & Sanity Check (Priority: P1)

**Description**: A researcher sets up the Python environment for the vendored ViQ codebase and runs the provided example script to verify that the code executes without import errors or immediate crashes on a CPU-only runner.

**Why this priority**: Without a functioning environment and a successful "hello world" execution, no further validation of the paper's claims is possible. This is the foundational step for any reproduction project.

**Independent Test**: Execute the `scripts/example.sh` script (or equivalent Python entry point) using the provided `example_dataset` and verify that it completes without a Python exception and generates at least one output artifact (e.g., a log file, a reconstructed image, or a JSON result).

**Acceptance Scenarios**:

1. **Given** the `external/ViQ` submodule is cloned and the `requirements.txt` is installed, **When** the user runs the example inference script on `scripts/example_dataset/images/red_circle.png`, **Then** the script exits with code 0 and produces a valid output file (e.g., `output_red_circle.png` or `result.json`) in the designated output directory.
2. **Given** the environment is initialized, **When** the user attempts to import `viq_inference.ViQ` in a fresh Python session, **Then** no `ImportError` or `ModuleNotFoundError` occurs, and all core dependencies (torch, transformers, etc.) load successfully.

---

### User Story 2 - Quantization & Reconstruction Validation (Priority: P2)

**Description**: A researcher validates the core claim of the ViQ paper—that the model can balance semantic information and low-level detail—by running the inference pipeline on a set of test images and comparing the reconstructed outputs against the originals.

**Why this priority**: This directly tests the primary technical contribution (the quantization mechanism) described in the abstract. It moves beyond "does it run" to "does it do what the paper says."

**Independent Test**: Run the inference pipeline on the `example_dataset` images and compute standard reconstruction metrics (e.g., PSNR, SSIM) or perform a visual inspection to confirm that the output images retain recognizable features and color fidelity.

**Acceptance Scenarios**:

1. **Given** the model weights are loaded and the inference script is configured for reconstruction, **When** the script processes `scripts/example_dataset/images/blue_square.png`, **Then** the reconstructed image preserves the square shape and blue color with a visible structural similarity (visually indistinguishable at a glance or PSNR > 20 dB if calculated).
2. **Given** the inference pipeline is running, **When** it processes an image with multiple distinct objects (e.g., `green_triangle.png` and `red_circle.png` if combined), **Then** the output maintains the spatial arrangement and distinct colors of all objects without significant blurring or hallucination.

---

### User Story 3 - Performance & Efficiency Reporting (Priority: P3)

**Description**: A researcher measures the inference time and resource utilization of the ViQ pipeline to verify the paper's claim of "[deferred]-70% acceleration" compared to continuous high-dimensional features, specifically within the constraints of a CPU-only environment.

**Why this priority**: This validates the efficiency claims of the paper. While the exact percentage acceleration depends on the baseline comparison (which may be complex to setup), measuring the absolute runtime and memory footprint is a necessary step to determine feasibility on the target hardware.

**Independent Test**: Execute the inference script with timing enabled and monitor the peak RAM usage and total wall-clock time for the example dataset.

**Acceptance Scenarios**:

1. **Given** the inference script is instrumented with a timer, **When** it processes the full `example_dataset` (4 images), **Then** the total wall-clock time is recorded and reported in the logs, and the process completes within the predefined CI time limit.
2. **Given** the system is running on the free-tier runner (GB RAM limit), **When** the inference script processes a standard input image, **Then** the peak RAM usage remains within acceptable system limits, ensuring the process does not get OOM-killed.

---

### Edge Cases

- **What happens when** the input image resolution is significantly larger than the example dataset (e.g., 4K)? The system must handle "Any Resolution" claims without crashing, potentially by downsampling or tiling, but the spec must clarify if the current example script supports this or if it's a limitation.
- **How does system handle** missing model weights? If the `external/ViQ` submodule does not include pre-trained weights (common in repos), the spec must define whether the test is "runnable" (code works) or "reproducible" (results match paper). Currently, we assume the test is "runnable" with random or default initialization if weights are missing, or that weights are provided in the repo.
- **What happens when** the CPU-only constraint causes a specific CUDA-dependent operation to fail? The system must explicitly fail with a clear error message indicating "CUDA required" rather than hanging or producing garbage, allowing the researcher to identify the incompatibility.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `viq_inference/ViQ.py` entry point using the provided `scripts/example.sh` configuration without modification to the core logic. (See US-1)
- **FR-002**: System MUST successfully load the example dataset images (`red_circle.png`, `blue_square.png`, etc.) and process them through the ViQ quantization pipeline. (See US-2)
- **FR-003**: System MUST generate output artifacts (reconstructed images or JSON logs) for every input image in the test dataset. (See US-2)
- **FR-004**: System MUST complete the full inference pipeline for the example dataset within 6 hours on a CPU-only runner. (See US-3)
- **FR-005**: System MUST log peak memory usage and total execution time for the inference process to stdout or a dedicated log file. (See US-3)
- **FR-006**: System MUST explicitly detect and report if any operation requires GPU/CUDA and fail gracefully with a clear error message if GPU is unavailable. (See US-1, US-3)

### Key Entities

- **Input Image**: A standard image file (PNG/JPG) from the example dataset used as the source for quantization.
- **Quantized Representation**: The intermediate discrete feature vector generated by the ViQ model, which serves as the unified representation.
- **Reconstructed Image**: The output image generated by decoding the quantized representation, used to validate fidelity.
- **Inference Log**: A text or JSON file containing timing, memory usage, and success/failure status of the run.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of successfully processed images is measured against the total count of images in `scripts/example_dataset` (Source: `scripts/example_dataset/`). (See US-2)
- **SC-002**: The peak RAM usage of the inference process is measured against the free-tier runner's storage limit (Source: GitHub Actions runner specifications). (See US-3)
- **SC-003**: The total wall-clock execution time is measured against the 6-hour job timeout limit (Source: GitHub Actions runner specifications). (See US-3)
- **SC-004**: The presence of output artifacts (reconstructed images) is measured against the requirement that every input image must produce a corresponding output (Source: FR-003). (See US-2)
- **SC-005**: The error log is measured for the presence of "CUDA required" or similar GPU-specific errors to confirm CPU-only compatibility (Source: FR-006). (See US-1)

## Assumptions

- The `external/ViQ` submodule contains all necessary Python source files and the `scripts/example_dataset` is complete and valid.
- The repository does not require downloading large pre-trained weights at runtime; if weights are missing, the test assumes "code execution" is the success metric, not "result matching."
- The ViQ implementation in the submodule has been updated or is compatible with CPU execution for the inference phase (i.e., no hard-coded `device='cuda'` that cannot be overridden by environment variables or arguments).
- The example dataset images are small enough (resolution and file size) to fit within the 7 GB RAM limit when processed by the model.
- The `scripts/example.sh` script uses a default configuration that is compatible with the CPU-only environment (e.g., does not force mixed-precision training or GPU-specific flags).
- The paper's claim of "[deferred]-70% acceleration" is relative to a specific baseline (likely a continuous model) which is not present in this repo; therefore, the spec focuses on measuring absolute runtime rather than relative speedup.
