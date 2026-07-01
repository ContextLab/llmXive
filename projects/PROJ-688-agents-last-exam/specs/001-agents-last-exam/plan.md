# Implementation Plan: Agents' Last Exam Reproduction

**Branch**: `688-agents-last-exam-repro` | **Date**: 2024-05-21 | **Spec**: `specs/688-agents-last-exam-repro/spec.md`
**Input**: Feature specification from `specs/688-agents-last-exam-repro/spec.md`

## Summary

Reproduce the "Agents' Last Exam" benchmark by initializing the `ale_run` environment, executing a representative task (e.g., `ar_full_300`) using a `dummy` agent to validate the **execution pipeline**, and generating a report that compares the observed binary outcome against the paper's qualitative description of that task tier. 

**Critical Scope Clarification**: Due to the single-task sample size (N=1) and the use of a dummy agent (for pipeline validation only), this project **cannot** statistically validate the paper's aggregate claims (e.g., "low average pass rate"). The goal is strictly to verify **pipeline reproducibility** (can the code run without crashing, produce artifacts, and handle timeouts/errors) rather than **benchmark validity** (do the results match the paper's statistical claims). The validation report will explicitly state this limitation.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `ale_run` (cloned submodule), `docker` (for sandbox), `pytest` (for validation logic), `pyyaml`  
**Storage**: Local filesystem (`artifacts/` directory for trajectories and summaries)  
**Testing**: `pytest` (contract tests for artifact existence, integration tests for task execution)  
**Target Platform**: GitHub Actions Free-Tier Runner (Linux, 2 CPU, ~7 GB RAM)  
**Project Type**: CLI / Reproduction Pipeline  
**Performance Goals**: Single task execution < 60 minutes; Total job < 6 hours  
**Constraints**: No GPU/CUDA; No 8-bit/4-bit quantization; Must handle missing API keys gracefully  
**Scale/Scope**: Single representative task (e.g., `ar_full_300`) for pipeline validation; Full suite deferred  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (SSoT)**: The plan explicitly clones the source repository and pins the environment to ensure the reproduction is deterministic where possible.
- **Principle II (Real-Call Testing)**: The plan utilizes a `dummy` agent. Per Principle II's fallback clause, this is permitted **only** for pipeline validation (infrastructure, I/O, timeouts) when real API calls are unavailable or when the primary goal is infrastructure verification. The plan explicitly distinguishes this from "Agent Performance Validation" which would require real calls.
- **Principle III (Data Integrity)**: The plan mandates the generation of `trajectory.json` and `summary.json` for every run, which will be validated against the `task_artifact.schema.yaml` to ensure artifacts are preserved for audit.
- **Principle IV (Error Handling)**: The plan includes specific steps to detect missing API keys and sandbox failures, ensuring the pipeline fails gracefully rather than crashing.
- **Principle V (Validation)**: The plan requires a `validation_report.md` that explicitly compares results to paper claims, but **redefines the scope** of this comparison to "Pipeline Reproducibility vs. Paper Setup" rather than "Statistical Validation," acknowledging the N=1 limitation.

## Project Structure

### Documentation (this feature)

```text
specs/688-agents-last-exam-repro/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── task_artifact.schema.yaml
│   └── validation_report.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/688-agents-last-exam-repro/
├── external/
│   └── agents-last-exam/   # Cloned submodule
├── scripts/
│   ├── setup-plan.sh       # Initialization and dependency install
│   ├── run-task.sh         # Wrapper to execute a single task with timeout
│   └── generate-report.sh  # Aggregates artifacts and creates validation report
├── artifacts/
│   └── [task_id]/
│       ├── trajectory.json
│       └── summary.json
└── output/
    └── validation_report.md
```

**Structure Decision**: The plan uses a flat script-based structure in `scripts/` to orchestrate the cloned submodule, ensuring minimal overhead and easy debugging on CI. Artifacts are isolated in `artifacts/` to prevent cross-contamination between runs. A schema validation step is inserted before report generation to ensure data model compliance.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations found. | N/A |

## FR/SC Coverage Map

| ID | Type | Plan Phase/Step Addressing It |
|----|------|-------------------------------|
| FR-001 | Functional | Phase 1: Environment Initialization (Clone & Install) |
| FR-002 | Functional | Phase 2: Task Execution (Run `ar_full_300` with dummy) |
| FR-003 | Functional | Phase 2: Artifact Generation (trajectory/summary) |
| FR-004 | Functional | Phase 1: API Key Detection & Error Handling |
| FR-005 | Functional | Phase 3: Validation Report Generation |
| FR-006 | Functional | Phase 2: Timeout Enforcement (60m limit) |
| FR-007 | Functional | Phase 2: Sandbox Error Handling (Log & Continue) |
| FR-008 | Functional | Phase 1 & 2: CPU-only constraint enforcement |
| SC-001 | Success | Phase 3: Report compares binary outcome to paper's tier description (not aggregate rate) |
| SC-002 | Success | Phase 2: Artifact existence check (schema validated) |
| SC-003 | Success | Phase 2: Timeout enforcement check |
| SC-004 | Success | Phase 1 & 2: Error handling tests (no tracebacks) |
| SC-005 | Success | Phase 3: Report explicitly states N=1 limitation and comparison logic |
| SC-006 | Success | Phase 1 & 2: Execution on GitHub Actions Free Tier |