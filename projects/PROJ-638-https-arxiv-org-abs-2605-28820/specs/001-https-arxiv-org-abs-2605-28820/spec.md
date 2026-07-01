# Feature Specification: Reproduce & Validate NEO-ov One-Vision Model

**Feature Branch**: `001-reproduce-neo-ov`  
**Created**: 2026-05-31  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: From Pixels to Words -- Towards Native One-Vision Models at Scale"

## User Scenarios & Testing

### User Story 1 - Validate Execution Pipeline on Sample Data (Priority: P1)

**Description**: As a researcher, I need to execute the vendored NEO-ov codebase on a minimal, CPU-tractable subset of a benchmark dataset to confirm the pipeline initializes, runs without CUDA/GPU dependencies, and produces valid output artifacts (logs, predictions, or metrics) within the 6-hour CI limit.

**Why this priority**: This is the absolute baseline. If the code cannot run on the available free-tier hardware (2 CPU, ~7 GB RAM, no GPU), the project cannot proceed to any scientific validation. It verifies the "compute feasibility" constraint explicitly.

**Independent Test**: The CI job runs `VLMEvalKit/run.py` against a single dataset sample (e.g., 5 images from MMBench) using only CPU. Success is defined by the script exiting with code 0 and generating a JSON/CSV result file containing non-empty predictions.

**Acceptance Scenarios**:

1. **Given** the NEO-ov submodule is checked out and dependencies are installed, **When** the user executes the smoke test script (`smoke_test_neo_si.py` or a minimal `run.py` invocation) on a 5-sample subset with CPU-only flags, **Then** the process completes in [deferred] and outputs a result file with at least 5 valid prediction entries.
2. **Given** a standard CI runner environment (no NVIDIA drivers), **When** the user attempts to run the training or inference entry point, **Then** the system does not raise a CUDA/GPU import error and completes the inference loop successfully.

---

### User Story 2 - Reproduce Benchmark Metrics on a Representative Dataset (Priority: P2)

**Description**: As a reviewer, I need to see the NEO-ov model evaluated on a standard, medium-sized benchmark (e.g., MMBench or ScienceQA) to verify that the model produces competitive or plausible performance metrics consistent with the paper's claims, without requiring full-scale training.

**Why this priority**: This moves beyond "it runs" to "it works." It validates the model's capability to process visual-language tasks and generate the specific metrics (accuracy, F1, etc.) claimed in the paper, serving as the primary scientific validation step.

**Independent Test**: The system runs the evaluation script against a predefined dataset subset (e.g., a representative sample) and generates a summary report. Success is defined by the report containing numeric scores that match the paper's reported range (within a reasonable variance for sample size) and a valid JSON artifact.

**Acceptance Scenarios**:

1. **Given** the model weights are loaded (or a pre-trained checkpoint is available in the submodule), **When** the evaluation is run on 500 samples of the MMBench dataset, **Then** the output report includes a final accuracy score and a breakdown per category, with no NaN or infinite values.
2. **Given** the execution completes, **When** the generated results are compared against the paper's Table 1 (or equivalent), **Then** the observed performance is within ±10% of the reported values (adjusting for the smaller sample size), confirming the model is not broken.

---

### User Story 3 - Document Methodological Constraints and Scaling Limitations (Priority: P3)

**Description**: As a methodologist, I need the spec and final report to explicitly address the reviewer's critique regarding "at Scale" by documenting the absence of a formal scaling law analysis (power-law fits, exponents) and clarifying the scope of the validation.

**Why this priority**: The reviewer (Geoffrey West) flagged the title's claim of "at Scale" as unsupported by the manuscript's lack of quantitative scaling analysis. This story ensures the project acknowledges this limitation transparently, preventing the "unfilled template" or "mismatch" verdict later.

**Independent Test**: The final validation report includes a dedicated section explicitly stating that the validation is limited to functional reproduction on fixed-size models and datasets, and that no scaling exponents were computed.

**Acceptance Scenarios**:

