# Implementation Plan: Reproduce & Validate ProRL

**Branch**: `640-reproduce-prorl` | **Date**: 2025-05-24 | **Spec**: `specs/640-reproduce-prorl/spec.md`
**Input**: Feature specification from `/specs/640-reproduce-prorl/spec.md`

## Summary

Reproduce the ProRL (Proactive Reinforcement Learning) algorithm from the paper "Effective Reinforcement Learning for Proactive Recommendation via Rectified Policy Gradient Estimation" (arXiv:2605.28293). The implementation will execute the pre-training and RL training pipelines on the `Books` dataset using a CPU-only environment (GitHub Actions free-tier: limited vCPU and RAM resources). The plan focuses on adapting the vendored codebase to run without CUDA dependencies, validating output artifacts, and generating a reproduction report that documents the CPU constraints and achieved metrics.

**Critical Scope Definition**: Due to hardware constraints (7GB RAM, 2 vCPU), this project is scoped as a **Feasibility and Implementation Fidelity Demonstration**. It will validate that the ProRL codebase executes correctly on CPU and produces valid artifacts. It will **not** claim statistical validation of the paper's performance claims (e.g., "ProRL outperforms Baseline X by Y%") due to the inability to perform a full power analysis or run sufficient epochs for convergence on a sampled dataset. Results will be reported as "Observed Performance under Resource Constraints".

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only build), `transformers` (CPU-compatible), `scikit-learn`, `pandas`, `numpy`.  
**Storage**: Local file system (`ckpt/`, `logs/`, `datasets/`).  
**Testing**: `pytest` (contract tests for artifact validity).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Research / Reproduction.  
**Performance Goals**: Complete full pipeline (Pretrain + RL) within 6 hours on CPU; peak RAM < 7GB.  
**Constraints**: No GPU/CUDA; no quantization libraries (`bitsandbytes`); dataset must be sampled if >7GB.  
**Scale/Scope**: Single dataset (`Books`); 100 epochs of RL; 1 reproduction report.

> Note: The `Books` dataset is sourced from the ProRL repository submodule. If the full dataset or embeddings exceed memory, the implementation will apply a **Stratified Sampling** strategy to preserve distributional properties, documented in `research.md`.

## Constitution Check

*Gates determined based on constitution file:*

1.  **Constitution Status**: No `constitution.md` was provided for this project (per input).
2.  **Fallback Principles**: This plan adheres to standard research integrity principles as a fallback:
    *   **Reproducibility**: The plan explicitly documents the CPU-only constraint and sampling strategy to ensure the run can be replicated on standard CI.
    *   **Data Integrity**: The plan includes validation steps (FR-003) to ensure checkpoints are not empty or NaN, preventing "silent failures."
    *   **Resource Compliance**: The plan explicitly forbids GPU-specific libraries and mandates a failure mode if RAM limits are exceeded (FR-006).
    *   **Methodological Rigor**: The plan distinguishes between "execution success" (code runs) and "performance success" (metrics match paper), ensuring honest reporting of CPU limitations.

## Project Structure

### Documentation (this feature)

```text
specs/640-reproduce-prorl/
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
├── prorl/
│   ├── __init__.py
│   ├── dataset.py       # Data loading with stratified sampling logic
│   ├── model.py         # Model definition (CPU compatible)
│   ├── trainer_pretrain.py # Pre-training logic
│   ├── trainer_rl.py    # RL training logic
│   └── evaluator.py     # Metrics calculation
├── scripts/
│   ├── run_pipeline.sh  # Orchestration script
│   └── validate_artifacts.py # Contract validation
├── data/
│   └── books/           # Dataset directory (from submodule)
├── ckpt/                # Output: Checkpoints
├── logs/                # Output: Training logs
└── reports/             # Output: reproduction_report.md

tests/
├── contract/
│   └── test_artifacts.py # Validates FR-003, FR-004
├── integration/
│   └── test_pipeline.py # Validates US-1, US-2
└── unit/
    └── test_dataset.py  # Validates sampling logic
```

**Structure Decision**: Single-project structure (`src/prorl`) is selected to minimize overhead for a research reproduction. The `scripts` directory handles orchestration, while `tests` are separated for contract validation. The `data`, `ckpt`, and `logs` directories are top-level to match standard ML project conventions and simplify pathing in the CI environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly defined by the paper's codebase. | N/A |

