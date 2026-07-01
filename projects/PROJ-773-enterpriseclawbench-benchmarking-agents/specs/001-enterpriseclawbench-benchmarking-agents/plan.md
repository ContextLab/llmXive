# Implementation Plan: EnterpriseClawBench Reproduction & Validation

**Branch**: `001-enterpriseclawbench-reproduction` | **Date**: 2026-06-15 | **Spec**: `specs/001-enterpriseclawbench-reproduction/spec.md`
**Input**: Feature specification from `/specs/001-enterpriseclawbench-reproduction/spec.md`

## Summary

This feature implements the reproduction and validation pipeline for the **EnterpriseClawBench** benchmark. The approach involves executing the vendored `EnterpriseClawBench` git submodule construction and evaluation pipelines against a minimal "smoke test" dataset to verify code integrity, then scaling to a sampled dataset to reproduce key *structural trends*. The plan strictly adheres to the GitHub Actions free-tier constraints (CPU-only, limited RAM) by limiting data volume and avoiding GPU-dependent operations. The core logic relies on Python 3.10+ scripts provided in the submodule, orchestrated via a wrapper CLI.

**Critical Methodological Note**: Due to the unavailability of the full 852-task dataset in the verified sources, this plan **does not** attempt to reproduce absolute population statistics (e.g., exact task counts). Instead, it validates the **structural integrity** of the pipeline and the **relative distribution trends** of role classes within the available sample.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `EnterpriseClawBench` (vendored submodule), `pyyaml`, `pytest`, `pandas`, `jsonschema`  
**Storage**: Local filesystem (input: `raw_session_example`, output: `output/smoke/tasks/`, `output/reports/`)  
**Testing**: `pytest` (unit/integration), contract tests against `contracts/` schemas  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: CLI / Data Processing Pipeline  
**Performance Goals**: Pipeline must complete smoke test in < 10 mins; full sample evaluation < 6 hours.  
**Constraints**: No GPU; RAM < 7GB; Disk < 14GB; Must handle LLM timeouts (FR-007) without blocking.  
**Scale/Scope**: Smoke test (-5 sessions); Sample validation (subset of available `example_runs`, N < 10).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file:*

1.  **Reproducibility**: The plan explicitly uses the vendored submodule code without modification, ensuring the "code integrity" assumption is tested.
2.  **Compute Feasibility**: The plan restricts execution to the `smoke.yaml` config and a sampled subset, avoiding the full 852-task load on the free-tier runner.
3.  **Data Integrity**: The plan includes a validation step (SC-002) to verify the 5 required fields in generated tasks before proceeding to evaluation.
4.  **Error Handling**: The plan mandates logging and graceful degradation for malformed inputs (FR-001, FR-007) rather than crashing.

## Project Structure

### Documentation (this feature)

```text
specs/001-enterpriseclawbench-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── task.schema.yaml
│   └── report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/EnterpriseClawBench/   # Vendored submodule (read-only execution)
├── construction/
│   ├── cli.py
│   └── configs/
└── evaluation/
    ├── cli.py
    └── rules.py

src/
├── runners/
│   ├── smoke_runner.py         # Orchestrates construction smoke test
│   └── eval_runner.py          # Orchestrates evaluation on sample
├── validators/
│   ├── task_validator.py       # Validates SC-002 fields
│   └── report_validator.py     # Validates SC-003 structure
└── utils/
    └── retry_utils.py          # Implements FR-007 exponential backoff

tests/
├── contract/
│   ├── test_task_schema.py
│   └── test_report_schema.py
├── integration/
│   └── test_smoke_pipeline.py
└── unit/
    └── test_retry_utils.py
```

**Structure Decision**: The `src/` directory contains the orchestration and validation logic, while the `external/` directory remains untouched as the source of truth for the benchmark logic. This separation ensures the reproduction can be updated if the submodule changes, without modifying the core benchmark code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is limited to a smoke test and sample validation. | N/A |

## Phase Breakdown

