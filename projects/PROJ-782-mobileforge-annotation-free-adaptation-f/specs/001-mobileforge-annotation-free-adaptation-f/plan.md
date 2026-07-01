# Implementation Plan: MobileForge: Annotation-Free Adaptation for Mobile GUI Agents with Hierarchical Feedback-Guided Policy Optimization

**Branch**: `782-mobileforge-reproduction` | **Date**: 2024-05-22 | **Spec**: `specs/782-mobileforge-reproduction/spec.md`

## Summary

This plan implements the reproduction and validation of the "MobileForge" framework on a CPU-only, free-tier CI environment. The primary goal is to execute the rollout pipeline (`rollout/run.py`), generate hierarchical feedback via the curriculum generator (`explore/curriculum_generator...`), and compute the Pass@K metric against the AndroidWorld benchmark, where K represents a configurable number of sampled attempts. The technical approach prioritizes CPU-tractable inference (using a quantized large language-vision model via `bitsandbytes` on CPU or a smaller fallback model), mock/simulated Android environments to bypass emulator resource limits, and strict memory/time monitoring to adhere to the 7GB RAM / 6-hour job constraints.

**Critical Limitation Acknowledgement**: Due to the N=10 task sample size, statistical claims are limited to "Pilot Feasibility". The comparison against the paper's baseline is strictly "Contextual Observation Only" and not a scientific validation of performance superiority.

## Technical Context

**Language/Version**: Python 3.10+ (Required for `bitsandbytes` CPU support and modern `transformers` features)
**Primary Dependencies**: `transformers`, `torch` (CPU wheel), `bitsandbytes` (CPU-enabled), `accelerate`, `datasets`, `pytest`, `pandas`, `numpy`, `scipy`
**Storage**: Local filesystem (JSONL for trajectories, JSON for metrics), temporary RAM for model loading
**Testing**: `pytest` (Unit tests for parsing/metrics, Integration tests for pipeline execution on mock data)
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, ~7GB RAM)
**Project Type**: Computational Research / Reproduction Pipeline
**Performance Goals**: <60 mins for 10-task rollout; <6h total job time; <6.5GB peak RAM
**Constraints**: No GPU; No full Android Emulator; No external network calls for large APKs (use cached/mock); Hard 300s timeout per task.

## Constitution Check

*Note: No project-specific `constitution.md` was provided. This plan adheres to the **Standard Research Integrity & Reproducibility Charter (v1.0)** defined below, which serves as the project's operational constitution.*

**Standard Research Integrity & Reproducibility Charter (v1.0)**:
1.  **P1 (Reproducibility)**: Code and data must be executable without external, unverified dependencies.
2.  **P2 (Resource Integrity)**: Execution must not exceed allocated compute resources (RAM, Time).
3.  **P3 (Data Validity)**: Generated data must be validated against defined schemas and quality heuristics.
4.  **P4 (Statistical Rigor)**: Metrics must be calculated using methods appropriate for the sample size (e.g., Exact Binomial for N<30).
5.  **P5 (Transparency)**: All assumptions, limitations, and environment differences must be explicitly stated.

**Plan Mapping to Charter Principles**:
*   **P1 (Reproducibility)**: Mapped to **Phase 0** (Verify `AndroidWorld` registry) and **Phase 2** (Use vendored code).
*   **P2 (Resource Integrity)**: Mapped to **Compute Feasibility Strategy** (Memory monitor, timeout) and **Phase 2** (Sequential execution).
*   **P3 (Data Validity)**: Mapped to **Phase 1** (Schema validation against `contracts/`) and **Phase 3** (Hint heuristic checks).
*   **P4 (Statistical Rigor)**: Mapped to **Phase 3** (Exact Binomial CI calculation, not Bootstrap).
*   **P5 (Transparency)**: Mapped to **Summary** (Limitation acknowledgement) and **Research.md** (Environment differences).

## Project Structure

### Documentation (this feature)

```text
specs/782-mobileforge-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── trajectory.schema.yaml
│   ├── feedback.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── mobileforge/
│   ├── rollout/
│   │   └── run.py              # Entry point for trajectory generation
│   ├── feedback/
│   │   └── curriculum_generator.py # HiFPO feedback generation
│   ├── evaluation/
│   │   └── androidworld/
│   │       └── run.py          # Evaluation against benchmark
│   ├── metrics/
│   │   └── pass_k.py           # Pass@3 calculation with Exact Binomial CI
│   └── utils/
│       ├── monitor.py          # Memory/CPU monitoring
│       └── timeout.py          # Task timeout enforcement
├── tests/
│   ├── contract/               # Schema validation tests
│   ├── integration/            # Pipeline execution tests (mock env)
│   └── unit/                   # Metric calculation tests
└── data/                       # Local cache for trajectories/metrics
    ├── trajectories.jsonl
    ├── feedback.jsonl
    ├── evaluation_results.json
    └── monitoring_logs.json
```