## Detailed Phase Plan

### Phase 0: Research & Feasibility (Current)
- **Goal**: Confirm `Books` dataset compatibility, CPU feasibility, and distribution preservation.
- **Actions**:
  - Inspect `datasets/Books` structure (`inter`, `datamaps`, `sem_ids`).
  - **Size Check**: Verify `qwen3-embedding-8b-pca.sem_ids` file size. If > 6GB, abort with "Resource Too Large" error.
  - **Distribution Check**: Analyze interaction distribution (item popularity bins). Plan Stratified Sampling to preserve these ratios.
  - Verify `requirements.txt` for CUDA dependencies; plan `pip` overrides for CPU-only `torch`.
- **Output**: `research.md`, `data-model.md`.

### Phase 1: Design & Contracts
- **Goal**: Define data schemas, validation contracts, and memory monitoring logic.
- **Actions**:
  - Define input schema for `dataset.py` (FR-001).
  - Define output schema for `metrics.json` (FR-004) including baseline fields.
  - Create `contracts/` YAML files for validation.
  - **Implement Memory Monitoring**: Design `DatasetSampler` with RSS monitoring (abort if >7GB).
  - Draft `quickstart.md` for CI execution.
- **Output**: `contracts/*.schema.yaml`, `quickstart.md`.

### Phase 2: Implementation (Implementer Agent)
- **Goal**: Execute the pipeline with strict resource controls.
- **Actions**:
  - Setup CI environment (install CPU `torch`).
  - **Step 1**: Run Pre-training (FR-001) with memory monitoring.
  - **Step 2**: Run RL Training (FR-002) using pretrain checkpoint.
  - **Step 3**: Validate artifacts using `contracts/dataset.schema.yaml` and `contracts/metrics.schema.yaml` defined in Phase 1.
  - **Step 4**: Generate Report (FR-005) including CPU constraints and baseline comparisons.
- **Output**: `ckpt/*.pth`, `logs/*.csv`, `reports/reproduction_report.md`.

### Phase 3: Verification
- **Goal**: Confirm Success Criteria.
- **Actions**:
  - Run contract tests.
  - Verify `reproduction_report.md` content against SC-003.
  - Ensure no GPU errors in logs (SC-005).
  - **Scientific Check**: Verify that ProRL metrics > Random Baseline metrics (if available).

## FR/SC Mapping

| Requirement | Plan Element | Description |
|-------------|--------------|-------------|
| **FR-001** (Pretrain CPU) | Phase 2, Step 1 | Run `trainer_pretrain.py` with CPU flag; enforce a reasonable timeout. |
| **FR-002** (RL CPU) | Phase 2, Step 2 | Run `trainer_rl.py` using pretrain checkpoint; enforce a sufficient number of epochs for convergence. |
| **FR-003** (Checkpoint Valid) | Phase 2, Step 3 | `validate_artifacts.py` checks file size > 0 and non-NaN tensors. |
| **FR-004** (Metrics Log) | Phase 2, Step 3 | `evaluator.py` writes `metrics.json` with HitRate/NDCG and baselines. |
| **FR-005** (Report Gen) | Phase 2, Step 4 | Script generates `reproduction_report.md` with env details. |
| **FR-006** (RAM Limit) | Phase 1, Design | Implement `DatasetSampler` with RSS monitoring; abort if >7GB with specific error. |
| **FR-007** (No CUDA) | Phase 0, Research | Pin `torch` to CPU wheel; fail if `cuda` import detected. |
| **SC-001** (Time Limit) | Phase 2, Config | Set CI job timeout to a reasonable duration; log time per epoch. |
| **SC-002** (Artifact Valid) | Phase 3, Test | Contract test asserts checkpoint keys exist. |
| **SC-003** (Report Content) | Phase 3, Test | Grep report for "CPU", "7GB", "Books". |
| **SC-004** (RAM Compliance) | Phase 2, Monitor | Monitor RSS memory; abort if >7GB. |
| **SC-005** (No GPU Calls) | Phase 3, Log | Scan logs for "CUDA", "GPU", "Cuda". |