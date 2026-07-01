# Implementation Plan: OpenThoughts-Agent Data Pipeline Validation & Reproduction

**Branch**: `[780-openthoughts-agent-validation]` | **Date**: 2024-06-20 | **Spec**: `specs/780-openthoughts-agent-validation/spec.md`
**Input**: Feature specification from `/specs/780-openthoughts-agent-validation/spec.md`

## Summary

This feature implements a CPU-only validation pipeline to verify the **code structure and robustness** of the "OpenThoughts-Agent" data generation phase. Due to the lack of access to the real "TaskTrove" API (as confirmed in `research.md`), the project scope is strictly limited to:
1.  Verifying that the pipeline code executes correctly on CPU-only CI.
2.  Validating that the pipeline handles API errors, retries, and schema conformance robustly (using simulated/mocked responses).
3.  Generating a report that explicitly flags any comparisons to the paper's claims (data volume, diversity, timing) as **Blocked** due to missing real data.

The implementation adheres to CPU-only constraints, avoids all GPU/CUDA operations, and ensures robust error handling for missing submodules and empty datasets.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `open-thoughts-agent` (submodule), `requests` (for API calls), `pydantic` (for schema validation), `pytest` (for testing)
**Storage**: Local filesystem (`data/generated/`, `results/`)
**Testing**: `pytest` (unit tests for schema validation, integration tests for pipeline execution with mocks)
**Target Platform**: Linux server (GitHub Actions free-tier: 2 CPU, 7GB RAM)
**Project Type**: CLI/Data Pipeline
**Performance Goals**: Generate 10 tasks in < 10 minutes on CPU (local logic only); < 1GB RAM usage during generation.
**Constraints**: CPU-only (no CUDA/GPU); Implement a retry mechanism with a limited number of attempts and an exponential backoff strategy (e.g., 5s) to handle transient API failures, as discussed in [Citation].; fail-fast on missing submodules; no external GPU clusters.
**Scale/Scope**: Small-scale validation

The research question investigates the efficacy of the proposed framework across a diverse set of tasks. The method involves a pilot study using a limited, representative subset of tasks to assess initial feasibility and identify potential failure modes before full-scale deployment. (References to be cited as appropriate).; full model training and real data generation out of scope.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Governing Constraints

*Note: No `constitution.md` file was provided in the project inputs. The plan adheres directly to the explicit requirements and assumptions in `spec.md`.*

- **Constraint 1 (Reproducibility Scope)**: The plan explicitly limits "reproduction" to **Code Structure Validation**. Comparison of data volume/diversity against the paper is marked as **Blocked** due to inaccessible API (see `research.md`).
- **Constraint 2 (CPU-Only)**: FR-006 and the Technical Context explicitly forbid GPU/CUDA operations, ensuring compatibility with free-tier CI.
- **Constraint 3 (Robustness)**: The plan includes retry mechanisms (FR-003), submodule checks (FR-005), and empty dataset detection (Edge Cases).
- **Constraint 4 (Validation)**: Artifact verification (FR-002) and schema validation (SC-001) are core components.
- **Constraint 5 (Transparency)**: Discrepancies and "Blocked" statuses are explicitly flagged in the report (US-3).

## Project Structure

### Documentation (this feature)

```text
specs/780-openthoughts-agent-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── generate_and_run_sbatch.py  # Main entry point (from submodule)
│   ├── bespoke/
│   │   └── verify.py               # Schema validation logic (Implementation of contracts)
│   └── generated/                  # Output directory for artifacts
├── results/
│   └── reproduction_report.md      # Final deliverable
├── tests/
│   ├── unit/
│   │   └── test_schema_validation.py
│   └── integration/
│       └── test_pipeline_execution.py
└── lib/
    └── api_client.py               # Retry logic wrapper
```

**Structure Decision**: Single project structure with distinct `data/`, `results/`, and `tests/` directories. The `data/` directory mirrors the submodule structure to facilitate direct execution of `generate_and_run_sbatch.py`. The `lib/` directory isolates API client logic for maintainability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The plan adheres to the single-project structure and avoids unnecessary complexity. | N/A |

## Implementation Phases

### Phase 0: Research & Feasibility (Pre-Implementation)
- **Goal**: Confirm dataset availability and API constraints.
- **Steps**:
  1. Verify access to `OpenThoughts-Agent` submodule and required API keys (FR-001, FR-005).
  2. Analyze the paper's claims regarding data volume and task diversity to establish baselines for the report (SC-003, SC-004).
  3. Confirm CPU-only feasibility of the data generation script (FR-006).
  4. **Critical Decision**: Acknowledge that real data generation is blocked; define the scope as "Pipeline Robustness Validation" using mocks.
- **Output**: `research.md` with dataset strategy, feasibility assessment, and explicit "Blocked" flags for real-data comparisons.

### Phase 1: Design & Contract Definition
- **Goal**: Define data schemas and validation rules.
- **Steps**:
  1. Define the `TaskTrajectory` schema (JSON/Parquet) in `data-model.md` and `contracts/` based on spec requirements (FR-002).
  2. Define the `DatasetManifest` schema for tracking generated files.
  3. Create `contracts/` YAML files for schema validation.
- **Output**: `data-model.md`, `contracts/*.schema.yaml`.

### Phase 2: Implementation (Core Logic)
- **Goal**: Implement the pipeline execution and validation logic.
- **Steps**:
  1. Implement `api_client.py` with exponential backoff (max retries, 5s initial) (FR-003).
  2. Implement submodule check logic (FR-005).
  3. Implement `verify.py` to enforce the schema defined in `contracts/` (FR-002, Edge Cases).
  4. Implement `reproduction_report.md` generation logic (FR-004).
- **Output**: Functional Python scripts in `src/data/` and `src/lib/`.

### Phase 3: Testing & Validation
- **Goal**: Ensure robustness and correctness.
- **Steps**:
  1. Execute `generate_and_run_sbatch.py` with `--task-limit` (default value for testing) (FR-001).
  2. Run schema validation on generated artifacts (FR-002).
  3. Verify report generation and "Blocked" flagging for paper comparisons (US-3).
  4. Simulate API failures and missing submodules to test error handling (Edge Cases).
- **Output**: `tests/` passing, `results/reproduction_report.md` generated.

### Phase 4: Documentation & Delivery
- **Goal**: Finalize deliverables.
- **Steps**:
  1. Compile `reproduction_report.md` with execution status, artifact counts, and explicit "Blocked" notes for data comparisons.
  2. Update `quickstart.md` with run instructions.
  3. Review against SC-001 to SC-004.
- **Output**: `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `results/reproduction_report.md`.

## Success Metrics

- **SC-001**: All generated task trajectories (mocked or real) pass schema validation. (measured by `verify.py`).
- **SC-002**: Number of generated files equals `--task-limit` (measured by file count).
- **SC-003**: Pipeline Execution Time (local logic + mock latency) < 10 minutes for 10 tasks on CPU (measured by `time` command). *Note: This metric validates system performance, not the paper's reported network latency.*
- **SC-004**: `reproduction_report.md` exists, contains non-empty content, and explicitly flags "Blocked" status for any comparison requiring real API access (measured by file existence and content check).