**Structure Decision**: Single `src/mobileforge` module structure. This minimizes import complexity for the reproduction pipeline and aligns with the existing vendored codebase structure. Tests are separated into `contract`, `integration`, and `unit` to validate the specific requirements (schema, pipeline flow, metric logic) independently.

## Phase Breakdown

### Phase 0: Research & Feasibility (Research.md)
*   **Goal**: Confirm dataset availability, model feasibility on CPU, and identify specific constraints of the `MobileForge` codebase.
*   **Actions**:
    *   Verify `AndroidWorld` registry structure and task definitions.
    *   Validate `Qwen2.5-VL-7B` CPU inference feasibility (quantization strategy).
    *   **Simulation Fidelity Validation**: Compare 3 mock trajectories against known task logic or gold standards (if available) to verify state transitions are valid before full rollout.
    *   Define the exact schema for trajectories and feedback signals.

### Phase 1: Data Model & Contracts (Data-Model.md, Contracts/)
*   **Goal**: Define strict schemas for all data artifacts to ensure pipeline integrity.
*   **Actions**:
    *   Define `Trajectory` schema (Task ID, Steps, Final Status).
    *   Define `Feedback` schema (Error Type, Hint Text, Step Context, Validation Rules).
    *   Define `Metrics` schema (Pass@k, Exact Binomial CI bounds).
    *   Define `System Monitoring Log` schema (Memory usage, CPU usage, Timestamp).
    *   Create YAML contract files (`contracts/trajectory.schema.yaml`, etc.) for automated validation.

### Phase 2: Implementation (Tasks.md - Future Step)
*   **Goal**: Implement the pipeline scripts and monitoring logic.
*   **Actions**:
    *   Implement `rollout/run.py` with memory monitoring and timeout enforcement.
    *   Implement `feedback` generation logic with hint validation (length + keyword heuristics).
    *   Implement `evaluation` and `metrics` calculation with Exact Binomial CI.
    *   Create mock environment interface for CI compatibility.

### Phase 3: Verification & Reporting
*   **Goal**: Execute the full pipeline on a subset of tasks and validate results.
*   **Actions**:
    *   Run a multi-task rollout.
    *   Generate feedback and validate hint quality (syntactic proxy).
    *   Compute Pass@k and report Exact Binomial CI (acknowledging wide interval).
    *   **Contextual Observation Only**: Compare results to paper baseline (if available) but explicitly state the comparison is invalid for scientific validation due to environment differences.
    *   Produce final report.

## Compute Feasibility Strategy

*   **Model**: Use `Qwen-VL-7B` in 4-bit quantization (if `bitsandbytes` CPU support is stable).
*   **Tiered Fallback**: If large-scale quantization exceeds available RAM (accounting for `MobileGym` overhead), the plan switches to `Qwen2-VL-2B` (or similar small CPU model) and logs a "DEGRADED_MODE" warning. This is a feasibility test only.
*   **Environment**: Replace full Android Emulator with a "Mock" or "Headless" interface that simulates screen states and actions without the overhead of a VM. This is critical for the 7GB RAM limit.
*   **Data**: Process tasks sequentially with garbage collection enforced between tasks to prevent memory accumulation.
*   **Timeout**: Enforce a hard time limit per task via `signal` or `timeout` decorators.

## Risk Mitigation

*   **Risk**: OOM Crash on CPU inference.
    *   *Mitigation*: Implement `FR-002` memory monitor; fallback to `Qwen2-VL-2B`; reduce batch size to a minimal feasible value.
*   **Risk**: Missing Model Weights.
    *   *Mitigation*: Implement `FR-007` startup check for `Qwen2.5-VL-7B`; clear error message with instructions.
*   **Risk**: Infinite Loops in Agent.
    *   *Mitigation*: Implement `FR-006` 300s timeout; log `TIMEOUT` status.
*   **Risk**: Invalid Feedback Generation.
    *   *Mitigation*: Implement `FR-005` hint validation (length + keyword heuristics); flag/reject invalid hints.