### Phase 0: Environment & Data Verification
- **Goal**: Verify submodule integrity and dataset availability.
- **Steps**:
  1.  Clone/Update `external/EnterpriseClawBench` submodule.
  2.  Install dependencies (`pip install -r external/EnterpriseClawBench/requirements.txt`).
  3.  Verify existence of `raw_session_example` and `example_runs` directories.
  4.  **FR-002**: Validate `smoke.yaml` configuration syntax.

### Phase 1: Construction Pipeline Execution (Smoke Test)
- **Goal**: Execute construction pipeline on minimal data (US-1).
- **Steps**:
  1.  Run `python -m construction.enterprise_clawbench_construction.cli --config construction/configs/smoke.yaml`.
  2.  **FR-003**: Validate output `task.json` files against the full `task.schema.yaml` (including optional `metadata` fields), ensuring the 5 core required fields (`prompt`, `role_class`, `skill_subclass`, `hard_rules`, `semantic_rubric`) are present.
  3.  **FR-001**: Ensure exit code 0 and no runtime errors.
  4.  **Edge Case**: Inject a malformed input file to verify graceful error logging (US-1, Edge Cases).

### Phase 2: Evaluation Protocol Validation
- **Goal**: Validate judge logic and scoring (US-2).
- **Steps**:
  1.  Load pre-generated artifacts from `example_runs`.
  2.  **Determinism Controls**: 
      - Configure the Judge LLM with `temperature=0` and a fixed `seed` (if supported by the provider).
      - **Fallback**: If the provider does not support deterministic seeds, the plan defaults to a **rule-based scoring mode** for the smoke test to satisfy SC-003.
  3.  Run evaluation CLI with default judge config.
  4.  **FR-004**: Verify `report.json` contains `artifact_delivery`, `visual_quality`, `cost`, `runtime`, `skill_transfer`.
  5.  **FR-005**: Run evaluation twice; compare outputs for determinism (SC-003).
      - *Note*: SC-003 applies strictly to runs where `status` is `completed` AND deterministic controls (or rule-based mode) are active. If `status` is `unscorable` (due to timeout), the determinism check applies to the `status` field itself, not the score value.
  6.  **FR-007**: Simulate LLM timeout; verify retry logic (multiple attempts) and `unscorable` marking.

### Phase 3: Statistical Reproduction (Sampled)
- **Goal**: Aggregate results and compare to paper metrics (US-3).
- **Statistical Limitation**: The available sample (N < 10) is insufficient to validate absolute population counts (852 tasks) with < 5% variance. This phase validates **structural trends** and **relative proportions** only.
- **Steps**:
  1.  Aggregate task counts from Phase 1 output.
  2.  **FR-006**: Generate role class distribution histogram.
  3.  **SC-004 (Revised)**: Compare the *relative proportions* of role classes in the sample against the *relative proportions* reported in the paper. The goal is to verify that the dominant role classes (e.g., "Analyst", "Developer") appear in the same order of magnitude, acknowledging that absolute counts will differ.
  4.  **SC-005**: Log error handling robustness metrics.

## Risk Mitigation

- **Risk**: Full dataset (852 tasks) exceeds RAM/Disk.
  - **Mitigation**: Strictly use `smoke.yaml` and `example_runs` for CI. If full reproduction is needed, it will be a separate, larger run (not in this feature).
- **Risk**: External LLM API unavailability.
  - **Mitigation**: FR-007 retry logic; CI job marked as `unstable` if >5% tasks are `unscorable` due to API, not code failure.
- **Risk**: Submodule version mismatch.
  - **Mitigation**: Pin submodule commit hash in `.gitmodules`.
- **Risk**: Statistical invalidity of sample comparison.
  - **Mitigation**: Explicitly reframe success criteria in Phase 3 to "structural trend alignment" rather than "absolute count variance". Document this limitation in the final report.
- **Risk**: Non-deterministic LLM output invalidating SC-003.
  - **Mitigation**: Enforce `temperature=0` and `seed` in Phase 2. If unsupported, fallback to rule-based scoring to ensure deterministic validation is possible.