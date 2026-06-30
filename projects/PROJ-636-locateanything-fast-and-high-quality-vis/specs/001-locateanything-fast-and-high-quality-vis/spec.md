# Feature Specification: Reproduce & Validate LocateAnything (Eagle)

**Feature Branch**: `636-reproduce-locateanything`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: LocateAnything: Fast and High-Quality Vision-Language Grounding with Parallel Box Decoding. The code is vendored in external/Eagle. Task is to run, validate, and reproduce the shipped implementation end-to-end."

## User Scenarios & Testing

### User Story 1 - Validate Model Inference on Sample Data (Priority: P1)

The researcher MUST be able to load the vendored `Eagle` model and execute a single inference step on a provided sample image and text prompt to confirm the model loads, the `Parallel Box Decoding` (PBD) mechanism activates, and the output is a valid bounding box coordinate set.

**Why this priority**: This is the "smoke test" for the entire project. If the model cannot load or generate a box on a CPU-only runner, the reproduction effort fails immediately. It validates the core "Fast and High-Quality" claim by confirming the inference path exists.

**Independent Test**: Execute the `gradio_demo.py` or `predict_demo.py` entry point with a hardcoded sample image and prompt. Verify the output file contains valid JSON with bounding box coordinates (normalized 0-1 or pixel values) and no CUDA/GPU errors.

**Acceptance Scenarios**:
1. **Given** the `external/Eagle` submodule is checked out and dependencies are installed, **When** the researcher runs the inference script with a 512x512 sample image and the prompt "Locate the dog", **Then** the script completes within 60 seconds on a CPU-only runner and outputs a file containing valid bounding box coordinates.
2. **Given** the inference script is configured to use `device="cpu"`, **When** the researcher runs the script, **Then** the system MUST NOT raise `ImportError: bitsandbytes` or `RuntimeError: CUDA not available` and MUST successfully execute the forward pass.

---

### User Story 2 - Execute Benchmark Evaluation on a Subset (Priority: P2)

The researcher MUST be able to run the evaluation pipeline (`lmms_eval`) against a small, representative subset of a standard grounding benchmark (e.g., RefCOCO or Flickr30K) to verify the scoring logic and metric calculation (e.g., IoU) function correctly without requiring the full M dataset.

**Why this priority**: The paper claims "extensive evaluations" on diverse benchmarks. Validating the evaluation harness on a subset proves the reproducibility of the *metrics* and the *scoring pipeline*, which is essential for comparing against the paper's reported numbers later.

**Independent Test**: Run the `evaluate_lmms_eval.py` script targeting a specific small benchmark (e.g., `flickr30k` or a 100-sample subset of `refcoco`). Verify the script generates a JSON result file with calculated IoU scores and no runtime errors.

**Acceptance Scenarios**:
1. **Given** the model is loaded in inference mode, **When** the researcher runs the evaluator on a subset of images from the `flickr30k` validation set, **Then** the system MUST generate a results JSON file within 15 minutes containing per-sample IoU scores and an aggregate mean IoU.
2. **Given** the evaluator is running on a CPU-only runner with ≤7GB RAM, **When** the batch size is set to 1, **Then** the process MUST complete without an `OOM` (Out of Memory) error.

---

### User Story 3 - Generate Reproduction Report Artifacts (Priority: P3)

The researcher MUST be able to compile the outputs from the inference and evaluation steps into a structured report (Markdown/JSON) that explicitly compares the observed runtime, memory usage, and metric scores against the claims in the `LocateAnything` paper abstract.

**Why this priority**: The ultimate goal of a "Reproduction project" is to produce a verifiable record. This story ensures the raw artifacts (logs, metrics) are transformed into a human-readable conclusion that addresses the paper's claims about speed and accuracy.

**Independent Test**: A script or manual process aggregates the inference logs and evaluation JSONs into a `reproduction_report.md` that lists: (1) Inference time per image, (2) Peak RAM usage, (3) Mean IoU on the subset, and (4) A binary pass/fail against the paper's qualitative claims.

