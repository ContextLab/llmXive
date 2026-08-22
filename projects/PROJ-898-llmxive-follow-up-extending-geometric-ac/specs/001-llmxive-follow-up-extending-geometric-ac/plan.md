# Implementation Plan: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

**Branch**: `001-llmxive-gam-symbolic-planner` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-follow-up-extending-geometric-ac/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-geometric-ac/spec.md`

## Summary

This project implements a symbolic-latent planner to extend the Geometric Action Model (GAM) for zero-shot generalization to novel kinematic chains and deformable materials. The core innovation replaces the learned neural predictor with a differentiable symbolic solver (via DiffTaichi) operating in the 3D latent space of a frozen Geometric Foundation Model (GFM). The system generates a synthetic "topology-shift" test set using PyBullet (300 unique tasks to ensure statistical power), executes the symbolic pipeline on CPU-only hardware, and performs rigorous statistical comparison (McNemar's test, Wilcoxon Signed-Rank) against the baseline GAM.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pybullet` (physics simulation), `diff-taichi` (differentiable solver), `torch` (GFM encoder/decoder, CPU mode), `scipy`/`statsmodels` (statistical tests), `numpy`/`pandas` (data handling).  
**Storage**: Local filesystem (`data/raw`, `data/generated`, `data/results`); **JSONL format only** (no Parquet).  
**Testing**: `pytest` (unit/integration), `pytest-cov` (coverage), custom validation scripts for topology hashing.  
**Target Platform**: GitHub Actions x86_64 runner (2 CPU cores, ~7 GB RAM).  
**Project Type**: Research/Scientific Computing (CLI-driven pipeline).  
**Performance Goals**: Complete 300 trials (approx. 10 steps each) within 6 hours; inference latency < 300ms per step (CPU).  
**Constraints**: No GPU/CUDA; frozen GFM weights; strict topology isolation from training data; constraint satisfaction ≥ 95%.  
**Scale/Scope**: synthetic trials; A symbolic solver implementation

The research question investigates how symbolic solvers can be applied to the problem. The method involves designing and evaluating a symbolic solver implementation. References include [Citation].; statistical analysis report.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **COMPLIANT**. The plan mandates pinned `requirements.txt`, fixed random seeds in all generation scripts, and CPU-only execution to ensure identical results on any fresh runner. External datasets (PyBullet, GFM) are local or user-provided.
- **II. Verified Accuracy**: **COMPLIANT**. All citations (GFM, PyBullet, DiffTaichi) will be validated against the "Verified datasets" block. No fabricated URLs will be used.
- **III. Data Hygiene**: **COMPLIANT**. All generated data (test sets, logs) will be checksummed. Raw simulation states are preserved; derived metrics (success rates, latencies) are written to new files. No in-place modifications.
- **IV. Single Source of Truth**: **COMPLIANT**. The `contracts/trial_log.schema.yaml` defines the single source of truth for trial results. All redundant schema files have been removed.
- **V. Versioning Discipline**: **COMPLIANT**. Every artifact (code, data, config, schema) will carry a content hash. The plan includes a `state` update mechanism for artifact changes (see 'Versioning Mechanism' section).
- **VI. Latent-Space Symbolic Fidelity**: **COMPLIANT**. The plan explicitly freezes GFM weights and isolates the symbolic solver to the latent space, ensuring gradients do not flow through the decoder. Physical constraints are validated in 3D space via the decoder output.
- **VII. Zero-Shot Topology Generalization Protocol**: **COMPLIANT**. The test set generation (FR-001) strictly enforces topology isolation via `training-topology-manifest.json` hashing. No standard benchmarks without topology shifts will be used for primary claims.

## Versioning Mechanism

To satisfy Constitution Principle V:
1. **Hashing**: A script `code/utils/hash_artifacts.py` computes SHA-256 hashes for:
   - `code/` directory (excluding `__pycache__`)
   - `data/raw/` (user-provided weights)
   - `data/generated/` (test set)
   - `data/results/` (trial logs)
   - `contracts/trial_log.schema.yaml` (the single SSoT)
