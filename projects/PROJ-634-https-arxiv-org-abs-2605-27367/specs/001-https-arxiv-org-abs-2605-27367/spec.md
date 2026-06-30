# Feature Specification: Reproduce & Validate SpatialBench

**Feature Branch**: `634-reproduce-spatialbench`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: SpatialBench: Is Your Spatial Foundation Model an All-Round Player? (arxiv preprint). Code vendored at external/SpatialBench."

## User Scenarios & Testing

### User Story 1 - Validate End-to-End Execution on CPU (Priority: P1)

**Description**: As a researcher, I need to execute the vendored `SpatialBench` benchmark code on a standard CPU-only CI runner (GitHub Actions free tier) to confirm the implementation runs without crashing, produces valid output artifacts, and respects hardware constraints (no GPU, <7GB RAM).

**Why this priority**: This is the foundational step. Without a successful execution that produces artifacts, no scientific validation can occur. The paper's claims cannot be verified if the code fails to run or requires unavailable hardware (GPU/CUDA).

**Independent Test**: Run the benchmark entry point with a minimal configuration on a CPU-only runner. Verify that the process exits with code 0 and generates at least one non-empty JSON/CSV report file and one visualization image.

**Acceptance Scenarios**:
1. **Given** the `SpatialBench` submodule is checked out and dependencies are installed, **When** the user executes the benchmark runner with `--device cpu` and a subset of 1 dataset, **Then** the job completes within 60 minutes, uses <7GB RAM, and produces a `results_minimal.json` file containing valid metric keys.
2. **Given** the environment has no CUDA/GPU drivers, **When** the benchmark attempts to load a model, **Then** the system gracefully falls back to CPU execution or raises a clear, non-fatal error if the model is strictly CUDA-bound (triggering a skip), and the run continues or exits cleanly.

---

### User Story 2 - Reproduce Key Quantitative Findings (Priority: P2)

**Description**: As a reviewer, I need to run the benchmark on a representative subset of the scenes (e.g., 5 scenes across 2 domains) to reproduce the core quantitative findings reported in the paper (e.g., "full-context attention maximizes accuracy") to verify the implementation's numerical correctness.

**Why this priority**: Execution alone is insufficient; the results must align with the paper's claims. This validates that the logic, metrics, and data processing are implemented correctly and not just "running."

