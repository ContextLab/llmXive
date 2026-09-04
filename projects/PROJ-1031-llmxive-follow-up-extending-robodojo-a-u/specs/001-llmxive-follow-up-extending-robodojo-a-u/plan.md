# Implementation Plan: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

**Branch**: `001-symbolic-dojo-extend` | **Date**: 2026-09-03 | **Spec**: `specs/001-symbolic-dojo-extend/spec.md`
**Input**: Feature specification from `/specs/001-symbolic-dojo-extend/spec.md`

## Summary

This project investigates whether high-fidelity continuous physics simulation is strictly necessary for long-horizon robot manipulation planning. The technical approach implements a "Symbolic-Dojo" adapter that strips continuous dynamics (friction, mass) from RoboDojo visual observations, mapping them to a discrete `SymbolicState` graph. A CPU-tractable planner (A*/MCTS) generates action sequences of discrete sub-goals. These sequences are executed via an adapted low-level controller (using pre-trained RoboDojo weights) in the real-world environment. Success is measured by task completion rates against the baseline, computational overhead reduction, and a "Physics Fidelity Gap" analysis (diagnostic only) using a simulated oracle control.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `scikit-learn`, `networkx`, `pandas`, `datasets`, `opencv-python`, `pyyaml`  
**Storage**: Local filesystem (`data/` for raw/processed data, `data/interim/` for embeddings), JSON logs for execution metrics.  
**Testing**: `pytest` (unit tests for state mapping, integration tests for planner logic, contract tests for schema validation).  
**Target Platform**: GitHub Actions Free Tier (Linux, multiple CPU cores, ~7 GB RAM, ~ GB disk).  
**Project Type**: Research Pipeline / Benchmarking Suite  
**Performance Goals**: Planner execution ≤ 60s per task; Total memory ≤ 6 GB; No GPU dependency for the symbolic layer.  
**Constraints**: Must run entirely on CPU for the planning phase; Real-world execution data is the ground truth (no synthetic data generation for final metrics).  
**Scale/Scope**: RoboDojo real-world tasks (subset of available video data).  
**Dataset Version**: RoboDojo-Benchmark/RoboDojo (Commit: `v.1` - Verified for 18-task subset).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All code in `code/` with pinned `requirements.txt`. Random seeds fixed. Data fetched from verified HF URLs with commit pin. |
| **II. Verified Accuracy** | **PASS** | Citations (RoboDojo paper, MobileViT) will be validated against primary sources before report generation. |
| **III. Data Hygiene** | **PASS** | Raw parquet files stored in `data/raw/` with checksums. Derivations (embeddings, state graphs) in `data/processed/` with new filenames. |
| **IV. Single Source of Truth** | **PASS** | All success rates and metrics in the final report will be generated via scripts reading from `data/` and `code/`. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in `state/`. `updated_at` timestamps managed by the agent. |
| **VI. Simulation Fidelity Independence** | **PASS** | **Primary metrics** (SC-001, SC-002) derived *only* from real-world execution. The "Oracle" is a diagnostic tool only, not used for the primary hypothesis test. Continuous physics variables explicitly excluded from `SymbolicState`. |
| **VII. Computational Efficiency** | **PASS** | Wall-clock time and memory logs (CPU cycles, RAM) recorded for every task to substantiate the "CPU-tractable" claim. |

## Project Phases

### Phase 0: Baseline Re-Execution
**Goal**: Generate paired baseline data for statistical validity.
**Tasks**:
1. Load the specific RoboDojo tasks from the dataset (Commit `v.1`).
2. Execute the original RoboDojo Neural Policy (pre-trained weights) on all tasks in the real-world environment (or high-fidelity sim if real-robot unavailable, logged as "Sim-Baseline").
3. Record `ExecutionOutcome` for each task.
**Output**: `data/interim/baseline_results.parquet`.

### Phase 0.5: Adapter Construction (Sim-to-Real)
**Goal**: Train the low-level controller adapter without overfitting to the test set.
**Tasks**:
1. Split the tasks into a training set and a hold-out validation set.
2. Train a "Linear Probe" on top of the frozen MobileViT backbone using a diverse set of tasks.
3. Validate on the hold-out tasks to ensure generalization.
4. Retrain on all tasks for the final evaluation (acknowledging the limitation, but ensuring the baseline comparison is fair).
**Output**: `data/processed/adapter_weights.pt`.

