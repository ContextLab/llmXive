# Implementation Plan: Kairos: A Native World Model Stack for Physical AI

**Branch**: `001-kairos-world-model-stack` | **Date**: 2026-06-30 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-kairos-world-model-stack/spec.md`

## Summary

This project implements a comparative study of world model architectures for embodied AI. The primary requirement is to evaluate a "Hybrid Multi-Scale Temporal Memory" module (Kairos) against a baseline Transformer-based world model. The technical approach involves training both models on a stratified subset of **BridgeData V2 (Kitchen domain)** robotics manipulation data within a MuJoCo simulation environment, strictly constrained to CPU-only execution (<7 GB RAM, 1 effective core via thread pinning). The study measures Long-Horizon Success Rate, Prediction Error (MSE), and Physics Consistency Score (PCS) to determine if the memory-augmented architecture improves **Initial Learning Slope** (sample efficiency proxy) and planning fidelity in the specific domains present in the dataset.

*Scope Note*: The "open-world" claim is explicitly bounded to the diversity of tasks within the BridgeData V2 Kitchen subset. The study explicitly acknowledges that the Open X-Embodiment dataset is excluded due to the lack of a verified source URL in the project's verified dataset list. **If BridgeData V2 is unavailable, the study is aborted** to prevent reliance on synthetic data, which would invalidate the "open-world" and "sample efficiency" claims.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mujoco`, `gymnasium`, `torch` (CPU-only build), `transformers`, `scikit-learn`, `pandas`, `numpy`, `ucimlrepo` (for BridgeData V2 access)  
**Storage**: Local filesystem (`data/` for datasets, `artifacts/` for checkpoints/logs)  
**Testing**: `pytest` (unit), `pytest-benchmark` (latency), custom integration scripts for simulation trajectories  
**Target Platform**: Linux (GitHub Actions Free Runner: limited CPU resources, ~7 GB RAM, no GPU)  
**Project Type**: Computational Research / Simulation Study  
**Performance Goals**: <200ms total control loop (split: ~100ms simulation + ~100ms inference), <7 GB peak RAM, <6h total runtime.  
**Constraints**: No GPU usage, no 8-bit quantization, strict adherence to stratified dataset sampling to fit memory limits. `torch.set_num_threads(1)` enforced.  
**Scale/Scope**: A set of test trajectories from BridgeData V2

The research question remains: How can we evaluate the robustness of the proposed method? The method is: We will employ a benchmarking protocol using test trajectories from BridgeData V2. References: [Insert DOI/arXiv/author-year here]., Multiple random seeds, A sample of training steps is planned..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds will be pinned in `code/`. External datasets will be fetched via `ucimlrepo` or verified HuggingFace loaders with specific revision hashes. `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **Pass** | Citations for datasets (BridgeData V2) and methods (MuJoCo, GatedDeltaNet) will be validated against primary sources. No title-token-overlap without verification. |
| **III. Data Hygiene** | **Pass** | Raw data downloads will be checksummed (`data/`); no in-place modification. Derivations (stratified subsets) will be new files with documented hashes. |
| **IV. Single Source of Truth** | **Pass** | All metrics (MSE, Success Rate) in the final report will be auto-generated from `data/` rows and `code/` execution logs. No hand-typed statistics. |
| **V. Versioning Discipline** | **Pass** | Artifacts (checkpoints, logs) will carry content hashes. The `state` YAML will be updated on any change. |
| **VI. Simulation Fidelity** | **Pass (Enforced)** | Experiments strictly limited to MuJoCo + Franka Panda. Resource monitoring (RAM, CPU) will be logged per step. **Mitigation**: `torch.set_num_threads(1)` is enforced to strictly limit CPU usage to 1 active thread, satisfying the "single CPU core" constraint despite the runner's 2 vCPU availability. Deviation >7 GB RAM invalidates the run. |
| **VII. Long-Horizon Validation** | **Override (Mitigated)** | Evaluation focuses on Success Rate (N steps), MSE, and PCS over a set of representative trajectories. **Override**: The Constitution mandates "paired t-tests", but with N=5 seeds, normality assumptions are likely violated. The plan uses **Bootstrap Confidence Intervals** as the primary test for effect size, with Wilcoxon signed-rank as a secondary check. This is a standard statistical override for small sample sizes to ensure validity. The Constitution's t-test requirement is scientifically unsound for N=5. |

## Spec Gap & Scope Reduction

*This section addresses the discrepancy between the Spec's "UNION" requirement and the available verified data.*

- **FR-001 & FR-005**: The spec requires a "stratified subset of the UNION of Open X-Embodiment and BridgeData V2".
- **Reality**: No verified source URL exists for Open X-Embodiment in the project's verified dataset list.
- **Action**: The plan **excludes** Open X-Embodiment. The study proceeds **only** with BridgeData V2 (Kitchen subset).
- **Impact**: FR-001 and FR-005 are **Partially Satisfied**. The "UNION" requirement is not met. The "open-world" claim is bounded to the "Kitchen" domain diversity. This is a **Scope Reduction** and is explicitly flagged for spec revision (kickback).
- **Consequence**: Success Rate and PCS metrics are valid only for the Kitchen domain, not the full "open-world" scope.
- **Abort Condition**: If BridgeData V2 is not accessible via verified loaders, the study **aborts**. No synthetic fallback is permitted.

## Project Structure

### Documentation (this feature)

```text
specs/001-kairos-world-model-stack/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-740-kairos-a-native-world-model-stack-for-ph/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── main.py                 # Entry point for training/eval
│   ├── config.py               # Hyperparameters & paths
│   ├── data/
│   │   ├── loader.py           # Dataset ingestion (BridgeData V2 via ucimlrepo/HF)
│   │   └── preprocessing.py    # Stratified sampling & normalization
│   ├── models/
│   │   ├── __init__.py
│   │   ├── baseline_transformer.py
│   │   └── kairos_memory.py    # Hybrid Multi-Scale Memory module
│   ├── env/
│   │   ├── __init__.py
│   │   └── mujoco_panda.py     # MuJoCo Franka Panda wrapper
│   ├── eval/
│   │   ├── metrics.py          # MSE, Success Rate, PCS logic (incl. Energy/Momentum checks for sim, Heuristics for real)
│   │   └── statistical.py      # Bootstrap CI & Wilcoxon
│   └── utils/
│       ├── logger.py           # RAM/CPU monitoring
│       └── checkpoint.py       # Saving/loading
├── data/
│   ├── raw/                    # Downloaded raw subsets (checksummed)
│   └── processed/              # Stratified training/test splits
├── artifacts/
│   ├── logs/                   # Training logs, latency profiles
│   └── checkpoints/            # Model weights (baseline & kairos)
└── tests/
    ├── unit/                   # Component tests
    ├── integration/            # Sim loop tests
    └── contract/               # Schema validation tests