**Independent Test**: Execute the benchmark on a curated subset of 5 scenes from 2 distinct domains (e.g., DTU and ScanNet). Compare the generated metrics against the "Expected Results" table in the paper (or the paper's reported baseline values for those specific scenes if available in the repo) to ensure the values are within a reasonable floating-point tolerance (e.g., <1% relative error).

**Acceptance Scenarios**:
1. **Given** the benchmark runs on a subset of 5 scenes, **When** the `metrics.py` module calculates depth estimation error (Abs Rel), **Then** the output values match the paper's reported baseline for the same model on the same scenes within a 5% relative tolerance.
2. **Given** the benchmark runs with different input densities (as per the paper's 4 settings), **When** the results are aggregated, **Then** the trend (e.g., accuracy drops as density drops) matches the qualitative claims in the paper's abstract.

---

### User Story 3 - Generate Validation Report & Visualization (Priority: P3)

**Description**: As a project stakeholder, I need the system to automatically generate a human-readable validation report and visualization artifacts (e.g., `overview.png`, `memory_curve.png`) that summarize the reproduction results, confirming the benchmark's ability to produce the visual evidence claimed in the paper.

**Why this priority**: The paper emphasizes "deterministic sampling" and "visual evidence." Generating these artifacts proves the pipeline is complete and ready for the final `research_complete` state.

**Independent Test**: Run the visualization script (`visualize_benchmark_web.py`) on the generated results. Verify that the output includes the expected figure types (e.g., memory curves, domain performance heatmaps) and that the report text accurately reflects the run parameters.

**Acceptance Scenarios**:
1. **Given** a valid `results.json` file exists, **When** the `visualize_benchmark_web.py` script is executed, **Then** it generates at least 2 PNG images and 1 HTML report within 5 minutes.
2. **Given** the generated report, **When** a user inspects the "Memory Curve" chart, **Then** the chart displays the expected axes (Memory vs. Sequence Length) and data points corresponding to the benchmarked models.

---

### Edge Cases

- **What happens when a model requires GPU?** The system MUST detect the missing GPU and either skip the model with a logged warning or fail gracefully with a specific error code (e.g., `EXIT_CODE_GPU_REQUIRED`), ensuring the rest of the benchmark suite continues.
- **How does the system handle missing data?** If the dataset submodule (e.g., `DTU` or `ScanNet`) is not initialized or data is missing, the system MUST fail fast with a clear error message indicating which dataset is missing, rather than running silently with zero data.
- **What happens if memory exceeds 7GB?** The system MUST monitor RAM usage; if it approaches 6GB, it MUST terminate the current model evaluation with a `MEMORY_LIMIT_EXCEEDED` status to prevent the CI job from being killed by the OOM killer.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `SpatialBench` benchmark runner using only CPU resources, ensuring no CUDA/GPU dependencies are invoked during inference. (See US-1)
- **FR-002**: System MUST generate a structured results file (JSON/CSV) containing per-scene, per-model metrics (e.g., Abs Rel, δ1, δ2) after execution. (See US-1)
- **FR-003**: System MUST support a "subset mode" that allows running the benchmark on a configurable number of scenes (e.g., `--num-scenes 5`) to fit within 6-hour CI limits. (See US-2)
- **FR-004**: System MUST produce visualization artifacts (PNG/HTML) summarizing memory usage curves and domain performance comparisons. (See US-3)
- **FR-005**: System MUST log a clear error or skip status if a specific model adapter requires hardware not available in the current environment (e.g., 8-bit quantization requiring CUDA). (See US-1)
- **FR-006**: System MUST validate that the output metrics match the paper's reported baseline values within a 5% relative tolerance for at least one reference model. (See US-2)

### Success Criteria

- **SC-001**: The benchmark execution completes successfully (exit code 0) on a CPU-only runner without OOM errors for a subset of 5 scenes. (See US-1)
- **SC-002**: The generated results file contains valid numerical metrics for at least 3 distinct models across 2 domains. (See US-2)
- **SC-003**: The validation report includes at least 2 distinct visualization types (e.g., memory curve, performance table) matching the paper's figure categories. (See US-3)
- **SC-004**: The relative error between reproduced metrics and paper-reported baselines for the reference model is ≤ 5%. (See US-2)
- **SC-005**: The total wall-clock time for the subset run (5 scenes, 3 models) is ≤ 60 minutes. (See US-1)

## Assumptions

- **Assumption about compute constraints**: The benchmark code can be configured to run on CPU-only hardware by disabling CUDA-specific flags (e.g., `torch.cuda.is_available()` checks) and using float32 precision instead of 8-bit/4-bit quantization, as the paper's codebase likely defaults to GPU but is adaptable.
- **Assumption about data availability**: The necessary dataset files (e.g., DTU, ScanNet) are either included in the submodule or can be downloaded via the provided scripts within the 14GB disk limit of the free-tier runner.
- **Assumption about model scope**: For the purpose of this reproduction, only a subset of the models mentioned in the paper will be tested (e.g., 3 representative models) to ensure the job completes within the 6-hour limit.
- **Assumption about paper claims**: The "baseline values" in the paper are reproducible within a 5% tolerance on CPU, acknowledging that floating-point differences may occur between GPU and CPU execution.
- **Assumption about memory**: The "full-context attention" models mentioned in the paper will be run on a downsampled sequence length or a single scene to prevent memory overflow, as the full 546-scene run is out of scope for the initial validation.
