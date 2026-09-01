# Implementation Plan: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

**Branch**: `001-predict-molecular-surface-charge` | **Date**: 2026-08-24 | **Spec**: `specs/001-predict-molecular-surface-charge/spec.md`
**Input**: Feature specification from `/specs/001-predict-molecular-surface-charge/spec.md`

## Summary

This project implements a Geometric Graph Neural Network (GNN) to predict atomic partial charges (Merz-Kollman) from 3D molecular geometry using the QM9 dataset. The system ingests QM9 data, trains a SchNet or DimeNet architecture on CPU-only hardware (GitHub Actions free tier), and validates that 3D geometry provides predictive power beyond simple connectivity (2D graph) baselines. The implementation strictly adheres to a scaffold-based split (Bemis-Murcko) to ensure generalization to unseen molecular topologies and targets a Mean Absolute Error (MAE) ≤ 0.05 e.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch, PyTorch Geometric, RDKit, `datasets` (Hugging Face), `numpy`, `pandas`, `scikit-learn`  
**Storage**: Local filesystem (temporary artifacts in `data/` and `code/`); QM9 dataset streamed from Hugging Face.  
**Testing**: `pytest` (unit tests for architecture, integration tests for training/evaluation loops).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, ~7 GB RAM).  
**Project Type**: Scientific Computing / Machine Learning Pipeline  
**Performance Goals**: Training completes ≤ 6 hours; Peak memory ≤ 7 GB; Model size < 500 MB.  
**Constraints**: CPU-only execution for training; No local GPU; Streaming dataset loading to avoid OOM.  
**Scale/Scope**: Subset of QM9 (approx. 130k molecules, sampled/streamed to fit memory); ~10 epochs for validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Plan Compliance Strategy |
|-----------|-------------|--------------------------|
| **I. Reproducibility** | Pin seeds, canonical sources, reproducible runs. | `random_seed=42` enforced in all loaders/splitters. QM9 source pinned to verified Hugging Face URL. `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | Citations verified against primary sources. | All dataset citations (QM9) use only the verified Hugging Face URLs provided in the spec. No fabricated URLs for ESP-derived data. |
| **III. Data Hygiene** | Checksums, no in-place modification, new files for derivations. | Raw QM9 parquet checksum recorded. Derived features (normalized coords) written to new files in `data/processed/`. |
| **IV. Single Source of Truth** | Figures/stats trace to one row in data/code. | Evaluation script outputs JSON report; paper text generated programmatically from this JSON. No hand-typed numbers. |
| **V. Versioning** | Content hashes, artifact updates. | `state/` YAML updated on artifact change. Code artifacts hashed on commit. |
| **VI. Numerical Stability** | Normalize coords, strict float consistency. | Plan includes explicit center-of-mass normalization step. MAE/RMSE computed in float32/64 consistently. |
| **VII. Structural Generalization** | Scaffold-based split (Bemis-Murcko). | `FR-004` mandates RDKit Bemis-Murcko split. Validation uses scaffold-aware metrics. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-surface-charge/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── prediction.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-404-predicting-molecular-surface-charge-dist/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py           # QM9 streaming, filtering, normalization
│   │   └── split.py            # Bemis-Murcko scaffold split
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schnet.py           # SchNet implementation
│   │   ├── dimenet.py          # DimeNet implementation
│   │   └── gnn_2d.py           # Connectivity-only baseline
│   ├── train/
│   │   ├── __init__.py
│   │   ├── trainer.py          # Training loop, early stopping
│   │   └── utils.py            # Metrics, logging
│   └── eval/
│       ├── __init__.py
│       ├── evaluator.py        # MAE, RMSE, R calculation
│       └── report.py           # JSON report generation
├── data/
│   ├── raw/                    # Symlinks or downloads (checksummed)
│   └── processed/              # Normalized, split data
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_loader.py
│   │   └── test_models.py      # Architecture init tests
│   └── integration/
│       ├── test_training.py    # Loop completion, early stopping
│       └── test_evaluation.py  # Full pipeline, baseline comparison
└── state/
    └── projects/PROJ-404-predicting-molecular-surface-charge-dist.yaml
```

**Structure Decision**: Single project structure (`code/` subpackage) is selected. This minimizes import complexity for a scientific pipeline and aligns with the "CPU-first" constraint where a monolithic, well-structured script or small package is more efficient to manage than a microservice architecture. The `tests/` directory mirrors `code/` for direct coverage mapping.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Scaffold Split vs Random Split** | Required by Constitution Principle VII and US-3 to test generalization to unseen topologies. | Random splitting would leak structural information (scaffolds) between train/test, invalidating the hypothesis that 3D geometry predicts charge for *new* molecules. |
| **Streaming Data Loading** | Required by SC-005 (7 GB RAM limit) for QM9 (130k+ molecules). | Loading full QM9 into RAM exceeds 7 GB. Streaming allows processing on the free-tier runner without OOM. |
| **2D Baseline GNN** | Required by US-3 and SC-003 to quantify the value of 3D geometry. | A simple atom-type average baseline is insufficient; a 2D GNN provides a stronger, more realistic baseline that accounts for connectivity alone. |
| **Separate Evaluation Script** | Required by US-3 and Constitution IV (Single Source of Truth). | Embedding evaluation in training prevents independent verification and makes the "exit code" logic for hypothesis validation (FR-007) harder to isolate and test. |
