# Implementation Plan: Reproduce & Validate Domino Speculative Decoding Framework

**Branch**: `001-reproduce-domino-speculative-decoding` | **Date**: 2024-05-21 | **Spec**: `specs/001-reproduce-domino-speculative-decoding/spec.md`
**Input**: Feature specification from `specs/001-reproduce-domino-speculative-decoding/spec.md`

## Summary

This feature implements a reproducible validation pipeline for the "Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding" framework (arXiv:2605.29707). The primary requirement is to execute the vendored benchmark scripts on a CPU-only GitHub Actions runner (limited CPU and memory resources) to confirm the implementation runs without modification and produces initial output artifacts. The technical approach involves adapting the HuggingFace backend to strictly enforce CPU execution, handling model size constraints by selecting smaller compatible variants (e.g., Qwen2-0.5B/1.8B) if the target Qwen3 exceeds RAM limits, and generating a structured comparison report validating the *algorithmic feasibility* (positive speedup) rather than replicating the specific GPU magnitude claims.

## Technical Context

**Language/Version**: Python 3.10+ (strictly enforced for `transformers` compatibility)  
**Primary Dependencies**: `torch` (CPU-only wheel), `transformers`, `accelerate`, `datasets` (optional for prompt loading), `pandas`, `pytest`, `scipy` (for bootstrapping)  
**Storage**: Local filesystem (`external/Domino/`) for artifacts; HuggingFace Hub for model weights  
**Testing**: `pytest` for unit tests; CI integration for end-to-end benchmark validation  
**Target Platform**: Linux (GitHub Actions Free Tier Runner)  
**Project Type**: Computational Research / Benchmarking Tool  
**Performance Goals**: 
- Benchmark completion: ≤ 45 minutes per run
- Peak Memory (RSS): < 6.5 GB
- Speedup Validation: > 1.0x (positive speedup required)
**Constraints**: 
- NO GPU/CUDA usage (no `bitsandbytes`, no `load_in_8bit`)
- NO large model training; inference only
- Strict adherence to 45-minute timeout
- Model must fit in constrained RAM (likely requires Qwen-0.5B or 1.8B)
**Scale/Scope**: 
- Single model inference runs
- ~50 prompts for benchmarking (aggregated over n=10 runs)
- ~ GB model weights

> **Note on Dataset/Model**: The "Verified datasets" block provided does not contain a specific LLM model dataset. This necessitates the use of HuggingFace Hub model repositories (e.g., `Qwen/Qwen2-0.5B-Instruct`) which are standard programmatic loads, not the CSV/JSONL datasets listed in the verified block. The verified block lists RAM, MUST, and CPU-supported datasets which are irrelevant to LLM inference benchmarks; thus, no URL from that block will be cited for the model.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle 1: Reproducibility** - The plan explicitly mandates logging library versions (`transformers`, `torch`), hardware context, and the specific Draft/Target model pair to ensure the experiment can be repeated.
- **Principle 2: Feasibility** - The plan restricts all operations to CPU-only, avoids low-bit quantization libraries that require CUDA, and selects model sizes guaranteed to fit in available system RAM.
- **Principle 3: Scientific Rigor** - The plan includes a direct comparison against the paper's claimed speedup but explicitly flags hardware differences (CPU vs. GPU) and model substitutions, decoupling the success criteria from the specific magnitude to avoid a category error.
- **Principle 4: Resource Management** - A timeout mechanism is planned to prevent CI resource exhaustion.

## Project Structure

### Documentation (this feature)

```text
specs/001-reproduce-domino-speculative-decoding/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── benchmark_metrics.schema.yaml  # SSoT for metrics
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── Domino/              # Vendored submodule
    ├── code/            # Benchmark scripts
    ├── requirements-hf.txt
    └── run_hf_benchmark.sh

src/
├── benchmark/           # Wrapper logic for CPU enforcement
│   ├── runner.py        # Executes the benchmark with CPU constraints
│   ├── metrics.py       # Parses logs and calculates speedup
│   └── report.py        # Generates comparison report
├── config/
│   └── constraints.yaml # CPU/RAM limits and model selection rules
└── utils/
    └── logger.py        # Version and hardware logging

tests/
├── contract/            # Validates JSON schema of metrics
├── integration/         # Runs a mini-benchmark (1 prompt)
└── unit/
    └── test_metrics.py
```

**Structure Decision**: The structure separates the vendored `Domino` code from the project's orchestration logic (`src/benchmark`). This ensures that the original research code remains untouched while the project layer handles the specific constraints of the CPU-only CI environment (e.g., model substitution, timeout enforcement).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly bounded by the spec's CPU constraints. | N/A |

## Phase Breakdown

### Phase 0: Feasibility & Dependency Verification
- **Step 0.1**: Inspect `external/Domino/code/` for CUDA-specific imports (e.g., `bitsandbytes`, `flash_attn`). If found, plan a fallback to pure-Python speculative decoding or a compatible `transformers` implementation.
- **Step 0.2**: **Runtime Feasibility Check**: Execute a minimal import test of the vendored code on CPU. If the code strictly requires CUDA kernels (e.g., for draft acceptance logic) and cannot run on CPU, the system MUST fail early with a clear "Not CPU-Feasible" error message. Do NOT attempt to stub core algorithms. If the code is pure Python/transformers-compatible, proceed.
- **FR-002 Mapping**: Ensures no CUDA imports occur.
- **FR-006 Mapping**: Logs library versions.