1. **Given** the validation report is generated, **When** a human reviewer scans the "Limitations" or "Methodological Notes" section, **Then** they find a clear statement acknowledging that the "at Scale" claim in the title was not validated via scaling law analysis (e.g., no exponent fitting performed).
2. **Given** the project scope, **When** the spec defines the "Scale" parameter, **Then** it is explicitly defined as "model architecture scale" (e.g., parameter count) rather than "data/compute scaling law," with a note that the latter is out of scope for this reproduction run.

---

### Edge Cases

- **What happens when the model weights are missing or corrupted?** The system MUST detect missing checkpoint files during initialization and exit with a clear error code (e.g., 1) and a message directing the user to download the weights, rather than crashing with a generic traceback.
- **How does the system handle datasets that require GPU-accelerated preprocessing?** The system MUST fallback to a CPU-compatible preprocessing path or skip the specific dataset, logging a warning that the dataset was skipped due to hardware constraints, rather than failing the entire job.
- **What happens if the 6-hour CI timeout is approached?** The system MUST implement a checkpointing mechanism or a sample-size limiter (e.g., cap at a reasonable sample size) to ensure the job completes within the 6-hour window, logging a "truncated due to time limit" status if necessary.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the NEO-ov inference pipeline on a CPU-only environment (no CUDA, no GPU) to process at least 500 samples from a standard benchmark (e.g., MMBench) within 6 hours. (See US-1)
- **FR-002**: System MUST generate a structured JSON or CSV artifact containing model predictions and ground-truth comparisons for every processed sample. (See US-2)
- **FR-003**: System MUST calculate and report aggregate performance metrics (e.g., accuracy, exact match) with at least 3 decimal places of precision. (See US-2)
- **FR-004**: System MUST explicitly log a warning or error if any required dependency (e.g., `torch`, `transformers`) is missing or incompatible with the CPU-only constraint. (See US-1)
- **FR-005**: System MUST include a "Methodological Notes" section in the final report that explicitly states the validation did not perform a quantitative scaling law analysis (exponent fitting) and defines "Scale" as architectural size only. (See US-3)
- **FR-006**: System MUST implement a hard limit on the number of samples processed (≤ 1000) to ensure the total compute time does not exceed 6 hours on a 2-core runner. (See US-1)

### Key Entities

- **Benchmark Dataset**: A collection of image-text pairs (e.g., from MMBench, ScienceQA) used as the input for validation.
- **Prediction Artifact**: A structured file (JSON/CSV) containing the model's output text, confidence scores, and the corresponding ground truth label.
- **Validation Report**: A Markdown document summarizing the execution status, performance metrics, and methodological limitations.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The inference pipeline completes successfully on ≥ 95% of the 500-sample subset without crashing or raising CUDA errors. (Measured against: Execution log output; See FR-001, FR-004)
- **SC-002**: The generated prediction artifact contains ≥ 475 valid entries ([deferred] of 500) with non-empty text predictions. (Measured against: Artifact file row count; See FR-002)
- **SC-003**: The reported aggregate accuracy is a finite number between 0.0 and 1.0, with no NaN or Infinity values. (Measured against: Summary metric value; See FR-003)
- **SC-004**: The final report explicitly contains the phrase "scaling law analysis" in a negative context (e.g., "not performed") or a similar explicit limitation statement. (Measured against: Text search in report; See FR-005)
- **SC-005**: The total wall-clock time for the validation run is ≤ 6 hours. (Measured against: CI job duration; See FR-006)

## Assumptions

- The NEO-ov model weights are available in the submodule or can be downloaded from the provided GitHub URL without requiring a paid API key or proprietary access.
- The "Scale" claim in the paper title refers to the architectural capacity (parameter count) of the NEO-ov model rather than a quantitative scaling law (e.g., power-law exponents), which is acknowledged as a limitation in the validation scope.
- The `VLMEvalKit` and `NEO` codebases are compatible with Python 3.x+ and standard CPU-only PyTorch installations (no 8-bit quantization or CUDA-specific kernels).
- The dataset samples (images) can be processed within the ~7 GB RAM limit by loading them one-by-one or in small batches (≤ 4 images) without OOM errors.
- The paper's reported metrics are based on a specific checkpoint version that matches the one vendored in the submodule; if the submodule contains a different version, the comparison will be qualitative rather than exact.