```

**Structure Decision**: A modular `code/` directory layout is selected to separate data ingestion, model definition, environment simulation, and evaluation logic. This ensures the "Single Source of Truth" principle is maintained by isolating metric calculation logic in `eval/metrics.py` and preventing data leakage between training and testing phases.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Hybrid Memory Module** | Required to test the core hypothesis (Kairos) against baseline. | A pure Transformer baseline cannot test the "multi-scale temporal memory" variable. |
| **Bootstrap CI** | Required for robust statistical inference with N=5 seeds where normality is violated. | Paired t-test assumes normality which is unlikely with n=5; Wilcoxon has low power. |
| **MuJoCo + Franka Panda** | Required for physics consistency (PCS) and realistic robot dynamics. | Simpler grid-world environments lack the "physics consistency" and "collision" variables required by FR-005. |
| **BridgeData V2 Only** | Required to use a verified source for real-world trajectories. | Open X-Embodiment excluded due to lack of verified source; synthetic data rejected to avoid circular validation. |

## Latency Budget Mitigation

*Addressing the concern that <200ms total loop (sim + inference) on 1 CPU core is empirically improbable.*

- **Target**: <200ms per step (p95).
- **Risk**: MuJoCo simulation + Transformer inference on 1 CPU core may exceed 200ms.
- **Mitigation**:
  1. The system will log `sim_time` and `inference_time` **separately**.
  2. If `total_time > 200ms`, the run is **flagged as "Fail Real-Time"**.
  3. **Crucially**: The run is **NOT aborted**. The data is recorded, and the result is reported as a failure of the "real-time" claim.
  4. This ensures the study can still measure *planning fidelity* even if the *real-time* constraint is not met, providing a valid (negative) result rather than a broken test.

## Sample Efficiency & Training Limitations

*Addressing the concern that ~10k steps is insufficient for convergence.*

- **Strategy**: The study measures **Initial Learning Slope** (loss reduction per step in the initial phase of training) and **Final MSE at fixed step count** (10k steps).
- **Rationale**: This tests "early-stage sample efficiency" (how fast the model learns in the first few epochs) rather than full convergence.
- **Disclaimer**: The plan explicitly states that the study does **not** claim to train the models to convergence. The "sample efficiency" claim is bounded to the initial learning phase.

## Data Diversity Validation

*Addressing the concern that a small subset lacks variance.*

- **Action**: Before training, the system will compute the variance of state/action vectors in the stratified subset.
- **Reporting**: The report will include a "Data Diversity Score" comparing the subset's variance to the full dataset (if metadata available) or listing the specific task types covered.
- **Scope**: The "open-world" claim is explicitly bounded to the **BridgeData V2 Kitchen** task distribution.