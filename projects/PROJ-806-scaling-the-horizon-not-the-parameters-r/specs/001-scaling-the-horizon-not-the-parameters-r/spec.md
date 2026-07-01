# Feature Specification: Reproduce & Validate: Scaling the Horizon, Not the Parameters

**Feature Branch**: `806-reproduce-validate-scaling-horizon`  
**Created**: 2026-06-14  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Scaling the Horizon, Not the Parameters: Reaching Trillion-Parameter Performance with a Large-Scale Agent"

## User Scenarios & Testing

### User Story 1 - Execute End-to-End Reproduction Pipeline (Priority: P1)

The researcher MUST be able to trigger the vendored `Agents-A1` evaluation pipeline via a single command, causing the system to load a large-scale MoE model, execute a subset of long-horizon benchmarks (e.g., SEAL-0, IFBench, or SciCode), and generate raw result artifacts (JSON logs, token traces) without manual intervention.

**Why this priority**: This is the foundational step. Without a successful, automated execution of the shipped code, no validation or comparison is possible. It confirms the codebase is functional and the environment is correctly configured.

**Independent Test**: Can be fully tested by running the provided `run.sh` or entry script in a clean environment and verifying the existence of output files (e.g., `results/seal-0.json`) within the 6-hour CI limit.

**Acceptance Scenarios**:

1. **Given** the `Agents-A1` submodule is cloned and dependencies are installed, **When** the user executes the primary evaluation entry point (`evaluation/Search/run.sh`), **Then** the system completes the inference loop for at least one benchmark subset and writes a valid JSON results file to `evaluation/Search/results/`.
2. **Given** the environment has no GPU, **When** the pipeline starts, **Then** the system successfully loads the model in CPU-compatible precision (default float32 or quantized via CPU-only methods) and completes the first 10 inference steps without crashing due to CUDA errors.

---

### User Story 2 - Validate Performance Against Paper Claims (Priority: P2)

The researcher MUST be able to compare the generated raw results against the specific numerical claims in the abstract (e.g., SEAL-0 score ≥ 56.4, IFBench score ≥ 80.6) and produce a validation report indicating whether the reproduced scores meet, exceed, or fall short of the paper's reported metrics.

**Why this priority**: The core scientific value of this project is verification. This story ensures the reproduction is not just "running code" but actually "testing the hypothesis" that the 35B agent matches 1T performance.

**Independent Test**: Can be tested by parsing the output JSON from US-01, calculating the benchmark score using the provided `judger` logic, and comparing it to the threshold values defined in the paper's abstract.

**Acceptance Scenarios**:

1. **Given** a completed inference run for the SEAL-0 benchmark, **When** the validation script compares the calculated score against the paper's claim of 56.4, **Then** the system outputs a clear pass/fail status and the exact numerical difference.
2. **Given** the inference results for multiple domains (Search, Tools, Science), **When** the aggregation script runs, **Then** it produces a summary table showing the reproduced score for each domain alongside the paper's reported score.

---

### User Story 3 - Resource & Feasibility Audit (Priority: P3)

The researcher MUST be able to confirm that the entire reproduction process (inference + evaluation) adheres to the strict free-tier CI constraints (≤2 CPU cores, ≤7 GB RAM, ≤6 hours) and that no GPU-specific dependencies are required.

**Why this priority**: The project's success depends on reproducibility in a constrained environment. If the code requires hardware not available in the free tier, the project cannot reach the `research_complete` stage.

**Independent Test**: Can be tested by monitoring the CI runner's resource usage (via GitHub Actions logs) and verifying no `CUDA`, `torch.cuda`, or GPU-specific library imports trigger errors.

**Acceptance Scenarios**:

1. **Given** the CI runner is a standard GitHub Actions free-tier instance, **When** the evaluation job runs, **Then** the job completes within 360 minutes (6 hours) and the memory usage never exceeds 7 GB.
2. **Given** the codebase imports `torch` or `transformers`, **When** the script executes on a CPU-only runner, **Then** the system does not raise a `RuntimeError` regarding missing CUDA devices or unsupported quantization backends.

