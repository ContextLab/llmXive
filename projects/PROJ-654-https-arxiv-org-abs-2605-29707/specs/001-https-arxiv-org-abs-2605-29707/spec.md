# Feature Specification: Reproduce & Validate Domino Speculative Decoding Framework

**Feature Branch**: `001-reproduce-domino-speculative-decoding`  
**Created**: 2025-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding (arXiv:2605.29707)"

## User Scenarios & Testing

### User Story 1 - Execute End-to-End Validation Pipeline on CPU (Priority: P1)

**Journey**: As a researcher, I want to execute the vendored `Domino` benchmark scripts in a CPU-only environment to confirm the implementation runs without modification and produces initial output artifacts, establishing the baseline for reproducibility.

**Why this priority**: This is the critical path. Without a successful run, no validation or comparison to the paper's claims is possible. It validates the "shipped code" claim immediately.

**Independent Test**: The pipeline runs `run_hf_benchmark.sh` (or `benchmark.py`) and exits with status 0, producing at least one log file and one metrics JSON/CSV artifact in the `external/Domino/` directory.

**Acceptance Scenarios**:

1. **Given** the `external/Domino` submodule is cloned and dependencies are installed via `requirements-hf.txt`, **When** the user executes `bash run_hf_benchmark.sh` on a CPU-only runner, **Then** the script completes successfully (exit code 0) and generates a `results_*.json` or `benchmark_log.txt` file containing latency and throughput metrics.
2. **Given** the environment lacks GPU support, **When** the benchmark script initializes, **Then** it detects CPU-only mode and proceeds using the default CPU path without raising CUDA-specific errors (e.g., `CUDA_VISIBLE_DEVICES` errors or `bitsandbytes` import failures).
3. **Given** the script completes, **When** the user inspects the generated artifacts, **Then** the artifacts contain non-zero token counts and non-NaN latency values, proving actual inference occurred.

---

### User Story 2 - Verify Computational Feasibility & Resource Constraints (Priority: P2)

**Journey**: As a CI/CD engineer, I want to confirm that the reproduction process completes within the GitHub Actions free-tier limits (2 CPU, 7GB RAM, 6 hours) without OOM errors or excessive runtime, ensuring the project is maintainable.

**Why this priority**: The paper claims speedups using LLMs, which often require GPUs. If the reproduction fails due to resource exhaustion on CPU, the project cannot reach `research_complete`. This ensures the "Compute Feasibility" constraint is met.

**Independent Test**: The benchmark run finishes in ≤ 45 minutes on a standard 2-core runner and stays under 6.5GB RAM usage peak.

**Acceptance Scenarios**:

1. **Given** the benchmark is running on a 2-core, 7GB RAM runner, **When** the process consumes memory, **Then** the peak RSS (Resident Set Size) remains below 6.5 GB, preventing an OOM kill.
2. **Given** the benchmark processes a sample dataset (e.g., 50 prompts), **When** the total wall-clock time is measured, **Then** the duration is ≤ 45 minutes, leaving a buffer for the 6-hour CI limit.
3. **Given** the environment has no GPU, **When** the model loads, **Then** the system uses standard 32-bit float precision (FP32) or FP16 on CPU (if supported by the backend) rather than attempting 8-bit/4-bit quantization which requires CUDA libraries.

---

### User Story 3 - Reproduce Paper Claims & Generate Comparison Report (Priority: P3)

**Journey**: As a peer reviewer, I want to compare the reproduced metrics (speedup, throughput) against the paper's reported claims (up to 5.49x speedup) to validate the scientific accuracy of the vendored code.

**Why this priority**: This fulfills the "Research Complete" definition. It moves the project from "it runs" to "it works as claimed."

**Independent Test**: A comparison report is generated that lists the reproduced speedup factor and explicitly states whether it matches the paper's range (considering hardware differences).

**Acceptance Scenarios**:

1. **Given** the benchmark has produced metrics for both "Baseline" (standard autoregressive) and "Domino" modes, **When** the comparison logic runs, **Then** it calculates the speedup ratio as `Baseline_Latency / Domino_Latency`.
2. **Given** the paper claims up to 5.49x speedup on Qwen3, **When** the report is generated, **Then** it explicitly notes if the reproduced speedup is within 20% of the claim or if it deviates due to hardware differences (CPU vs. GPU), citing the specific hardware used.
3. **Given** the benchmark fails to produce a speedup > 1.0x, **When** the report is generated, **Then** it flags the result as "Failed to Reproduce Speedup" and logs the specific configuration parameters (draft size, model size) used.