### Phase 1: Environment & Dependency Setup (Addresses FR-002, FR-006)
- **Step 1.1**: Create `requirements.txt` pinning `torch` to a CPU-only wheel (e.g., `torch --index-url https://download.pytorch.org/whl/cpu`).
- **Step 1.2**: Ensure `transformers` and `accelerate` are installed without CUDA dependencies.
- **Step 1.3**: Implement a pre-flight check script to verify no GPU-specific libraries are imported.
- **Step 1.4**: **Network Timeout Handling**: Implement a retry mechanism (up to 3 attempts) for `pip install` commands to handle network timeouts as required by the Edge Case.
- **FR-002 Mapping**: This phase ensures no CUDA imports occur.
- **FR-006 Mapping**: This phase logs library versions.

### Phase 2: Model Selection & Hardware Detection (Addresses FR-004, Edge Case: Model Size)
- **Step 2.1**: Implement hardware detection logic to force `device_map="cpu"`.
- **Step 2.2**: **Automatic Model Substitution**: Define a model selection strategy: If the paper's target (Qwen) is unavailable or too large, the system MUST automatically select `Qwen/Qwen2-0.5B-Instruct` (Draft) and `Qwen/Qwen2-1.8B-Instruct` (Target) as CPU-tractable proxies.
  - **Verification**: Before selection, verify that the Qwen2 architecture supports the specific Domino mechanism (e.g., attention masking). If not, flag the limitation.
  - **Logging**: This substitution MUST be explicitly logged in the output artifacts as a mandatory system behavior.
- **Step 2.3**: Add a memory check (approximate parameter count) to prevent OOM crashes.
- **Step 2.4**: Implement mandatory logging of the model substitution (Qwen3 -> Qwen2-1.8B/0.5B) in the output artifacts.
- **FR-004 Mapping**: Dynamic device configuration.
- **Edge Case Mapping**: Graceful fallback to smaller models.

### Phase 3: Benchmark Execution & Timeout (Addresses FR-001, FR-005, SC-001, SC-002)
- **Step 3.1**: **Primary Entry Point**: The `run_hf_benchmark.sh` script remains the primary entry point. The Python wrapper handles environment setup, timeout enforcement, and artifact parsing, but does not replace the script's execution.
- **Step 3.2**: Configure the benchmark to run a small sample (e.g., 5 prompts) repeated **10 times** (n=10) to ensure completion within time limits and provide statistical power.
- **Step 3.3**: Monitor RAM usage during execution; abort if > 6.5 GB.
- **FR-001 Mapping**: Execution of the benchmark script.
- **FR-005 Mapping**: Timeout mechanism implementation.
- **SC-001/SC-002 Mapping**: Ensuring runtime and memory constraints are met.

### Phase 4: Metrics Extraction & Comparison Report (Addresses FR-003, FR-007, SC-003, SC-004)
- **Step 4.1**: Parse the generated `results_*.json` or log files to extract raw latency values for each of the 10 runs. **Extract statistical objects**: `baseline_latency_ms` and `domino_latency_ms` must be extracted as objects containing `mean`, `std`, `min`, `max` from the aggregated run data, matching the schema.
- **Step 4.2**: **Aggregation Logic**: Aggregate the 10 runs into statistical objects: `mean`, `std`, `min`, `max` for `baseline_latency`, `domino_latency`, and `speedup_ratio`. This matches the `contracts/benchmark_metrics.schema.yaml` SSoT.
- **Step 4.3**: **Statistical Rigor**: Calculate `speedup_ratio` for **each individual run**, then aggregate these ratios to compute the final `mean`, `std`, `min`, `max`. Do NOT aggregate latencies first.
- **Step 4.4**: Generate a `validation_report.md`:
  - **Mechanism Pass**: If `mean_speedup_ratio` > 1.0 (with 95% CI > 1.0), status is "PASS".
  - **Paper Claim Check**: Compare to a substantial improvement factor. Explicitly state "N/A (Hardware Mismatch: CPU vs GPU)" and do not fail based on a 20% tolerance.
  - **Model Substitution**: Log the specific Draft/Target pair used.
  - **Methodological Limitation**: Explicitly acknowledge that the speedup ratio is an emergent property of the specific model pair and hardware, and that the result validates the *algorithmic feasibility* on CPU, not the specific magnitude of the GPU claim.
- **FR-003 Mapping**: Structured metrics generation.
- **FR-007 Mapping**: Comparison logic (decoupled from invalid tolerance).
- **SC-003/SC-004 Mapping**: Valid speedup and hardware logging.

### Phase 5: Contract Validation & Documentation (Addresses SC-005, Data Model)
- **Step 5.1**: Validate the output JSON against `contracts/benchmark_metrics.schema.yaml` (the single SSoT). The conflicting `metrics.schema.yaml` is deprecated and ignored.
- **Step 5.2**: Ensure no CUDA errors occur in logs (SC-005).
- **Step 5.3**: Finalize `quickstart.md` and `data-model.md`.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Qwen3 model unavailable or too large for 7GB RAM | High | Use `Qwen2-0.5B` (Draft) + `Qwen2-1.8B` (Target) as verified CPU-tractable proxies; explicitly log substitution. |
| `transformers` defaults to CUDA on some runners | Medium | Explicitly set `CUDA_VISIBLE_DEVICES=""` and `device_map="cpu"` in the runner script. |
| Benchmark takes > 45 mins | High | Reduce prompt count to 5; repeat 10 times; implement hard timeout kill. |
| Paper's 5.49x speedup not achievable on CPU | Medium | Document that speedup on CPU is expected to be lower (e.g., modest to moderate); the goal is *positive* speedup (>1.0x) to validate the algorithm, not exact replication of GPU numbers. |
| Vendored code requires CUDA kernels | High | Phase 0 Step 0.2 will detect this; fail early with "Not CPU-Feasible" error. |