2. **State Update**: The `state/projects/PROJ-898-llmxive-follow-up-extending-geometric-ac.yaml` file is updated post-run with these hashes and a `updated_at` timestamp.
3. **Invalidation**: If a hash changes, the Advancement-Evaluator Agent invalidates stale review records.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-geometric-ac/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── trial_log.schema.yaml  # Single Source of Truth (All other schemas removed)
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/
├── code/
│   ├── __init__.py
│   ├── config.py                # Hyperparameters, paths, seeds
│   ├── data/
│   │   ├── generator.py         # PyBullet topology-shift generation
│   │   └── loader.py            # GFM/PyBullet data loading
│   ├── models/
│   │   ├── gfm_wrapper.py       # Frozen GFM encoder/decoder interface
│   │   ├── symbolic_solver.py   # DiffTaichi constraint solver
│   │   └── baseline_gam.py      # Baseline neural predictor (local impl)
│   ├── evaluation/
│   │   ├── runner.py            # Trial execution loop (CPU)
│   │   └── stats.py             # McNemar, Wilcoxon, drift detection
│   ├── utils/
│   │   └── hash_artifacts.py    # Versioning script
│   └── main.py                  # CLI entry point
├── data/
│   ├── raw/                     # User-provided weights
│   │   └── .gitkeep
│   ├── generated/               # Synthetic test sets
│   │   └── .gitkeep
│   └── results/                 # Trial logs, stats
│       └── .gitkeep
├── tests/
│   ├── unit/
│   │   ├── test_generator.py
│   │   └── test_solver.py
│   └── integration/
│       └── test_end_to_end.py
├── .pre-commit-config.yaml
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. This aligns with the research nature of the project, minimizing overhead. The `code/` directory is split into logical modules (`data`, `models`, `evaluation`) to separate concerns while maintaining a unified execution flow. `data/` directories are strictly separated into `raw` (immutable downloads), `generated` (synthetic test sets), and `results` (trial logs) to enforce data hygiene.

## File System Evidence

The following directories and files are required to exist for the implementation to proceed:
- `data/raw/.gitkeep`
- `data/generated/.gitkeep`
- `data/results/.gitkeep`
- `code/data/generator.py`
- `code/models/symbolic_solver.py`
- `contracts/trial_log.schema.yaml`

## Implementation Phases

### Phase 0: Data & Calibration (Pre-Experiment)

- **0.1 Manifest Generation**: Generate or load `training-topology-manifest.json` from the reference dataset (or a mock if none exists) to satisfy FR-001. Verify zero overlap with generated topologies.
- **0.2 Latent Drift Calibration**: Calculate reference mean/covariance for latent drift detection (FR-001, Edge Cases) from the training distribution (or mock).
- **0.3 Latent Space Validity Test**: Run a preliminary test to verify the frozen GFM encoder produces valid latents for novel topologies (Addressing Assumption).
- **0.4 Ground-Truth Trajectory Generation**: Generate ground-truth 3D trajectories via PyBullet for a subset of tasks to decouple solver failure from decoder failure (Addressing Methodology Concern).

### Phase 1: Core Implementation

- **1.1 Topology-Shift Test Set Generation**: Generate 300 unique tasks using PyBullet (FR-001, US-1).
- **1.2 Symbolic Solver Implementation**: Implement DiffTaichi solver with hybrid convex/non-convex fallback (FR-003, US-2).
- **1.3 Decoder Robustness Control**: Implement a control phase to measure decoder reconstruction error independently (Addressing Methodology Concern).
- **1.4 Finite Difference Verification**: Execute numerical finite difference check to validate solver differentiability (FR-003, Phase 1.6).
- **1.5 Baseline GAM Implementation**: Implement the baseline neural predictor locally for comparison (US-3).

### Phase 2: Execution & Analysis

- **2.1 Trial Execution**: Run 300 trials for both symbolic and baseline methods (US-3).
- **2.2 Statistical Analysis**: Perform McNemar's test (paired success) and Wilcoxon Signed-Rank test (latency) (US-3).
- **2.3 Feasibility Check**: Verify total execution time ≤ 6 hours (SC-005).
- **2.4 CI Time Limit Verification**: Explicitly measure and record `ci_time_limit_exceeded` flag against the 6-hour limit (SC-005).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Differentiable Symbolic Solver (DiffTaichi) | Required to enforce physical constraints in latent space while maintaining gradient flow for validation (FR-003). | Pure neural predictor (baseline) lacks interpretability and fails zero-shot topology generalization. |
| CPU-only Execution | GitHub Actions free-tier constraints (no GPU). | GPU execution would violate the "CPU-first" compute feasibility rule and increase cost/complexity. |
| Topology-Shift Test Set | Required for Zero-Shot generalization hypothesis (Constitution VII). | Standard benchmarks (e.g., RT-1/RT-2) do not contain the specific novel topologies needed. |
| Hybrid Solver (Convex + Fallback) | Soft-body dynamics are non-convex; DiffTaichi alone is insufficient. | Pure non-convex solvers are too slow for the 6-hour limit. |