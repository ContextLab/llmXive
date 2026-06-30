# Implementation Plan: Self-Distilled Agentic Reinforcement Learning (SDAR) Reproduction

**Branch**: `579-https-arxiv-org-abs-2605-15155-repro` | **Date**: 2024-05-22 | **Spec**: `specs/579-https-arxiv-org-abs-2605-15155-repro/spec.md`
**Input**: Feature specification from `specs/579-https-arxiv-org-abs-2605-15155-repro/spec.md`

## Summary

This feature reproduces the core execution pipeline of the Self-Distilled Agentic Reinforcement Learning (SDAR) paper (arXiv:2605.15155) using the vendored codebase. The primary requirement is to validate that the SDAR algorithm, including its self-distillation gating and RL components, executes successfully on a CPU-only GitHub Actions runner with limited CPU and RAM resources without GPU acceleration. 

**Critical Distinction**: This project performs **Execution Verification** (validating the code runs and the mechanism is present), not **Statistical Validation** (proving the algorithm improves performance by +[deferred]). The 10-step training run is designed to confirm the *gating mechanism activates* and the *loss functions compute*, not to converge the model.

## Technical Context

**Language/Version**: Python 3.10+ (inferred from SDAR/ALFWorld ecosystem)
**Primary Dependencies**: Ray (distributed computing), PyTorch (CPU-only), ALFWorld (environment), HuggingFace `transformers`, `verl` (if used by SDAR), `pytest`.
**Storage**: Local filesystem for checkpoints (`.pt`), logs (`.json`/`.txt`), and temporary environment state.
**Testing**: `pytest` for unit tests; integration tests via shell scripts executing entry points.
**Target Platform**: Linux (GitHub Actions runner `ubuntu-latest`), CPU-only.
**Project Type**: Research reproduction / CLI pipeline.
**Performance Goals**:
- Wall-clock time ≤ 6 hours for full pipeline (sanity + train + eval).
- Memory usage ≤ 6 GB (leaving 1GB headroom for OS/ALFWorld overhead).
- No CUDA errors.
**Constraints**:
- No GPU hardware or CUDA drivers available.
- No `load_in_8bit`, `bitsandbytes`, or `device_map="cuda"`.
- Hard timeout of 60s per evaluation task (FR-005).
- Dataset/Environment: ALFWorld (simulated).
**Scale/Scope**:
- Training: 10 steps, batch size 1.
- Evaluation: A set of tasks.
- Model: CPU-tractable approximation (verified in Phase 0).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

**STATUS**: BLOCKING GAP - Constitution Not Found

*The project constitution file (`projects/PROJ-579-https-arxiv-org-abs-2605-15155/.specify/memory/constitution.md`) was not provided in the input. Per protocol, the plan cannot verify compliance with specific constitutional principles (e.g., SSoT, No Silent Fallbacks) without the source document.*

**Action Required**:
1.  **Gate**: This plan cannot pass the "Constitution Check" gate until `constitution.md` is injected.
2.  **Placeholder**: The following structure is reserved for the actual check once the document is available:
    *   *Principle I (SSoT)*: [Pending Verification]
    *   *Principle II (No Silent Fallbacks)*: [Pending Verification]
    *   *Principle V (Real-Call Testing)*: [Pending Verification]

*Until the constitution is provided, the plan assumes standard scientific reproducibility principles but explicitly flags the missing SSoT verification as a known gap.*

## Project Structure

### Documentation (this feature)

```text
specs/579-https-arxiv-org-abs-2605-15155-repro/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
# Option 1: Single project (DEFAULT) - Leveraging vendored submodule
external/SDAR/             # Vendored submodule containing the SDAR codebase
├── tests/
│   └── ray_cpu/
│       └── check_worker_alive/
│           └── main.py    # Entry point for FR-001
├── agent_system/          # Core SDAR implementation
│   ├── train.py           # Entry point for FR-002
│   └── eval.py            # Entry point for FR-004
├── requirements.txt
└── README.md

outputs/                   # Generated artifacts (not committed)
├── logs/
│   ├── train_log.json
│   └── eval_log.json
├── health/
│   └── ray_health.json    # Ray sanity check output
└── checkpoints/
    └── step_5.pt

scripts/
├── setup_env.sh           # Installs deps, initializes Ray CPU
├── run_sanity_check.sh    # Executes FR-001
├── run_mini_train.sh      # Executes FR-002
└── run_mini_eval.sh       # Executes FR-004
```

**Structure Decision**: The project leverages the existing `external/SDAR` submodule structure. No new complex architecture is introduced; the focus is on wrapping the existing entry points with environment constraints (CPU-only, timeouts) and orchestrating the execution flow via shell scripts. This minimizes code changes and reduces the risk of introducing bugs during the reproduction phase.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project adheres strictly to the spec's minimal scope (a constrained number of steps and tasks). | No complexity violations detected. The approach is intentionally minimal to fit CI constraints. |