**Acceptance Scenarios**:
1. **Given** the inference and evaluation steps have completed successfully, **When** the researcher runs the report generation script, **Then** a `reproduction_report.md` file is created containing a table of observed metrics and a summary statement on whether the "Parallel Box Decoding" speedup was observable on CPU.
2. **Given** the observed metrics are collected, **When** the report is generated, **Then** the report MUST explicitly state if the observed throughput (images/sec) is within 20% of the paper's claimed baseline for CPU inference (or note if the paper only reported GPU results).

---

### Edge Cases

- **What happens when** the model weights are missing or corrupted in the submodule? The system MUST detect missing `.safetensors` or `.bin` files and fail fast with a clear error message, rather than hanging or generating random noise.
- **How does system handle** a prompt that results in zero detected boxes? The system MUST return an empty list `[]` or a specific null marker in the JSON output, not crash or return a default "full image" box.
- **What happens when** the RAM usage exceeds a high threshold during the loading of the vision encoder.? The system MUST gracefully fail with an OOM error message, and the spec assumes the user will sample data or use a smaller model variant (e.g., `Eagle-7B` vs `Eagle-34B`) to fit the constraints.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST load the `Eagle` model architecture using only CPU resources, explicitly avoiding any CUDA/GPU device calls or `bitsandbytes` quantization loaders. (See US-1)
- **FR-002**: The system MUST execute the `Parallel Box Decoding` (PBD) inference step to generate bounding box coordinates in a single forward pass, outputting results in a standardized JSON format with `x_min`, `y_min`, `x_max`, `y_max` fields. (See US-1)
- **FR-003**: The evaluation pipeline MUST calculate Intersection-over-Union (IoU) metrics for a provided subset of the RefCOCO or Flickr30K dataset and output a mean IoU score. (See US-2)
- **FR-004**: The system MUST log peak memory usage (RAM) and total inference time for every test case to facilitate the "speed" claim validation. (See US-3)
- **FR-005**: The system MUST handle missing or malformed input images by skipping the sample and logging a warning, rather than crashing the entire evaluation batch. (See US-2)

### Key Entities

- **InferenceResult**: Represents the output of a single inference run, containing `image_id`, `prompt`, `predicted_boxes` (list of coordinates), `inference_time_ms`, and `status`.
- **EvaluationMetric**: Represents the aggregate performance on a benchmark subset, containing `benchmark_name`, `subset_size`, `mean_iou`, and `throughput_images_per_sec`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The inference execution time per image is measured against the paper's claimed throughput (images/sec) for the "Parallel Box Decoding" mechanism to verify the speedup claim. (See US-1)
- **SC-002**: The mean IoU score on the benchmark subset is measured against the paper's reported baseline scores for the same dataset to verify the "High-Quality" claim. (See US-2)
- **SC-003**: The peak RAM usage during model loading and inference is measured against the free-tier CI runner limit to verify compute feasibility. (See US-1)
- **SC-004**: The reproducibility status (Pass/Fail) is measured against the paper's abstract claims regarding "substantial parallelism" and "improved localization accuracy." (See US-3)

## Assumptions

- The `external/Eagle` submodule contains all necessary pre-trained weights (`.safetensors` or `.bin` files) and does not require a separate download step during the CI run.
- The "Parallel Box Decoding" mechanism is implemented in the vendored code such that it can function (albeit slower) on a CPU-only environment without requiring specific GPU kernels.
- The evaluation subset (e.g., a representative sample of images) is sufficient to validate the correctness of the scoring pipeline without requiring the full M training dataset or the complete benchmark test sets.
- The `lmms_eval` framework included in the submodule is compatible with the Python version and library versions available in the standard GitHub Actions free-tier environment.
- The paper's "speed" claims are primarily relative to serial decoding; the reproduction will measure absolute time on CPU and compare it to the paper's relative improvement claims, acknowledging that absolute CPU times may be significantly higher than the paper's GPU-reported times.