### Edge Cases

- **What happens when the model size exceeds RAM?** The system MUST fail gracefully with an explicit "Out of Memory" error message suggesting model quantization (if CPU-supported) or dataset subsampling, rather than hanging or crashing silently.
- **How does the system handle network timeouts during dependency installation?** The script MUST retry failed `pip install` commands up to 3 times before failing the entire job.
- **What if the paper's specific model (Qwen3) is unavailable?** The system MUST default to a smaller, available model (e.g., Qwen2-0.5B or Llama-3-8B) and explicitly log this substitution in the output artifacts.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `run_hf_benchmark.sh` script using the HuggingFace backend to load the target model and run the Domino inference loop. (See US-1)
- **FR-002**: The system MUST run the inference entirely on CPU, avoiding any CUDA-specific imports (e.g., `bitsandbytes`, `load_in_8bit`) that would cause runtime errors on free-tier runners. (See US-2)
- **FR-003**: The system MUST generate a structured metrics file (JSON or CSV) containing at least: `total_latency`, `tokens_per_second`, `speedup_ratio`, and `model_name`. (See US-3)
- **FR-004**: The system MUST detect the available hardware (CPU/GPU) at runtime and configure the `device_map` parameter accordingly to prevent initialization crashes. (See US-2)
- **FR-005**: The system MUST implement a timeout mechanism for the benchmark step, aborting the process if it exceeds a predefined duration threshold to preserve CI resources. (See US-2)
- **FR-006**: The system MUST log the exact version of the `transformers` and `torch` libraries used during execution to ensure reproducibility of the environment. (See US-3)
- **FR-007**: The system MUST compare the calculated `speedup_ratio` against the paper's claimed value and output a "Pass/Fail" status based on a 20% tolerance threshold. (See US-3)

### Key Entities

- **Benchmark Run**: A single execution instance of the benchmark script, characterized by model parameters, hardware context, and output metrics.
- **Metrics Artifact**: The structured output file (JSON/CSV) containing performance data from a Benchmark Run.
- **Validation Report**: A human-readable summary comparing the Metrics Artifact against the paper's claims.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The benchmark script MUST complete successfully (exit code 0) within 45 minutes on a 2-core CPU runner. (See US-2)
- **SC-002**: The peak memory usage of the process MUST remain within acceptable limits during the entire benchmark run. (See US-2)
- **SC-003**: The generated metrics artifact MUST contain a valid `speedup_ratio` value > 1.0, indicating Domino is faster than the baseline in the tested configuration. (See US-3)
- **SC-004**: The validation report MUST explicitly state the hardware configuration used (e.g., "2 vCPU, 7GB RAM") and the specific model version tested. (See US-3)
- **SC-005**: The system MUST NOT crash with a `CUDA_ERROR` or `ImportError` related to GPU-specific libraries. (See US-1, US-2)

## Assumptions

- The vendored `external/Domino` repository contains a `requirements-hf.txt` that is compatible with standard CPU-only PyTorch installations (i.e., does not strictly require `bitsandbytes` or CUDA-specific wheel versions).
- The target model (Qwen3 or a compatible proxy) is available via HuggingFace Hub and can be loaded into 7GB of RAM (likely requiring a smaller model variant like Qwen2-1.8B or similar if Qwen3 is too large).
- The paper's claim of "significant speedup" is based on GPU acceleration; the reproduced speedup on CPU may be lower (e.g., 2x - 3x) but must still demonstrate a positive speedup over the baseline to validate the algorithm's efficacy.
- The GitHub Actions runner provides stable network access to `huggingface.co` for model and dependency downloads.
- The "base-anchored training curriculum" mentioned in the paper is not required for this reproduction task, as the task is to validate the *inference* framework, not retrain the model weights.
- The benchmark scripts in `external/Domino/code/` are designed to handle missing GPU devices by falling back to CPU execution without requiring code modification.
