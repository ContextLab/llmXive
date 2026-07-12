# Implementation Plan: State-Guided Curriculum for MobileGym

**Branch**: `001-state-guided-curriculum` | **Date**: 2026-07-12 | **Spec**: `specs/001-state-guided-curriculum/spec.md`
**Input**: Feature specification from `/specs/001-state-guided-curriculum/spec.md`

## Summary

This feature implements a **State-Guided Curriculum** for training mobile GUI agents within the MobileGym simulation environment. The core innovation is a dynamic scheduler that selects training tasks based on real-time **State Coverage Vectors** (binary flags for high-impact UI variables like `dark_mode` or `unread_count`) and estimated difficulty (targeting the 30-70% success rate "sweet spot"). The system runs two parallel training modes—**Static Random** (baseline) and **State-Guided** (experimental)—using the identical Qwen2-VL-2B model (CPU-optimized), to compare convergence speed and Sim-to-Real transfer robustness. The implementation must adhere to strict CPU-only constraints (limited cores, limited RAM, a fixed time limit). and validate the methodological soundness of the state proxies via sensitivity analysis using **Point-Biserial Correlation** on **Task-Intrinsic Complexity**.

## Technical Context

**Language/Version**: Python 3.x
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `mobilegym` (pinned to specific git commit hash), `pandas`, `scikit-learn`, `pyyaml`, `pytest`
**Storage**: Local filesystem (`data/` for logs, `code/` for scripts), JSON/Parquet for state vectors and training logs.
**Testing**: `pytest` (unit tests for scheduler logic, integration tests for coverage instrumentation).
**Target Platform**: GitHub Actions Free Tier (Linux, multiple vCPUs, 7GB RAM, no GPU).
**Project Type**: Research Simulation / Training Pipeline
**Performance Goals**: Complete two training runs (baseline + experimental) + analysis within 6 hours; Scheduler latency < 10% of batch execution time.
**Constraints**: No GPU/CUDA; memory usage < 7GB; disk usage < 14GB; no manual intervention during runs.
**Scale/Scope**: A set of training tasks and 256 test tasks (MobileGym subset); ~ tasks for sensitivity validation; [deferred]-rollout steps per agent (sampled to fit time budget).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

**Dependency Pinning Strategy**: The `mobilegym` dependency is pinned in `requirements.txt` to a specific git commit hash (e.g., `git+<COMMIT_HASH>`). The resolved hash is recorded in `data/raw/.checksums.txt` immediately upon acquisition to satisfy Constitution Principle I (Reproducibility) and Principle III (Data Hygiene).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|:--- |:--- |:--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`; MobileGym source/tasks checksummed upon download (git commit hash recorded); `requirements.txt` pins all deps. |
| **II. Verified Accuracy** | **Compliant** | Citations in `research.md` and `paper/` validated against primary sources; Title overlap ≥ 0.7 enforced. |
| **III. Data Hygiene** | **Compliant** | Raw data (MobileGym tasks) preserved; derivations (coverage vectors) written to new files with checksums in `state/...yaml`. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats in paper trace to `data/` logs; no hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Content hashes for artifacts; `updated_at` timestamp updated on artifact changes. |
| **VI. Dynamic Curriculum Traceability** | **Compliant** | **Implemented via `code/scheduler/curriculum_scheduler.py`** which logs specific coverage metrics (e.g., `dark_mode` transition) triggering each batch selection to **`data/processed/scheduler_trace.json`**. The `metrics_triggered` field in the schema explicitly captures the state metrics that triggered the selection, ensuring the dynamic prioritization strategy can be audited. |
| **VII. Sim-to-Real Transfer Variance Control** | **Compliant** | **Implemented via `code/analysis/transfer.py`** which explicitly reports the variance of success rates across high state-dependency apps (metric **SC-002**), not just mean performance. |

## Project Structure

### Documentation (this feature)

```text
specs/001-state-guided-curriculum/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
└── contracts/ # Phase 1 output (AUTHORITATIVE SCHEMAS)
 ├── dataset.schema.yaml
 └── coverage.schema.yaml
```

> **Note on Authority**: The `contracts/` directory contains the **authoritative schema definitions**. The `code/scheduler/` and `code/training/` modules MUST validate their inputs/outputs against these schemas to enforce the Single Source of Truth principle. The `metrics_triggered` field in `coverage.schema.yaml` is the canonical source for Principle VI traceability.

### Source Code (repository root)

```text
projects/PROJ-858-llmxive-follow-up-extending-mobilegym-a/
├── code/
│ ├── __init__.py
│ ├── scheduler/
│ │ ├── __init__.py
│ │ ├── state_coverage.py # Implements FR-001, US-002
│ │ └── curriculum_scheduler.py # Implements FR-002, US-001 (Logs to scheduler_trace.json)
│ ├── training/
│ │ ├── __init__.py
│ │ ├── runner.py # Orchestrates Static vs. State-Guided runs
│ │ └── model_config.py # Qwen2-VL-2B config (CPU-optimized)
│ ├── analysis/
│ │ ├── __init__.py
│ │ ├── convergence.py # Implements FR-006, SC-001
│ │ ├── transfer.py # Implements FR-007, SC-002, US-003 (Reports Variance)
│ │ └── sensitivity.py # Implements FR-008, SC-006, US-004 (Point-Biserial/Logistic)
│ └── utils/
│ ├── constants.py # Time limits, thresholds
│ └── logging.py
├── data/
│ ├── raw/ # MobileGym tasks (checksummed)
│ ├── processed/ # Coverage vectors, training logs
│ └── validation/ # Held-out test sets
├── tests/
│ ├── contract/
│ ├── integration/
│ └── unit/
│ └── test_scheduler.py # Tests for US-001
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Single project structure under `code/` is selected to minimize overhead and simplify the CPU-only execution pipeline. The separation into `scheduler`, `training`, and `analysis` modules ensures modularity for independent testing (US-001, US-002, US-003, US-004) while maintaining a unified entry point for the 6-hour run.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **Dynamic Scheduler Logic** | Required to implement the core "State-Guided" hypothesis (US-001). | Random sampling (Static Baseline) cannot test the research question regarding curriculum efficiency. |
| **Two-Phase Selection (Low Coverage + Sweet Spot)** | Necessary to balance exploration (novelty) and exploitation (difficulty) as per FR-002. | Single-phase (e.g., only difficulty) risks ignoring unexplored state space, violating the "State-Guided" premise. |
| **Sensitivity Analysis Module** | Required to validate the proxy assumption (US-004, FR-008). | Skipping validation risks optimizing for trivial state transitions, invalidating the "convergence" claim. |