---

### Edge Cases

- **What happens when the model weights are too large for 7 GB RAM?** The system MUST implement a chunked loading or aggressive sampling strategy to fit the model into memory; if this fails, the job MUST fail gracefully with a specific error code `ERR_OOM_CPU` rather than hanging.
- **How does the system handle a timeout during long-horizon generation?** If a single trajectory exceeds the k token limit or the 6-hour wall-clock limit, the system MUST terminate that specific trajectory, log a `TIMEOUT_EXCEEDED` flag, and proceed to the next sample to ensure partial results are preserved.
- **What if the vendor code requires a specific Python version?** The system MUST detect version mismatches during the `pip install` phase and fail immediately with a clear message, rather than attempting to run with incompatible dependencies.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `Agents-A1` inference pipeline on a subset of benchmarks (SEAL-0, IFBench, or SciCode) using only CPU resources, completing the run within 6 hours. (See US-01)
- **FR-002**: System MUST parse the raw output logs and calculate benchmark scores using the provided `judger` logic (e.g., `evaluation/Search/judger/evaluate.py`) to ensure consistency with the paper's methodology. (See US-02)
- **FR-003**: System MUST compare the calculated scores against the paper's claimed values (SEAL-0 ≥ 56.4, IFBench ≥ 80.6) and generate a boolean pass/fail indicator for each metric. (See US-02)
- **FR-004**: The system must enforce a hard memory limit. and a CPU core limit of a constrained number during execution, terminating the job if these thresholds are exceeded to prevent CI failure. (See US-03)
- **FR-005**: System MUST verify that no GPU-specific libraries (e.g., `bitsandbytes` in 8-bit mode requiring CUDA, `device_map="cuda"`) are invoked, ensuring the code runs in a pure CPU environment. (See US-03)
- **FR-006**: System MUST handle long-horizon trajectories (up to 45k tokens) by implementing a token-count cutoff that stops generation if the limit is reached, logging the truncation reason. (See US-01)

### Key Entities

- **Benchmark Result**: The structured output containing the task ID, generated trajectory, score, and pass/fail status for a single evaluation sample.
- **Validation Report**: The aggregate document summarizing the performance of the 35B agent against the paper's claims across all executed benchmarks.
- **Resource Log**: The telemetry data capturing memory usage, CPU utilization, and wall-clock time for the execution job.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Reproduction success rate is measured against the paper's reported scores (e.g., SEAL) by calculating the absolute difference; a pass is defined as `|reproduced_score - paper_score| ≤ 2.0`. (See US-02)
- **SC-002**: Resource feasibility is measured against the free-tier constraints (≤7 GB RAM, ≤6 hours); success is defined as [deferred] of jobs completing without OOM or timeout errors. (See US-03)
- **SC-003**: Code compatibility is measured against the CPU-only constraint; success is defined as zero `CUDA` or `GPU` related exceptions during the entire execution pipeline. (See US-03)
- **SC-004**: Trajectory validity is measured against the k token horizon limit; success is defined as [deferred] of generated trajectories either completing naturally or being truncated with a logged reason, with no unhandled exceptions. (See US-01)

## Assumptions

- The vendored `Agents-A1` codebase contains a valid, pre-trained B MoE model checkpoint that can be loaded into memory with CPU-only quantization or standard precision without requiring proprietary GPU drivers.
- The benchmark datasets (SEAL-0, IFBench, SciCode) are either included in the submodule or accessible via a public URL that does not require authentication tokens or large downloads (>14 GB) that would exceed the disk limit.
- The paper's reported scores are based on the exact same evaluation scripts and prompt templates provided in the `evaluation/` directory of the submodule.
- The "35B" model size refers to the active parameters or a MoE configuration that fits within 7 GB RAM when loaded with standard CPU optimization (e.g., `torch.float32` with offloading or `float16` if supported by the CPU backend).
- The `judger` logic in `evaluation/Search/judger/` is self-contained and does not depend on external APIs (e.g., an LLM-as-a-judge) that might introduce latency or cost beyond the free-tier limits.
