# Implementation Plan: Reproduce & Validate ResearchClawBench

**Branch**: `001-reproduce-researchclawbench` | **Date**: 2026-06-30 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This feature implements a reproduction and validation pipeline for the **ResearchClawBench** benchmark. The primary requirement is to execute the vendored `ResearchClawBench` codebase end-to-end on a free-tier CPU CI runner. The technical approach involves:
1.  **Environment Setup**: Installing vendored dependencies and configuring a `mock` agent to avoid GPU/external API dependencies.
2.  **Execution Engine**: Running the `rcb-eval` CLI on a single representative task (e.g., `Astronomy_000`) to verify pipeline integrity (FR-001, FR-003).
3.  **Scoring Validation**: Parsing `checklist.json` rubrics and verifying score calculation logic against **Synthetic Ground Truth** artifacts (FR-002, SC-002). This includes "Golden Test Cases" (perfect output) and "Negative Test Cases" (deliberately missing elements) to validate the *content inspection* logic, not just arithmetic.
4.  **Aggregation**: Implementing a script to aggregate scores across multiple runs to compute mean/std dev (FR-005, SC-003).
5.  **Robustness**: Ensuring graceful failure on missing data (FR-003, SC-004) and implementing **unconditional** retry logic for transient network errors in the wrapper layer (FR-006).

**Scope Clarification**: This feature validates the *mechanical correctness* of the benchmark engine (does it parse rubrics correctly? does it calculate scores as defined?). It does *not* validate the *scientific validity* or *discriminative power* of the benchmark (i.e., whether the rubric correlates with human expert judgment), as that requires running real agents and human evaluation, which is outside the scope of a reproduction pipeline.

## Technical Context

**Language/Version**: Python 3.11 (required by ResearchClawBench vendored code).  
**Primary Dependencies**: `researchclawbench` (vendored), `pytest`, `pyyaml`, `requests` (for retry logic), `jsonschema`.  
**Storage**: Local filesystem (tasks in `tasks/`, results in `results/`). No external database.  
**Testing**: `pytest` (unit tests for scoring logic, integration tests for CLI execution).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM).  
**Project Type**: CLI tool / Validation Pipeline.  
**Performance Goals**: Single task run < 30 minutes (SC-005); Memory < 4 GB.  
**Constraints**: No GPU; No external LLM API calls for validation (use `mock` agent); No new dataset requirements.  
**Scale/Scope**: 1 representative task (`Astronomy_000`) for smoke test; 2 agents for aggregation test.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This section maps the implementation to the project's governing principles (SSoT, No Silent Fallbacks, etc.) as defined in the project's constitutional framework.

1.  **Principle I: Single Source of Truth (SSoT)**
    *   **Requirement**: All data and logic must be derived from the verified `spec.md` and vendored `ResearchClawBench` code.
    *   **Implementation**: The plan uses *only* the vendored `tasks/` directory for data. No external datasets are introduced. The `mock` agent configuration is defined locally in `src/config/` as a single source for the test environment.
    *   **Verification**: Phase 0 verifies the existence of `tasks/Astronomy_000` and `checklist.json` before execution.

2.  **Principle II: No Silent Fallbacks**
    *   **Requirement**: The system must not silently proceed with incomplete data or default to incorrect values.
    *   **Implementation**: The plan mandates strict validation in `rubric_checker.py` (fail if weights != 100) and `task_info` validation (fail if data files missing).
    *   **Verification**: Phase 2 includes "Negative Test Cases" where missing files or malformed rubrics trigger explicit `FileNotFoundError` or `ValueError` (SC-004).

3.  **Principle III: Real-Call Testing**
    *   **Requirement**: The system must handle real-world conditions (network errors, API limits) even if the primary test uses a mock.
    *   **Implementation**: The `rcb_runner.py` wrapper implements retry logic with exponential backoff (FR-006) for *all* network calls, regardless of whether the agent is `mock` or `real`. This ensures the infrastructure is robust.
    *   **Verification**: Phase 2 includes a unit test that simulates a network timeout to verify the retry mechanism triggers correctly.

4.  **Principle IV: Compute Feasibility**
    *   **Requirement**: The plan must be runnable on the target CI environment (2 CPU, 7 GB RAM).
    *   **Implementation**: The plan explicitly avoids GPU/CUDA. It relies on a `mock` agent and sampled data.
    *   **Verification**: Phase 0 confirms memory usage of the mock agent is < 1 GB.

