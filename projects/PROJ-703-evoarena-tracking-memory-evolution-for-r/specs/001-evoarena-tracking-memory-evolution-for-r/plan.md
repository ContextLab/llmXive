# Implementation Plan: EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments

**Branch**: `703-evoarena-tracking-memory-evolution-for-r` | **Date**: 2024-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/703-evoarena-tracking-memory-evolution-for-r/spec.md`

## Summary

Reproduce and validate the "EvoArena" paper findings by executing the vendored `external/EvoArena` codebase on a subset of the TerminalBench-Evo and PersonaMem-Evo datasets. The technical approach involves configuring the environment to run on CPU-only CI resources (limiting model size and data subset), executing baseline and EvoMem agents to generate raw JSON logs and memory patch artifacts, and aggregating these results to compute chain-level accuracy.

**Critical Scope Note**: Due to strict CI constraints (A runtime of approximately six hours is expected based on the current computational estimates, though the exact duration will be determined during the implementation phase., 7GB RAM), this plan executes a **Feasibility & Pipeline Integrity Probe** (N=5 chains per domain) rather than a statistically powered validation. Results will be reported as **Descriptive Statistics** only. The plan explicitly disavows statistical significance claims for this subset. The primary goal is to verify that the vendored code runs, produces valid artifacts, and that the pipeline logic is sound.

## Technical Context

**Language/Version**: Python 3.10+ (inferred from typical LLM agent frameworks and vendored code structure)  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `pandas`, `numpy`, `pyyaml`, `pytest`  
**Storage**: Local file system (JSON logs, CSV/Parquet datasets, patch store directories)  
**Testing**: `pytest` (for unit validation of data loading and artifact integrity), shell scripts for integration flow  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Research Reproduction / Evaluation Pipeline  
**Performance Goals**: Complete evaluation of ~10 chains (5 Terminal, 5 Persona) within 6 hours; <7GB RAM usage peak.  
**Constraints**: No GPU; no large model training; API rate limiting must be handled via backoff; memory patch history must be capped to prevent OOM.  
**Scale/Scope**: Subset evaluation (approx. 10 chains total) to validate logic and metric calculation before full-scale run.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility & Transparency**: The plan mandates the use of vendored code (`external/EvoArena`) and explicitly logs all execution parameters and random seeds to ensure the reproduction is transparent. The Single Source of Truth (SSoT) for reference values is defined in `contracts/reference_values.schema.yaml`.
2.  **Resource Efficiency**: The plan strictly limits the dataset subset size and model configuration to fit within the 7GB RAM and 2 CPU core constraints of the free CI runner, avoiding GPU dependencies.
3.  **Data Integrity**: The plan includes a validation phase (FR-005) to ensure all generated artifacts (JSON logs, patch files) are non-empty and structurally valid before aggregation. Validation logic explicitly enforces schemas defined in `contracts/execution_log.schema.yaml` and `contracts/memory_patch.schema.yaml`.
4.  **Ethical & Safe Execution**: The plan assumes the use of provided API keys with sufficient quota for small-scale testing. **Real API calls are required** for the main validation path; mocked responses are strictly for unit testing the pipeline logic. Includes error handling for rate limits to prevent abusive retry loops.
5.  **Modularity**: The plan separates data loading, agent execution, and result aggregation into distinct logical phases, facilitating independent testing and debugging.

## Project Structure

### Documentation (this feature)

```text
specs/703-evoarena-tracking-memory-evolution-for-r/
├── plan.md              # This file (defines schemas and logic)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Defined in Plan Phase (Schemas)
│   ├── accuracy_summary.schema.yaml
│   ├── execution_log.schema.yaml
│   ├── memory_patch.schema.yaml
│   └── reference_values.schema.yaml
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
external/
└── EvoArena/            # Vendored repository containing agents, benchmarks, and scripts
    ├── agents/          # Baseline and EvoMem agent implementations
    ├── benchmarks/      # TerminalBench-Evo and PersonaMem-Evo logic
    ├── scripts/         # launch_*.sh and evaluation scripts
    └── data/            # Symlinks or copies of dataset subsets

src/
└── evomem_validation/
    ├── __init__.py
    ├── config.py        # Environment and path configuration
    ├── runner.py        # Orchestration logic for baseline and EvoMem runs
    ├── aggregator.py    # Logic to compute accuracy metrics from JSON logs
    └── validators.py    # Logic to check artifact integrity (FR-005) against contracts/

tests/
├── unit/
│   └── test_validators.py
└── integration/
    └── test_evaluation_flow.py
```

**Structure Decision**: The plan adopts a "Validation Wrapper" structure. The vendored `external/EvoArena` code is treated as a black-box library. New code (`src/evomem_validation/`) is minimal and focused solely on orchestration, environment setup, and result aggregation. This minimizes the risk of breaking the vendored code while allowing for custom metrics and validation logic required by the spec.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Custom Aggregation Layer | The spec requires specific comparison against paper claims (SC-001, SC-002) and chain-level accuracy (FR-004) which may not be the default output of the vendored scripts. | Relying solely on vendored output logs would require manual post-processing, violating the automated validation requirement. |
| Artifact Validation Module | FR-005 requires strict validation of JSON structure and non-empty files before aggregation to prevent cascading errors. | Skipping validation risks aggregating corrupted data, leading to false negative/positive results in SC-001. |
| Reference Values Schema | To satisfy Constitution Principle I (SSoT), reference values must be externalized to a schema rather than hardcoded. | Hardcoding values risks silent drift and makes updates difficult. |
