# Implementation Plan: AutoResearchClaw Reproduction & Validation

**Branch**: `001-autoresearchclaw-repro` | **Date**: 2025-05-23 | **Spec**: `specs/001-autoresearchclaw-repro/spec.md`
**Input**: Feature specification from `specs/001-autoresearchclaw-repro/spec.md`

## Summary

This feature implements a validation harness for the `AutoResearchClaw` system, focusing on reproducing its core "self-reinforcing" research loop within the strict constraints of a GitHub Actions free-tier runner (CPU-only, 7GB RAM, 6h limit). The approach involves creating a lightweight execution engine that wraps the vendored `AutoResearchClaw` code, enforcing memory limits, simulating Human-in-the-Loop (HITL) interventions, and managing a persistent "Evolution Log" to track and prevent error recurrence. The validation will target a minimal set of synthetic or small-scale topics to verify the pipeline's ability to generate artifacts, heal code errors, and incorporate feedback without requiring GPU acceleration or large-scale data processing.

**Critical Note on Scope**: This pilot validates the *mechanism* of the loop (execution, error handling, HITL compliance) using synthetic data. It explicitly does *not* validate the *scientific validity* of the research outputs or the *semantic learning* capabilities claimed in the original paper, as those require real-world data and statistical power beyond the N=5 pilot size.

## Technical Context

**Language/Version**: Python 3.11 (required by `AutoResearchClaw` and standard scientific stack)
**Primary Dependencies**: `auto-researchclaw` (vendored submodule), `pytest`, `pandas`, `numpy`, `psutil` (for memory monitoring), `pyyaml` (for config/logs), `requests` (for API mocking).
**Storage**: Filesystem-based (JSON logs for Evolution Log, JSON/YAML for HITL configs, temporary CSV/Parquet for data). No external database.
**Testing**: `pytest` (unit tests for components, integration tests for the full loop).
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).
**Project Type**: CLI tool / Validation Harness.
**Performance Goals**: Complete one research cycle (hypothesis → report) in ≤ 6 hours; memory usage ≤ 7 GB; self-healing retry < 3 attempts per error.
**Constraints**: No GPU/CUDA; no large model training; strict 7 GB RAM cap (enforced via `psutil`); Timeout (enforced via CI job config and internal checkpointing).
**Scale/Scope**: 5 diverse topics (minimal set for SC-001 viability check); synthetic/small public datasets only.

> **Entity Mapping**: The plan executes multiple instances of the `ResearchCycle` entity defined in `data-model.md`.
> **Data Flow Mapping**: The `error_healer.py` component writes to the `EvolutionLog` entity, and `memory_guard.py` writes to the `MemorySnapshot` entity (as defined in `data-model.md`).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**STATUS: BLOCKING GAP**
The project constitution file (`projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/.specify/memory/constitution.md`) was **not provided** in the input.
Per FR-030 and Constitution Principle I (SSoT), the plan cannot be validated against a missing constitution.
- **Action Required**: The `constitution.md` file must be created and populated with the project's SSoT principles.
- **Current State**: The "Constitution Check" section below is a placeholder. No principles can be mapped or verified until the source file exists.
- **Impact**: The plan cannot claim compliance with any constitutional principle until this file is provided and the check is re-run.

*Placeholder for Future Content:*
*Once `constitution.md` is available, this section will list each numbered principle (e.g., Const-Principle-V) and map it to specific plan phases/lines.*

## Project Structure

### Documentation (this feature)

```text
specs/001-autoresearchclaw-repro/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── __init__.py
│   ├── runner.py            # Main execution loop wrapper
│   ├── memory_guard.py      # RAM monitoring and sampling trigger (writes to MemorySnapshot)
│   └── checkpoint.py        # State persistence for 6h timeout
├── validation/
│   ├── __init__.py
│   ├── hitl_controller.py   # HITL pause/resume logic
│   ├── error_healer.py      # Pivot/Refine loop implementation (writes to EvolutionLog)
│   └── artifact_validator.py# Checks for non-empty, valid outputs
├── data/
│   ├── __init__.py
│   └── synthetic_generators.py # Small, CPU-tractable data generators
├── config/
│   ├── topics.yaml          # Minimal topic manifest
│   └── hitl_config.yaml     # Intervention point definitions
└── logs/
    └── evolution_log.json   # Persistent failure/lesson store

tests/
├── contract/
│   └── test_schemas.py      # Validates output against contracts
├── integration/
│   └── test_full_loop.py    # End-to-end CPU run test
└── unit/
    ├── test_memory_guard.py
    ├── test_error_healer.py
    └── test_hitl_controller.py
```

**Structure Decision**: Single project structure (`src/`, `tests/`, `config/`) is selected to minimize overhead and keep the validation harness tightly coupled with the vendored `AutoResearchClaw` submodule. This avoids the complexity of multi-repo setups while allowing easy import of the submodule's core logic.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Custom Memory Guard | The system must proactively sample data before OOM occurs to prevent runner crash. | Standard Python `try/except` for OOM is too late; the process dies before logging the failure. |
| Evolution Log (JSON) | Required for cross-run learning (FR-004) to prevent recurrence. | In-memory state is lost between CI runs; a persistent file is necessary. |
| HITL Simulation | Required to validate FR-003 (HITL mode) without a real UI. | A real UI would require a web server and browser, exceeding the 6h/7GB budget. |
| **Synthetic Data** | Required to validate *mechanism* without real-world data complexity. | Real-world data is not available/verified for this specific pilot; synthetic data allows controlled testing of error handling. |