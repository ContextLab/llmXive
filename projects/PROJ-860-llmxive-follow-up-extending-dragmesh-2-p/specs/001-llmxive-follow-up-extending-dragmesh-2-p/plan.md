# Implementation Plan: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Branch**: `001-virtual-tactile-adaptation` | **Date**: 2026-07-13 | **Spec**: `specs/001-virtual-tactile-adaptation/spec.md`
**Input**: Feature specification from `/specs/001-virtual-tactile-adaptation/spec.md`

## Summary

This feature extends the DragMesh-2 framework to implement a "Virtual Tactile" zero-shot adaptation mechanism for dexterous hand-object interaction. The core innovation is a non-neural estimator that computes a stiffness proxy ($k_{est}$) from the ratio of hand joint torque derivatives to object velocity derivatives. This proxy drives an adaptive reward scheduler that dynamically adjusts detachment and contact maintenance weights during simulation, enabling the policy to handle unseen friction coefficients spanning a broad range without retraining. The implementation strictly adheres to CPU-only constraints (PyBullet) to ensure reproducibility on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pybullet` (CPU-only), `numpy`, `scipy` (for statistical tests), `pandas`, `datasets` (for HuggingFace loading), `pytest`, `statsmodels` (for power analysis)  
**Storage**: Local file system for generated geometry and logs; HuggingFace Hub for DragMesh-2 dataset.  
**Testing**: `pytest` with `pytest-timeout` to enforce 6-hour limit; `pytest-mock` for unit testing the estimator logic.  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~modest RAM).  
**Project Type**: Research simulation pipeline / library.  
**Performance Goals**: Complete full experiment (30 objects, 50 trials each, training, inference, analysis) in ≤ 6 hours; peak memory ≤ 7 GB.  
**Constraints**: No CUDA/GPU operations; no 8-bit/4-bit quantization; strict CPU backend for physics engine.  
**Scale/Scope**: A set of novel object geometries; 1 static baseline policy; 1 adaptive policy; statistical comparison via paired t-test on aggregated success rates.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates pinned `requirements.txt` (located in `code/`), random seed fixation, and re-runnable scripts against the canonical HuggingFace DragMesh-2 source.
2.  **II. Verified Accuracy**: All citations in `research.md` will be restricted to the verified HuggingFace dataset URL provided in the spec. The CI pipeline includes a `validate_citations.py` step that checks URL reachability and title-token-overlap (≥ 0.7) before execution.
3.  **III. Data Hygiene**: The plan requires checksumming of the DragMesh manifest and any derived geometry files. Checksums are recorded in `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under the `artifact_hashes` map. The `data/raw` directory is mounted read-only in the CI environment to enforce no in-place modifications.
4.  **IV. Single Source of Truth**: The `data/` directory will store the generated objects and simulation logs. The `paper/` (future) will reference these specific files.
5.  **V. Versioning Discipline**: Artifacts (schemas, logs) will be tracked with content hashes in the project state file `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under `artifact_hashes`.
6.  **VI. CPU-Only Simulation Fidelity**: The plan explicitly selects PyBullet with CPU backend and prohibits any GPU-accelerated libraries or CUDA calls.
7.  **VII. Derivative-Based Stiffness Proxy Validation**: The plan includes the specific formula $k_{est} = \frac{|\Delta \tau_{hand}|}{|\Delta v_{object}|}$ (with mass normalization) and the paired t-test validation against the static baseline as required.

## Project Structure

### Documentation (this feature)

```text
specs/001-virtual-tactile-adaptation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── estimator_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/
├── data/
│   ├── raw/             # DragMesh-2 manifest (downloaded, read-only)
│   └── generated/       # novel object geometries
├── code/
│   ├── __init__.py
│   ├── config.py        # Hyperparameters, seeds
│   ├── estimator.py     # VirtualTactileEstimator (FR-001, FR-006, FR-007)
│   ├── scheduler.py     # AdaptiveRewardScheduler (FR-002)
│   ├── environment.py   # PyBullet CPU setup (FR-004)
│   ├── generator.py     # NovelObjectSet generation (FR-003)
│   ├── train.py         # Policy training loop
│   ├── evaluate.py      # Inference and success rate logging
│   ├── analysis.py      # Paired t-test (FR-005)
│   ├── validate_citations.py # CI gate for Principle II
│   └── requirements.txt # Pinning dependencies (Constitution Reproducibility)
├── tests/
│   ├── unit/
│   │   └── test_estimator.py
│   └── integration/
│       └── test_pipeline.py
├── state/
│   └── projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml # State file with artifact_hashes
└── README.md
```

**Structure Decision**: A single-project structure is selected. The research involves a tight coupling between the estimator, scheduler, and physics environment, making a monolithic `code/` directory more efficient for simulation state management and reproducibility than a microservices split. The `data/` directory is strictly separated to enforce the "Data Hygiene" constitution principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project adheres to all constraints. | The CPU-only constraint is a hard requirement for CI feasibility, not a complexity choice. |