### Phase 1: Symbolic Abstraction & Planning
**Goal**: Generate symbolic plans for the 18 tasks.
**Tasks**:
1. **Vision Encoding**: Run `vision_encoder.py` on raw video frames to generate `SemanticEmbedding`.
2. **State Mapping**: Run `state_mapper.py` with deterministic thresholding (e.g., `>0.6` for `graspable`). Log ambiguity scores.
3. **Planning**: Run `planner.py` (A*) to generate `ActionSequence`.
4. **Constraint Check**: Verify execution time ≤ 60s per task.
**Output**: `data/interim/symbolic_plans.json`, `data/interim/planning_metrics.json`.

### Phase 2: Real-World Execution & Logging
**Goal**: Execute symbolic plans and log failure modes.
**Tasks**:
1. Execute `ActionSequence` using the Adapted Low-Level Controller.
2. Log `ExecutionOutcome` with `failure_mode` (Planner Infeasibility vs. Controller Execution Failure).
3. Record `ComputeMetric` (CPU cycles, RAM).
**Output**: `data/interim/execution_logs.parquet`.

### Phase 3: Oracle Control (Diagnostic Only)
**Goal**: Measure theoretical planner upper bound.
**Tasks**:
1. Execute `ActionSequence` against a "Perfect Low-Level Executor" (simulated).
2. Record success rate (expected to be high).
3. Calculate `Physics Fidelity Gap` = `Success_Oracle - Success_RealWorld`.
**Output**: `data/interim/oracle_results.json`.

### Phase 4: Ablation Study (FR-008)
**Goal**: Vary state representation detail.
**Tasks**:
1. Run Phase 1 & 2 with "Full Affordance Graph".
2. Run Phase 1 & 2 with "Simplified Connectivity Graph".
3. Compare success rates and compute overhead.
**Output**: `data/interim/ablation_results.parquet`.

### Phase 5: Statistical Analysis & Reporting (SC-004, SC-005)
**Goal**: Perform statistical tests and threshold checks.
**Tasks**:
1. **Wilcoxon Test**: Compare Symbolic vs. Baseline success rates (paired).
2. **Effect Size**: Calculate rank-biserial correlation.
3. **Catastrophic Failure Rate**: Calculate % of tasks with "Hardware Error" or "Timeout". Compare to a predefined threshold.
4. **Power Analysis**: Report limitations (N=18).
**Output**: `data/final/statistical_report.txt`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Oracle Executor** | Required to isolate the "Physics Fidelity Gap" (US-4, SC-006). | Without the Oracle, we cannot distinguish between planner infeasibility and low-level controller failure, violating the scientific rigor of the hypothesis test. |
| **Sim-to-Real Adapter** | Real-world video data differs from simulation; direct use of sim weights fails. | Using raw simulation weights would result in catastrophic failure rates, making the comparison invalid. |
| **Split-Data Adaptation** | Prevents overfitting confounds (Methodology Concern). | Fine-tuning on all 18 tasks would invalidate the baseline comparison. |

## Project Structure

```text
specs/001-symbolic-dojo-extend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── symbolic_state.schema.yaml
│   ├── execution_outcome.schema.yaml
│   ├── compute_metric.schema.yaml
│   └── ablation_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── src/
│   ├── __init__.py
│   ├── config.py                # Paths, seeds, hyperparameters
│   ├── data_loader.py           # RoboDojo parquet ingestion, streaming
│   ├── vision_encoder.py        # MobileViT (frozen, CPU) for embeddings
│   ├── state_mapper.py          # Embedding -> SymbolicState logic
│   ├── planner.py               # A* / MCTS implementation
│   ├── controller_adapter.py    # Low-level controller (Sim-to-Real protocol)
│   ├── oracle_executor.py       # Simulated "Perfect" executor for control
│   ├── metrics_logger.py        # CPU/RAM/Time logging
│   └── stats_analysis.py        # Wilcoxon tests, gap analysis
├── tests/
│   ├── contract/                # Schema validation tests
│   ├── integration/             # Planner end-to-end tests
│   └── unit/                    # State mapping tests
├── main.py                      # Orchestration script
└── requirements.txt             # Pinned dependencies
```