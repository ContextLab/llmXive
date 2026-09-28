# Implementation Plan: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

**Branch**: `001-symbolic-dojo-extend` | **Date**: 2026-09-03 | **Spec**: `specs/001-symbolic-dojo-extend/spec.md`
**Input**: Feature specification from `/specs/001-symbolic-dojo-extend/spec.md`

## Summary

This feature implements a CPU-tractable symbolic planning layer for the RoboDojo benchmark to test the hypothesis that topological symbolic abstractions alone suffice for long-horizon robot manipulation, decoupling success from high-fidelity physics simulation. The system converts visual observations to semantic embeddings (MobileViT), maps them to discrete `SymbolicState` graphs, and executes A*/MCTS planners to generate action sequences. These sequences are evaluated against a "Perfect Low-Level Executor" (Oracle) and the real-world RoboDojo environment to measure the "Physics Fidelity Gap." The plan strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and explicit compute feasibility on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU only), `transformers` (MobileViT), `networkx` (graph planning), `pandas`, `polars`, `scipy` (Wilcoxon), `pydantic` (validation), `datasets` (HuggingFace).  
**Storage**: Local `data/` directory (Parquet files, JSON logs), `data/interim/execution_logs.parquet`.  
**Testing**: `pytest` (unit/integration), `ruff` (linting), `black` (formatting).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM, no GPU).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: <60s per task planning; <6GB RAM peak; <4h total wall-clock for 18 tasks.  
**Constraints**: No GPU acceleration for planning; strict memory limits; open-source data only.  
**Scale/Scope**: 18 RoboDojo tasks; 1 symbolic planner implementation; 1 statistical analysis module.

> **Dataset Fit Note**: The plan relies on the verified RoboDojo parquet files (OpenMOSS/RoboDojo) which contain the necessary task specifications and video frames. The "Perfect Low-Level Executor" is implemented as a deterministic, non-physics rule-based verifier (graph matcher) to serve as the Oracle control, isolating the planner's logical validity from physics fidelity.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **[X] Reproducibility**: All random seeds pinned in `code/config.py`. Dependencies pinned in `requirements.txt`. External datasets fetched via `datasets` library from verified HuggingFace URLs.
- **[X] Verified Accuracy**: Citations for MobileViT, RoboDojo, and Wilcoxon test strictly reference the provided `# Verified datasets` and authoritative sources (e.g., Wikipedia for alpha).
- **[X] Data Hygiene**: Raw data (Parquet) is read-only. Derivations (embeddings, logs) written to new files with checksums recorded in `state/`.
- **[X] Single Source of Truth**: All metrics in the final report trace to `data/interim/execution_logs.parquet` and `data/interim/compute_metrics.parquet`.
- **[X] Versioning**: Artifacts include content hashes; `state/` updated on changes.
- **[X] Simulation Fidelity Independence**: The symbolic planner operates purely on discrete graphs. Success metrics are derived *only* from execution outcomes (Oracle vs. Real), not internal planner states.
- **[X] Computational Efficiency**: Planning uses A*/MCTS on CPU. Vision encoder is frozen MobileViT (quantized if needed). No GPU dependencies for the core loop.

## Project Structure

### Documentation (this feature)

```text
specs/001-symbolic-dojo-extend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Seeds, paths, hyperparameters
├── main.py              # CLI entry point
├── models/
│   ├── __init__.py
│   ├── semantic_encoder.py  # MobileViT wrapper (CPU)
│   └── symbolic_state.py    # PDDL-like graph representation
├── services/
│   ├── __init__.py
│   ├── planner.py           # A* / MCTS logic
│   ├── executor_oracle.py   # "Perfect" low-level executor (Rule-based)
│   ├── executor_real.py     # Real-world adapter (Sim-to-Real)
│   └── failure_detector.py  # Logic for T024/T026 (Planner vs. Controller)
├── analysis/
│   ├── __init__.py
│   ├── stats.py             # Wilcoxon test, metrics, ablation
│   └── report.py            # Report generation
├── utils/
│   ├── logging.py           # Structured logging to Parquet
│   └── io.py                # Data loading/saving
├── tests/
│   ├── test_planner.py
│   ├── test_failure_detector.py
│   └── test_stats.py
├── requirements.txt
├── pyproject.toml           # Linting/Formatting config (T002)
├── .ruff.toml               # Linting config (T002)
└── .black.toml              # Formatting config (T002)
```

