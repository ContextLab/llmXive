# Implementation Plan: AdaPlanBench Reproduction & Validation

**Branch**: `668-ada-plan-bench-reproduction` | **Date**: 2024-05-22 | **Spec**: `specs/668-ada-plan-bench-reproduction/spec.md`
**Input**: Feature specification from `/specs/668-ada-plan-bench-reproduction/spec.md`

## Summary

This project reproduces and validates the "AdaPlanBench" benchmark for evaluating adaptive planning in Large Language Model (LLM) agents under world and user constraints. The technical approach involves initializing the vendored git submodule containing the benchmark code, configuring a CPU-only execution environment, and running a **stratified subset** of the 307 household tasks (20 tasks: 5 tasks each for constraint counts 0, 1, 2, and 3+) using a **TinyLlama CPU-tractable LLM** as the primary agent for scientific validation. A deterministic Mock Agent is used **strictly** for infrastructure integration testing (verifying the loop logic) and baseline validation, but **never** for calculating the 'adaptive planning accuracy' metric. The plan ensures strict adherence to the GitHub Actions free-tier constraints (2 CPU, 7GB RAM, no GPU) by avoiding heavy model training, quantization requiring CUDA, or large-LLM inference. The primary output is a validation of the "adaptive planning accuracy" metric and the "constraint accumulation" mechanism described in the paper, with a fallback strategy if the LLM lacks sufficient reasoning capability.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `git` (for submodule), `pytest`, `requests`, `huggingface_hub` (for model loading), `jsonschema` (for validation), `numpy` (for metric calculation), `transformers` (CPU-optimized).  
**Storage**: Local filesystem (JSON artifacts in `outputs/`), Git submodule data.  
**Testing**: `pytest` (unit tests for logic, integration tests for runner execution).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Research/Reproduction CLI tool.  
**Performance Goals**: 
  - **Setup**: < 10 minutes.
  - **Loop Logic (parsing, checking, I/O)**: < 60s per task (excluding LLM inference). This target is feasible on 2 vCPU for pure Python logic.
  - **Full Execution**: Expected to exceed 60s per task due to CPU inference; total job < 6 hours.
  - **Subset Run**: 20 tasks (stratified) < 4 hours.
**Constraints**: CPU-only execution; No CUDA/GPU libraries; Memory footprint < 7GB; Disk usage < 14GB; No external API reliance (local model preferred).  
**Scale/Scope**: 
  - **Subset**: 20 tasks from the 307-task "MacGyver" housing domain.
  - **Stratification**: Multiple tasks with 0 constraints, multiple with 1, multiple with 2, and multiple with 3+ constraints. This ensures sufficient variance to validate the "performance degradation" trend (SC-005).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Note: The per-project `constitution.md` file was not provided in the inputs. The following check is **provisional** and based on the requirements explicitly defined in the `spec.md` (FR-001 through FR-006). Final verification of constitutional principles requires the missing `constitution.md` file.*

*   **Provisional Principle 1 (Reproducibility)**: The plan mandates the use of the vendored git submodule and a pinned dependency list to ensure the environment is reproducible across CI runs, satisfying the spec's requirement for a reproducible environment (FR-001).
*   **Provisional Principle 2 (Compute Feasibility)**: The plan strictly forbids GPU/CUDA usage and mandates the use of a CPU-tractable model (TinyLlama) or mock agent, ensuring the job completes within the 6-hour limit on a free-tier runner, satisfying the spec's compute constraints (US-3).
*   **Provisional Principle 3 (Data Integrity)**: The plan includes a validation step (FR-003) to ensure dataset files exist and are readable before execution, preventing silent failures, satisfying the spec's data integrity requirements.
*   **Provisional Principle 4 (Transparency)**: The plan requires logging of all constraint violations and plan revisions (FR-006), ensuring the "adaptive" mechanism is observable and auditable, satisfying the spec's transparency requirements.
*   **Provisional Principle 5 (Minimalism)**: The plan avoids unnecessary complexity by using a Mock Agent for infrastructure validation and a small, stratified subset of data for scientific validation, rejecting the need for full-scale 307-task runs in the initial validation phase, satisfying the spec's scope constraints.

## Project Structure

### Documentation (this feature)

```text
specs/668-ada-plan-bench-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
# Option 1: Single project (DEFAULT)
src/
├── ada_bench/
│   ├── __init__.py
│   ├── runner.py           # Main execution loop (wrapped from submodule)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── mock_agent.py   # Deterministic mock for infrastructure testing ONLY
│   │   └── cpu_llm_agent.py # TinyLlama wrapper for scientific validation
│   ├── constraints/
│   │   ├── __init__.py
│   │   └── checker.py      # Constraint validation logic
│   └── metrics/
│       ├── __init__.py
│       └── calculator.py   # Accuracy and accumulation metrics
├── tests/
│   ├── unit/
│   │   ├── test_constraint_checker.py
│   │   └── test_metrics.py
│   └── integration/
│       └── test_runner.py
├── domain_metadata/        # Vendored via submodule
│   └── housing/
│       └── final/
│           └── query_housing_macgyver_resample.json
└── outputs/                # Runtime artifacts (JSON logs)
```

**Structure Decision**: A single project structure is selected to minimize overhead. The core logic is wrapped in a `src/ada_bench` package to isolate the vendored submodule code from the project's own testing and metric calculation logic. The `domain_metadata` is treated as a read-only data source loaded via the submodule.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. | N/A |