# Implementation Plan: $π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows

**Branch**: `001-bench-evaluating-proactive-personal-assi` | **Date**: 2026-05-27 | **Spec**: `specs/001-bench-evaluating-proactive-personal-assi/spec.md`
**Input**: Feature specification from `specs/001-bench-evaluating-proactive-personal-assi/spec.md`

## Summary

This project implements a CPU-tractable reproduction pipeline for the "$π$-Bench" evaluation framework. The primary requirement is to execute the vendored `Pi-Bench` codebase on a standard GitHub Actions free-tier runner (A limited number of CPUs, 7GB RAM) without GPU dependencies. The technical approach involves wrapping the existing `main.py` entry point, configuring mock environments for 5 personas (Financier, Law Trainee, Marketer, Pharmacist, and one additional), and instrumenting the evaluation loop to compute specific metrics: `task_completion_rate` and a revised **Sequence Novelty Index (SNI)** to distinguish planning from complex retrieval (addressing the Turing-simulated reviewer's concern). The plan strictly adheres to the "fit the box" constraint by sampling tasks if necessary and enforcing CPU-only execution for all LLM backends.

## Technical Context

**Language/Version**: Python 3
**Primary Dependencies**: `torch` (CPU-only wheel), `scikit-learn`, `datasets`, `pyyaml`, `pytest`, `scipy` (for bootstrapping)
**Storage**: Local filesystem (`results/`, `external/Pi-Bench/`)
**Testing**: `pytest` (contract tests on JSON output schemas, integration tests on runner execution)
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Research benchmark / CLI evaluation tool
**Performance Goals**: Total runtime ≤ 6 hours for 100 tasks; Peak memory ≤ 7GB
**Constraints**: NO GPU/CUDA, NO 8-bit/4-bit quantization, NO deep-net training from scratch.
**Scale/Scope**: Multiple Personas

The research question is to understand how different user archetypes influence system adoption. The method involves developing a set of representative personas based on qualitative interview data. This approach aligns with guidelines for user-centered design ()., A moderate number of tasks each (a substantial number of tasks), Multiple distinct LLM backends.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: No `constitution.md` file was supplied in the project inputs. The following check is marked **PENDING** and will be performed once the Single Source of Truth (SSoT) document is provided.

| Principle | Status | Notes |
|:--- |:--- |:--- |
| **Principle I: SSoT** | **PENDING** | Constitution not provided. Will verify alignment once available. |
| **Principle V: Real-Call Testing** | **PENDING** | Constitution not provided. Will verify alignment once available. |
| **Reproducibility** | **PASS** | Plan mandates exact reproduction of `Pi-Bench` codebase and metrics. |
| **Compute Feasibility** | **PASS** | Explicitly targets CPU-only, sampled data, and 6-hour CI limits. No GPU dependencies. |
| **Methodological Rigor** | **PASS** | Addresses the "retrieval vs. planning" critique via Sequence Novelty Index (SNI) and bootstrapping. |
| **Data Integrity** | **PASS** | Mock environment ensures deterministic inputs; errors logged and excluded from metrics. |
| **No Unspecified Constraints** | **PASS** | All constraints (CPU, RAM, Time) are derived from the "fit the box" requirement in the spec and platform limits, not invented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-bench-evaluating-proactive-personal-assi/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── runners/
│ ├── __init__.py
│ ├── cpu_runner.py # Wrapper to enforce CPU mode
│ └── evaluator.py # Metric calculation logic (SNI, completion)
├── mocks/
│ ├── __init__.py
│ └── environment.py # Simulated API responses (Gmail, Amazon, etc.)
├── config/
│ ├── personas/ # task.yaml, profile.yaml for 5 personas
│ └── models/ # Model configs (MiniMax, Claude, DeepSeek)
└── utils/
 ├── metrics.py # SNI and Proactivity calculation
 └── logger.py

tests/
├── contract/
│ ├── test_output_schema.py # Validates JSON against contracts
│ └── test_metric_logic.py # Unit tests for SNI/proactivity formulas
├── integration/
│ └── test_cpu_run.py # End-to-end CPU-only execution test
└── unit/
 └── test_mock_env.py # Mock environment determinism

external/
└── Pi-Bench/ # Vendored codebase (submodule)
```

**Structure Decision**: Selected the "Single project" structure with a `src/` layout to keep the evaluation logic (`runners`, `utils`) separate from the vendored `Pi-Bench` code. This allows us to inject the `SNI` metric and CPU-enforcement logic without modifying the upstream vendor code, ensuring clean reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **Sequence Novelty Index (SNI)** | Required to address the Turing-simulated reviewer's critique that "proactivity" might just be complex retrieval. | Relying solely on the vendor's `proactivity_score` would fail to distinguish between "planning" and "echoing" trajectories. |
| **Mock Environment Wrapper** | The spec requires handling "Environment Failure" scenarios explicitly and excluding them from metrics. | Directly using the vendor's error handling might not distinguish between "Agent Failure" and "Environment Failure" in the final report. |
| **CPU-Only Enforcement** | The "fit the box" constraint is a hard blocker for CI success. | Assuming the vendor code auto-detects CPU is risky; explicit enforcement prevents CUDA errors in CI. |
| **Bootstrapping Strategy** | Required due to low sample size (N~100) to avoid invalid parametric p-values. | Standard t-tests would be statistically unsound given the small cell sizes. |

## Phase Breakdown

### Phase 0: Research & Dataset Strategy (Current)
- **Goal**: Verify dataset availability (mock tasks) and finalize metric definitions.
- **FR-002, FR-005**: Define **Sequence Novelty Index (SNI)** formula (n-gram deviation from template library) and baseline trajectory comparison logic (minimum distance to set of valid explicit paths).
- **FR-003**: Confirm `torch` CPU wheel availability and model config syntax for CPU-only mode.
- **SC-001, SC-003**: Establish the reference values for "high-novelty" vs. "retrieval" thresholds.
- **Statistical Mitigation**: Confirm bootstrapping strategy for low-N comparisons.

### Phase 1: Design & Contracts
- **Goal**: Define data models and output schemas.
- **FR-004**: Design the JSON artifact schema (`task_id`, `model_id`, `completion_status`, `proactivity_score`, `action_trace`, `latency_ms`, `novelty_index`).
- **FR-007**: Define error logging schema for "Environment Failure" and "Ambiguous Intent".
- **SC-004, SC-005**: Define resource monitoring hooks (memory, time).
- **Deliverable**: Produce `data-model.md` and `contracts/` directory with valid YAML schemas.

### Phase 2: Implementation
- **Goal**: Build the runner and metric calculators.
- **FR-001**: Implement `src/runners/cpu_runner.py` to integrate `Pi-Bench` with the mock environment.
- **FR-002, FR-005**: Implement `src/utils/metrics.py` with SNI and Proactivity Score logic.
- **FR-003**: Wrap model loading in `src/runners/cpu_runner.py` to force `device="cpu"`.
- **FR-006**: Implement result aggregation and reporting with bootstrapping.
- **Deliverable**: Functional Python codebase ready for CI.

### Phase 3: Testing & Validation
- **Goal**: Validate against acceptance criteria.
- **US-1**: Write `tests/integration/test_cpu_run.py` to validate end-to-end execution on Financier persona.
- **US-2**: Write `tests/contract/test_output_schema.py` to verify `proactivity_score` and `novelty_index` presence in JSON.
- **US-3**: Write `tests/integration/test_model_comparison.py` to validate comparative analysis across model backends.
- **Edge Cases**: Write `tests/unit/test_mock_env.py` to trigger API simulation failures and verify graceful handling.

## Constitution Check (Post-Research)

*To be filled after Phase 0 research confirms dataset variable fit and metric definitions, and after `constitution.md` is supplied.*