## Implementation Phases

### Phase 0: Environment Setup & Sanity Check (FR-001, SC-001, SC-005)
**Goal**: Verify the vendored codebase runs on CPU without GPU errors and validate model backbone feasibility.
1.  **Action**: Create a virtual environment (venv/conda) and install dependencies from `external/SDAR/requirements.txt`.
2.  **Action**: Explicitly set environment variables to disable CUDA (e.g., `CUDA_VISIBLE_DEVICES=""`, `TORCH_USE_CUDA_DSA=0`).
3.  **Action (New)**: **Model Backbone Verification**. Inspect `external/SDAR` config or code to identify the default model backbone.
    - If the default model is GPU-only (e.g., Llama-2-7B) and cannot be swapped via config, **FAIL** this phase and flag a blocking gap: "Vendored code requires GPU; cannot proceed with CPU-only reproduction without code modification."
    - If a CPU-tractable model (e.g., TinyLlama, DistilBERT) is available or configurable, proceed.
4.  **Action**: Execute `python tests/ray_cpu/check_worker_alive/main.py`.
5.  **Verification**:
    - Exit code must be 0.
    - Output must contain "Ray cluster healthy" and "multiple CPUs detected".
    - No "CUDA not found" or `ImportError` for `torch.cuda`.
    - **Artifact**: Generate `outputs/health/ray_health.json` (schema: `ray_health.schema.yaml`).
6.  **Failure Handling**: If Ray fails to initialize, adjust `ray init --num-cpus=2` parameters. If imports fail, isolate dependencies in a fresh venv.

### Phase 1: Minimal Training Run (FR-002, FR-003, SC-002, Mechanism Validation)
**Goal**: Execute a truncated training loop to verify the SDAR algorithm, logging, and *mechanism activation*.
1.  **Action**: Configure `external/SDAR/agent_system/train.py` with hardcoded parameters:
    - `num_steps=10`
    - `batch_size=1`
    - `env=alfworld`
    - `device="cpu"` (explicit override).
    - `model_name="cpu-tractable-model"` (if configurable).
2.  **Action**: Run the training script.
3.  **Verification**:
    - Logs must contain at least 5 entries for "SDAR Gate Loss" and "RL Loss".
    - **New Metric**: Logs must contain `gate_activation_rate` > 0.0% (confirms the self-distillation gate is active and making decisions, not just a dummy pass).
    - A checkpoint file (e.g., `step_5.pt`) must exist in the output directory.
    - Final summary report must show average loss.
4. **Failure Handling**: If CUDA errors occur, verify `device_map` settings. If `gate_activation_rate` is [deferred], verify the gate logic is not short-circuited in the code.

### Phase 2: Evaluation & Metric Reporting (FR-004, FR-005, SC-003, SC-004)
**Goal**: Run evaluation on a tiny subset to verify metric generation and robustness.
1.  **Action**: Configure `external/SDAR/agent_system/eval.py` with:
    - `num_tasks=5`
    - `task_timeout=60` (seconds).
2.  **Action**: Run the evaluation script.
3.  **Verification**:
    - Output must include a "Success Rate" metric (0.0 to 1.0).
    - Logs must record failure reasons (e.g., "Max steps exceeded") for any timeouts.
    - The process must not hang (enforced by timeout).
4.  **Failure Handling**: If a task hangs, the script must catch the timeout signal and proceed to the next task.

### Phase 3: Artifact Consolidation & Reporting (SC-004)
**Goal**: Ensure all artifacts are collected and the total runtime is within limits.
1.  **Action**: Aggregate logs and checkpoints into `outputs/`.
2.  **Action**: Verify total wall-clock time ≤ 6 hours (expected: < 30 mins for this minimal run).
3.  **Action**: Generate a final summary report confirming all Success Criteria are met.

## Risk Management

- **Risk**: ALFWorld dependencies (Thor binaries) fail to download on CI.
  - **Mitigation**: Use a cached Docker image or pre-download binaries if possible; otherwise, rely on the `external/SDAR` submodule's auto-download mechanism with a retry loop.
- **Risk**: Ray resource contention on 2-core runner.
  - **Mitigation**: Explicitly limit Ray to 2 CPUs (`ray init --num-cpus=2`) and ensure no other heavy processes run.
- **Risk**: Infinite loop in ALFWorld environment.
  - **Mitigation**: Enforce the 60s timeout per task (FR-005) at the script level, not just within the environment.
- **Risk**: Vendored code hardcodes a GPU-only model.
  - **Mitigation**: Phase 0 includes explicit model backbone verification. If the model is not CPU-tractable, the plan fails with a clear error message rather than attempting a silent substitution that would break the algorithm's validity.