5.  **Principle V: Methodological Rigor**
    *   **Requirement**: Validation must test the *logic* of the system, not just its existence.
    *   **Implementation**: The plan uses "Synthetic Ground Truth" (Golden and Negative test cases) to verify that the scoring engine correctly *interprets* rubric criteria (e.g., detecting a missing figure), not just that it sums numbers.
    *   **Verification**: Phase 2 validates that a "Negative Test Case" (missing figure) results in a score deduction equal to the rubric weight.

## Project Structure

### Documentation (this feature)

```text
specs/001-reproduce-researchclawbench-a-benchmark-for-end-to/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── ResearchClawBench/   # Vendored submodule

src/
├── cli/
│   └── rcb_runner.py    # Wrapper for rcb-eval with retry logic
├── validation/
│   ├── rubric_checker.py # Validates checklist.json weights
│   ├── scorer.py         # Logic to apply rubric to output (content-aware)
│   ├── aggregator.py     # Computes mean/std across runs
│   └── synthetic_generator.py # Creates Golden/Negative test artifacts
├── tests/
│   ├── test_rubric.py    # Unit tests for scoring logic
│   ├── test_aggregator.py# Unit tests for aggregation
│   └── test_integration.py# Integration test for single task run
└── config/
    └── mock_agent.yaml   # Configuration for the mock agent

tests/
├── contract/             # Contract tests against schema
└── integration/          # End-to-end CLI tests
```

**Structure Decision**: A single `src/` directory is selected. The `external/` directory holds the vendored code. The `src/validation/` directory isolates the custom logic required to verify the benchmark (scoring, aggregation, synthetic generation) without modifying the vendored code. This separation ensures the validation layer can be updated independently if the benchmark format changes.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. | N/A |

## Plan Phases

### Phase 0: Research & Environment Feasibility
*   **Goal**: Confirm the vendored `ResearchClawBench` code is present and the `mock` agent configuration is feasible.
*   **Steps**:
    1.  Inspect `external/ResearchClawBench` for `rcb-eval` CLI entry point.
    2.  Verify existence of `tasks/Astronomy_000` (or equivalent) and `checklist.json`.
    3.  Identify the `mock` agent implementation or create a stub that returns deterministic output.
    4.  **FR-003 / SC-004**: Confirm the code raises `FileNotFoundError` for missing data files.
*   **Deliverables**: `research.md` (Dataset Strategy, Feasibility Report).

### Phase 1: Data Model & Contracts
*   **Goal**: Define the schema for inputs (`checklist.json`, `task_info.json`) and outputs (`score.json`, `summary.json`).
*   **Steps**:
    1.  Extract schema from `tasks/<ID>/target_study/checklist.json`.
    2.  Extract schema from expected `results/<ID>_score.json`.
    3.  Create YAML contracts in `contracts/`.
    4.  **FR-002 / SC-002**: Define the logic for weight validation (sum == 100).
*   **Deliverables**: `data-model.md`, `contracts/*.schema.yaml`, `quickstart.md`.

### Phase 2: Implementation (Mocked & Synthetic)
*   **Goal**: Implement the validation scripts (scoring, aggregation) and the CLI wrapper.
*   **Steps**:
    1.  Implement `rubric_checker.py` to parse and validate weights.
    2.  Implement `scorer.py` to apply weights to **synthetic outputs** (Golden and Negative cases).
    3.  Implement `aggregator.py` to compute mean/std.
    4.  Create `mock_agent.yaml` and wrapper script.
    5.  **FR-006**: Implement retry logic in `rcb_runner.py` (wrapper level, unconditional).
    6.  **Construct Validity**: Create `synthetic_generator.py` to produce:
        *   *Golden Case*: Output containing all required artifacts (figures, text) as per rubric.
        *   *Negative Case*: Output missing a specific artifact (e.g., a figure) to test deduction logic.
*   **Deliverables**: Source code in `src/validation/` and `src/cli/`.

### Phase 3: Integration & Validation
*   **Goal**: Run the full pipeline on `Astronomy_000`.
*   **Steps**:
    1.  Execute `rcb-eval --task Astronomy_000 --agent mock`.
    2.  Verify `results/Astronomy_000_score.json` exists and matches schema.
    3.  Run aggregation script on two mock runs.
    4.  Verify `summary.json` contains correct mean.
    5.  **SC-005**: Measure execution time (must be < 30 mins).
 6. **Validation**: Run `synthetic_generator.py` to create test cases and verify `scorer.py` correctly scores the Golden case ([deferred]) and the Negative case (deducted score).
*   **Deliverables**: `tasks.md`, Final Report.