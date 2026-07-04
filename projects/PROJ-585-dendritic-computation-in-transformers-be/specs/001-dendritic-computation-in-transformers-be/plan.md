# Implementation Plan: Dendritic Computation in Transformers: Beyond Point Neurons

**Branch**: `001-dendritic-computation-in-transformers` | **Date**: 2026-06-08 | **Spec**: `specs/001-dendritic-computation-in-transformers/spec.md`
**Input**: Feature specification from `specs/001-dendritic-computation-in-transformers/spec.md`

## Summary

This project implements a rigorous comparison between standard transformer architectures (point-neuron feedforward layers) and a novel variant incorporating biologically inspired dendritic compartmentalization (local nonlinearities and plateau potential gating). The primary objective is to determine if dendritic mechanics enable more efficient hierarchical feature detection on the GLUE SST-2 benchmark, strictly controlling for parameter count and FLOPs. The implementation adheres to a CPU-only constraint (limited cores, constrained RAM, 6h limit). and includes a full probing pipeline with statistical validation across multiple seeds.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `torch` (CPU-only wheel), `scikit-learn`, `datasets` (HuggingFace), `pandas`, `numpy`, `pytest`, `wandb` (optional, local logging preferred for CPU constraints)
**Storage**: Local file system (`data/`, `artifacts/`, `state/`) for checkpoints, logs, and checksums; no external database.
**Testing**: `pytest` for unit tests (model architecture, FLOP counting); integration tests for training loops.
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7GB RAM).
**Project Type**: Research library / CLI tool.
**Performance Goals**: Training must complete or hit a hard stop within 6 hours; FLOP matching within <1% (counting non-linear gates as distinct operations); parameter matching within <0.1%.
**Constraints**: No GPU/CUDA; no 8-bit quantization; memory usage <7GB; strict adherence to matched compute budgets.
**Scale/Scope**: Single benchmark (SST-2), A small number of random seeds, shallow-to-moderate transformer depth (e.g., 4-6 layers) to ensure CPU feasibility.

> Note: Empirical values (exact dataset splits, final accuracies) are deferred to the implementation phase.

**FLOP Counting Methodology**:
To ensure fair comparison (FR-002), the FLOP counter explicitly accounts for the computational cost of dendritic gates.
- Matrix Multiplication: Constant-factor operations proportional to H * W.
- Non-linear Gating (Sigmoid, Element-wise Multiply): a constant number of operations per element.
- The <1% tolerance is calculated on the *total* operation count, ensuring the gating overhead is not ignored. If the dendritic model has higher non-linear overhead, the linear projection width will be reduced to compensate.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, deterministic data loading, and `requirements.txt`. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will strictly use verified URLs from the spec block. |
| **III. Data Hygiene** | **PASS** | Data will be checksummed; raw data preserved; derived data written to new files. Checksums recorded in `data/checksums.manifest` and `state/artifact_hashes.yaml`. |
| **IV. Single Source of Truth** | **PASS** | All metrics traced to `data/experiments/` logs and code blocks. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts will be updated upon change. |
| **VI. Dendritic Model Documentation** | **PASS** | Plan explicitly requires exposing `local_nonlinearities`, `plateau_gating`, and `calcium_modulation` as configurable modules with logged hyperparameters. |
| **VII. Benchmark Parity** | **PASS** | Plan enforces matched parameters/FLOPs, identical schedules, and 6h wall-clock limit. |

## Project Structure

### Documentation (this feature)

```text
specs/001-dendritic-computation-in-transformers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── models/
│   ├── __init__.py
│   ├── transformer_base.py       # Standard point-neuron baseline
│   ├── transformer_dendritic.py  # Dendritic variant with compartmentalized units
│   └── utils.py                  # FLOP counter, parameter matcher
├── data/
│   ├── __init__.py
│   └── loaders.py                # SST-2 loader with checksums
├── experiments/
│   ├── train.py                  # Main training loop with 6h timeout
│   ├── probe.py                  # Linear probing on intermediate layers
│   ├── analyze.py                # Statistical tests (t-test, FDR)
│   └── validate_arch.py          # Architecture validation script
├── config/
│   └── config.yaml               # Hyperparameters, dendritic thresholds
├── tests/
│   ├── test_architecture.py      # Verify FLOP/Param matching
│   └── test_training.py          # Verify timeout and logging
├── requirements.txt
└── main.py                       # CLI entry point

artifacts/
├── logs/
├── checkpoints/
└── results/

state/
├── artifact_hashes.yaml          # Checksums for data hygiene (Constitution III)
└── current_stage.yaml
```

**Structure Decision**: A single `code/` directory with modular separation of models, data, and experiments. This minimizes import overhead and simplifies the CPU-only execution environment. The `models/` directory explicitly separates the baseline and dendritic implementations to ensure the "Distinct Logic" requirement (Constitution VI) is met. The `state/` directory is explicitly included to house the `artifact_hashes` map required by Constitution III.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Dendritic Sub-units** | Required by spec (FR-001) to test biological realism hypothesis. | Reverting to standard MLPs would fail the research question entirely. |
| **Statistical Probing** | Required by FR-004/005 to measure "hierarchical feature detection" (US-3). | Comparing only final accuracy would miss the core mechanism (local vs. global feature extraction). |
| **FLOP Counter** | Required by FR-002 to ensure fair comparison. | Assuming parameter count equality is insufficient; FLOPs vary with nonlinearity complexity. |
| **6h Timeout Mechanism** | Required by US-2 and Constitution VII (Compute Consistency). | Without a hard stop, CPU-only training might run indefinitely, violating the "fair comparison" constraint. |