**Structure Decision**: Single project structure selected. The separation of `services/` (planning vs. execution) and `analysis/` (stats) ensures modularity and supports the ablation study (FR-008) and Oracle control (FR-010) without code duplication.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Oracle Executor** | Required by FR-010 to isolate "Physics Fidelity Gap". | A simple "always success" flag is insufficient; we need to verify the *planner's* logical validity against a ground-truth task graph, not just a binary toggle. |
| **Failure Detector** | Required by T024/T026 to distinguish Planner vs. Controller failure. | **BLOCKER**: Logging only "Success/Fail" is insufficient for the ablation study (US-2). We need step-level granularity to identify where the symbolic abstraction breaks vs. where the controller breaks. **Status: Unimplemented.** |
| **Parquet Logging** | Required for Data Hygiene (Constitution III) and performance. | CSV is too slow for large logs and lacks schema enforcement. Parquet allows efficient streaming and type safety. |
| **Ablation Logic** | Required by FR-008 to test state representation levels. | A single graph type cannot test the hypothesis that "topology suffices" vs. "affordances matter". We need to vary the graph complexity. |
| **Sim-to-Real Adapter** | Required by FR-009 to bridge the domain gap. | Using raw weights without adaptation leads to high failure rates, confounding the planner's performance with the controller's inability to adapt. |

## Resolved Unresolved Panel Concerns

*Note: The following concerns were previously flagged as "unresolved" or "incomplete". This plan explicitly addresses them by defining the implementation tasks and correcting the status.*

- **[ ] T005a-d (Schemas)**: **Status: Pending Implementation**. These schemas are the primary deliverable of **Phase 1**. The plan defines the exact schemas to be created in `contracts/` and `data-model.md`.
- **[ ] T002 (Linting/Formatting)**: **Status: Pending Implementation**. `pyproject.toml` and `.ruff.toml` are defined in the project structure and will be created in **Phase 2**.
- **[ ] T024/T026 (Execution Logs)**: **Status: Pending Implementation**. The `services/failure_detector.py` and `utils/logging.py` are explicitly designed to detect failure modes (Planner vs. Controller) and write to `data/interim/execution_logs.parquet`. Implementation is scheduled for **Phase 2**.

## Phase Plan

### Phase 0: Research & Data Strategy
- Verify RoboDojo dataset accessibility (OpenMOSS/RoboDojo).
- Confirm MobileViT CPU inference speed on 2-core runner.
- Define the "Perfect Low-Level Executor" (Oracle) as a **deterministic rule-based graph matcher** (non-physics).
- **Power Analysis**: Calculate sample size justification for N=18 tasks. Acknowledge risk of Type II error and define effect size detection threshold.

### Phase 1: Data Model & Contracts
- Define `SymbolicState`, `ExecutionOutcome`, `ActionSequence`, `ComputeMetric`, and `AblationResult` schemas.
- Create `contracts/*.schema.yaml` files (T005a-d).
- Implement `data-model.py` for validation.

### Phase 2: Core Implementation
- **T002**: Create `pyproject.toml`, `.ruff.toml`, `.black.toml` (Linting/Formatting config).
- Implement `semantic_encoder.py` (MobileViT) with **Mapping Validation** step to measure encoder-to-state accuracy.
- Implement `planner.py` (A*/MCTS).
- Implement `failure_detector.py` (T024 logic) to distinguish Planner vs. Controller failures.
- Implement `executor_oracle.py` (Rule-based graph matcher) and `executor_real.py`.
- **T024/T026**: Implement `utils/logging.py` to write `data/interim/execution_logs.parquet`.
- **FR-009**: Implement `Sim-to-Real Adapter` (Fine-tuning Protocol) using real-world videos.
- **FR-008**: Implement `Ablation Study` logic to vary state representation levels (Full vs. Simplified graph).

### Phase 3: Analysis & Reporting
- Implement `stats.py` (Wilcoxon test, metrics, **Catastrophic Failure Rate** calculation for SC-005).
- Implement `report.py` (Generate final metrics).
- Run full pipeline on a representative set of tasks.
- Generate ablation results for `data/interim/ablation_results.parquet`.

### Phase 4: Validation & Cleanup
- Verify checksums and data hygiene.
- Run `pytest` and `ruff`.
- Generate final `paper/` artifacts.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Ambiguous Embeddings** | Planner cannot map to unique state. | Implement "Mapping Validation" metric; if >5% ambiguous, report as "Encoder Ambiguity" (confound) rather than Planner Infeasibility. |
| **Real-World Failure Rate** | High failure rate obscures planner performance. | Use the Oracle Executor to separate planner failure from controller failure (FR-010). |
| **Compute Time** | >6 hours for 18 tasks. | Parallelize task execution (if runner allows) or reduce task count to 10 for initial validation. |
| **Data Access** | HuggingFace rate limits. | Use `datasets` library with caching and retries. |
| **Statistical Power** | N=18 may be insufficient to detect small effects. | Acknowledge limitation in report; focus on effect size estimation rather than strict significance. |