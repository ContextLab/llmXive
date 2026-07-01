# Feature Specification: EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts

**Feature Branch**: `001-efficientrollout-validation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts (Paper: arXiv:2606.18967)"

## User Scenarios & Testing

### User Story 1 - Environment Initialization and CPU-Feasible Quantization (Priority: P1)

As a researcher, I want to initialize the `EfficientRollout` codebase and generate a CPU-compatible quantized drafter from the target model, so that I can proceed with validation without requiring GPU hardware or CUDA-specific quantization libraries.

**Why this priority**: This is the foundational step. The paper relies on "self-speculative decoding" where a quantized drafter is induced from the target model. If the environment cannot build the quantized drafter on CPU (e.g., due to missing bitsandbytes/CUDA dependencies), the entire reproduction fails immediately. This step validates the "compute feasibility" constraint of the project.

**Independent Test**: Can be fully tested by running the `quantize_utils.py` script or the equivalent setup command on a CPU-only runner and verifying the output of a quantized model file exists without CUDA errors.

**Acceptance Scenarios**:

1. **Given** a fresh GitHub Actions free-tier runner (2 CPU, 7GB RAM), **When** the user executes the environment setup script for CPU quantization, **Then** the script must complete without importing `bitsandbytes` or `load_in_8bit` flags that require CUDA, and a quantized model artifact must be written to disk.
2. **Given** the target model (e.g., Llama-3.1-8B-Instruct) is loaded in default precision, **When** the quantization routine is applied, **Then** the resulting model must be loadable by the `sd_toggle` module using only CPU-based inference kernels.

---

### User Story 2 - Execution of System-Aware SD Toggle on Sample Data (Priority: P2)

As a researcher, I want to run the `sd_toggle` prediction workflow on a small, fixed subset of the `SimpleRL-Zoo` dataset, so that I can verify the system-aware toggle logic executes end-to-end and produces latency artifacts without exceeding the 6-hour CI time limit.

**Why this priority**: This validates the core algorithmic contribution (the toggle policy and draft-length adaptation) on a manageable scale. Running the full paper's dataset would likely exceed CI limits; a representative subset proves the logic works while respecting compute constraints.

**Independent Test**: Can be fully tested by running the `predict.py` or `cli.py` entry point with a `--max-num-seqs` limit (e.g., 10 sequences) and verifying that output logs show successful "speculation" and "verification" phases.

**Acceptance Scenarios**:

1. **Given** a quantized drafter and a target model loaded in CPU mode, **When** the user runs the `sd_toggle` CLI with a sample of 10 prompts from `SimpleRL-Zoo`, **Then** the system must complete the rollout generation within 15 minutes and output a JSON log containing per-token acceptance rates and latency measurements.
2. **Given** the active batch size shrinks during generation, **When** the system evaluates the "system-aware toggle," **Then** the logs must explicitly record the decision to enable or disable speculation based on the current compute/memory-bound regime, matching the logic in `sd_toggle/fit.py`.

---

### User Story 3 - Reproduction of Latency Reduction Metrics (Priority: P3)

As a researcher, I want to compare the latency of the `EfficientRollout` (speculative) run against a standard autoregressive baseline run on the same subset, so that I can confirm the directionality of the speedup (even if the exact [deferred] figure is not reproducible on CPU).

**Why this priority**: This provides the final validation of the paper's claim. While exact numbers may differ on CPU vs. A100, the *method* of measuring speedup and the *direction* of the result (speedup > 0) must be reproducible to validate the research.

**Independent Test**: Can be fully tested by running two distinct jobs (Baseline AR vs. EfficientRollout SD) on the same 10-prompt subset and calculating the ratio of total end-to-end latency.

**Acceptance Scenarios**:

1. **Given** two completed runs (Baseline AR and EfficientRollout SD) on the same dataset subset, **When** the `plot.py` or analysis script aggregates the latency data, **Then** the output must include a comparative bar chart or table showing `EfficientRollout` latency < `Baseline` latency.
2. **Given** the paper claims up to 19.6% reduction, **When** the comparison is performed on the CPU subset, **Then** the spec must record the observed reduction percentage and flag if the reduction is statistically insignificant or negative, rather than forcing a match to the paper's number.

---

### Edge Cases

- **What happens when the quantized drafter fails to load on CPU?** The system MUST fail fast with a clear error message indicating that the quantization method requires GPU/CUDA, triggering a `[NEEDS CLARIFICATION]` to switch to a CPU-native quantization format (e.g., GGUF via `llama.cpp` backend if available in the repo, or fallback to default precision with a note on performance).
- **How does the system handle memory pressure during batched generation?** If the batch size exceeds the available RAM limit of the runner, the system MUST automatically reduce the batch size to 1 or 2 and log a warning, ensuring the job completes rather than OOM-killing.
- **What if the `sd_toggle` logic predicts speculation is never beneficial?** The system MUST still execute the baseline path correctly and report a "[deferred] speedup" or "negative speedup" rather than crashing or skipping the verification step.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the target model (e.g., Llama-3.1-8B-Instruct) and generate a quantized drafter using only CPU-compatible operations, avoiding any CUDA-specific quantization libraries like `bitsandbytes` (See US-1).
- **FR-002**: System MUST execute the `sd_toggle` prediction workflow on a user-defined subset of the `SimpleRL-Zoo` dataset, ensuring the batch size is dynamically capped to fit within 7 GB of RAM (See US-2).
- **FR-003**: System MUST log per-token acceptance rates and total end-to-end latency for both the speculative and autoregressive baselines in a structured JSON format (See US-3).
- **FR-004**: System MUST implement the "system-aware toggle" logic to disable speculation when the active batch size indicates a memory-bound regime, as described in the paper's abstract (See US-2).
- **FR-005**: System MUST compare the total latency of the `EfficientRollout` run against a standard autoregressive run and output a calculated speedup ratio (See US-3).

### Key Entities

- **Quantized Drafter**: A reduced-precision version of the target model used for token drafting, stored as a file artifact on the runner.
- **Rollout Trace**: A sequence of tokens generated during the RL rollout, annotated with acceptance/rejection flags and timing data.
- **Toggle Decision**: A binary state (Enable/Disable) determined by the `sd_toggle` module based on current system metrics (batch size, memory pressure).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: CPU-only quantization success rate is measured against the requirement that no CUDA errors occur during model loading (See FR-001, US-1).
- **SC-002**: Total execution time for the 10-prompt subset is measured against the 6-hour CI limit to ensure the workflow is feasible on free-tier hardware (See FR-002, US-2).
- **SC-003**: Latency reduction ratio (EfficientRollout / Baseline) is measured against the paper's claim of "up to 19.6% reduction" to validate the directionality of the result (See FR-005, US-3).
- **SC-004**: Memory usage peak is measured against the 7 GB RAM limit to verify the batch-size capping logic prevents OOM failures (See FR-002, US-2).

## Assumptions

- **Assumption about compute environment**: The GitHub Actions free-tier runner provides a standard multi-core CPU environment with sufficient RAM and disk resources for typical workloads; no GPU accelerators are available or assumed.
- **Assumption about data source**: The `SimpleRL-Zoo` dataset is available via the vendored submodule or a public URL accessible from the runner, and a subset of prompts is sufficient to validate the logic without reproducing the full paper's statistical power.
- **Assumption about quantization**: The `EfficientRollout` codebase includes a CPU-compatible quantization path (e.g., via `torch.quantization` or a fallback to default precision) that does not strictly require `bitsandbytes` or CUDA, or the spec assumes a fallback to default precision with a performance penalty note.
- **Assumption about paper claims**: The paper's claim of "[deferred] latency reduction" is specific to A100 GPUs and high-throughput regimes; the reproduction on CPU may yield a different magnitude or even negative speedup due to overhead, which is acceptable as long as the *mechanism* is validated.
- **Assumption about dataset-variable fit**: The `SimpleRL-Zoo` dataset contains the necessary prompt/response pairs for the `sd_toggle` logic to function; no additional metadata (e.g., user traits) is required for this reproduction.
