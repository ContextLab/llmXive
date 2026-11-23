# Implementation Plan: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

**Branch**: `001-predict-molecular-surface-charge` | **Date**: 2026-08-24 | **Spec**: `specs/001-predicting-molecular-surface-charge/spec.md`
**Input**: Feature specification from `specs/001-predicting-molecular-surface-charge/spec.md`

## Summary

This project implements a Geometric Graph Neural Network (GNN) to predict atomic partial charges (Merz-Kollman) from molecular 3D geometry, using the QM9 dataset. The system addresses the research question: "Can 3D structural descriptors learn the structure-to-charge mapping better than 2D connectivity alone?" The implementation is constrained to a CPU-only GitHub Actions runner with limited RAM and a time limit. and must validate generalization to unseen molecular scaffolds.

**Methodological Note**: The baseline comparison involves two components:
1.  **Statistical Baseline**: Atom-Type Average (represents the limit of 2D connectivity without geometric context).
2.  **Architectural Baseline**: Connectivity-Only GNN (2D graph without 3D coordinates), as mandated by FR-006.
The hypothesis is validated if the 3D GNN outperforms *both* baselines on unseen scaffolds, specifically achieving MAE ≤ 0.05 e.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch`, `torch-geometric`, `rdkit`, `pandas`, `numpy`, `scipy`, `datasets` (Hugging Face), `pyyaml`, `pytest`  
**Storage**: Local filesystem (temporary cache for datasets), CSV/Parquet for intermediate splits, JSON for artifacts.  
**Testing**: `pytest` (unit tests for architecture, integration tests for training/eval loops).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete 10+ epochs within 6 hours on 2 vCPU; Peak RAM < 7 GB.  
**Constraints**: 
- No GPU access (unless auto-offloaded to Kaggle for specific CUDA kernels, but plan assumes CPU-first for GNNs like SchNet).
- Must handle missing Merz-Kollman charges via filtering and graceful halting.
- Must use scaffold-based splitting (Bemis-Murcko).
- Must verify data schema (Merz-Kollman columns) before processing.
- Must measure and log peak memory usage.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and programmatic data fetching from verified URLs. Split indices are persisted to disk. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to the "# Verified datasets" block provided in the prompt. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of downloaded QM9 parquet files and writing hashes to `state/projects/PROJ-404-...yaml`. Raw data is preserved; derivations are new files. |
| **IV. Single Source of Truth** | **PASS** | Metrics (MAE, RMSE, R, Generalization Gap) will be computed programmatically and stored in JSON artifacts; no hand-typed numbers in final reports. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes will be recorded in `state/projects/PROJ-404-predicting-molecular-surface-charge-dist.yaml` upon data download, model save, and split generation. |
| **VI. Computational Numerical Stability** | **PASS** | Plan mandates coordinate normalization to center of mass and float32 precision for all GNN operations. |
| **VII. Structural Generalization Validation** | **PASS** | Data split strategy explicitly uses RDKit Bemis-Murcko scaffolds, not random splitting, to test generalization to unseen topologies. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-surface-charge-dist/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Source of Truth Schemas)
    ├── molecule.schema.yaml
    ├── prediction.schema.yaml
    ├── metrics_report.schema.yaml
    ├── dataset.schema.yaml
    └── training_config.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-404-predicting-molecular-surface-charge-dist/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py          # QM9 ingestion, streaming, schema validation, filtering
│   │   └── splits.py          # Bemis-Murcko scaffold splitting, index persistence
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schnet.py          # Geometric GNN implementation
│   │   └── baseline.py        # Connectivity-only GNN & Atom-Type Average
│   ├── train.py               # Training loop with early stopping & state persistence
│   ├── eval.py                # Evaluation, baseline comparison, metrics, hypothesis check
│   └── utils.py               # Coordinate normalization, logging, memory tracking
├── data/
│   ├── raw/                   # Downloaded parquet files (cached)
│   └── processed/             # Splits, preprocessed tensors, split indices
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_schnet.py     # Architecture init test
│   │   └── test_loader.py     # Schema validation test
│   └── integration/
│       ├── __init__.py
│       ├── test_training.py   # Loop completion & early stopping
│       └── test_eval.py       # Full pipeline & baseline comparison
├── artifacts/
│   ├── models/                # Saved state dicts
│   ├── splits/                # Persisted train/val/test indices
│   └── reports/               # JSON/CSV metrics
├── state/
│   └── projects/PROJ-404-predicting-molecular-surface-charge-dist.yaml  # Artifact hashes
└── README.md
```

**Structure Decision**: The chosen structure separates data loading, filtering, model definition, training, and evaluation into distinct modules to support independent unit testing. The `state/` directory is explicitly included to satisfy Constitution Principle V. The `contracts/` directory is located in `specs/` as the source of truth for schemas.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Scaffold-based Split (vs Random) | Required by Constitution Principle VII to test generalization to unseen topologies. | Random splitting would overestimate performance by leaking structural information between train/test sets. |
| Streaming Data Loading | Required to fit QM9 (or large subsets) within 7 GB RAM. | Loading the full dataset into a pandas DataFrame would likely trigger OOM errors on the free-tier runner. |
| Dual Baseline (2D vs 3D) | Required by US-3 and FR-006 to isolate the contribution of 3D geometry. | A simple atom-type average baseline would not adequately test the "Geometric" hypothesis (requires 2D GNN). |
| Memory Measurement | Required by FR-001 to validate the 7 GB constraint. | Assumption of "fit" is not a validation; explicit measurement is required. |

## Phase Plan

### Phase 0: Data Verification & Strategy
- **T001**: Verify QM9 dataset schema (check for `charges_merkollman` column). **FAIL** if missing.
- **T002**: Estimate theoretical memory footprint of raw data and processed tensors.
- **T003**: Define sampling strategy (if needed) to ensure < 7 GB RAM.

### Phase 1: Data Pipeline & Splitting
- **T011**: Implement `loader.py` with streaming support, schema validation, and filtering logic (atomic).
- **T012**: Implement `splits.py` to compute Bemis-Murcko scaffolds. **Sub-task**: Write split indices to disk (JSON/Parquet) to ensure independent shippability.
- **T013**: Implement `filter.py` logic (integrated into loader) to drop molecules with missing charges/coords.
- **T014**: **Persist Split Indices**: Write train/val/test masks to `artifacts/splits/` (JSON/Parquet) for reproducibility.
- **T015**: Measure and log peak memory usage during data loading.

### Phase 2: Model Implementation
- **T021**: Implement SchNet (3D GNN) with cutoff=5.0 Å, batch size=32.
- **T022**: Implement Connectivity-Only GNN (2D) baseline.
- **T023**: Implement Atom-Type Average baseline.
- **T024**: **Unit Test**: Implement and execute unit tests for SchNet/DimeNet architecture initialization.

### Phase 3: Training & Early Stopping
- **T031**: Implement training loop with Adam (lr=1e-3).
- **T032**: Implement early stopping (patience=10, based on val MAE).
- **T033**: **Persist Early Stopping State**: Save best epoch, best MAE, and final weights to `artifacts/models/`.
- **T034**: Implement memory tracking during training.
- **T035**: **Integration Test**: Implement and execute integration test for training loop completion and early stopping.

### Phase 4: Evaluation & Reporting
- **T041**: Evaluate models on test set.
- **T042**: Calculate MAE, RMSE, Pearson R, and **Generalization Gap** (Train-Val, Val-Test).
- **T043**: Compare 3D GNN vs 2D GNN vs Atom-Type Average.
- **T044**: **Hypothesis Validation**: Check if 3D GNN MAE ≤ 0.05 e AND 3D GNN MAE < Baseline MAE.
- **T046**: **Exit Code Logic**: Exit with `EXIT_CODE_BASELINE_LOSS` if hypothesis not validated. (Depends on T044).
- **T047**: Aggregate metrics.
- **T048**: **Render Final Report**: Generate JSON report with `hypothesis_validated` field. (Depends on T047).
- **T049**: **Integration Test**: Implement and execute integration test for full evaluation pipeline and baseline comparison.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Merz-Kollman columns** | Fatal | T001 verifies schema. If missing, pipeline halts with "Data Unavailable" error. |
| **OOM on Data Loading** | High | Streaming loader (T011) and memory estimation (T002) mitigate this. |
| **Model Convergence Failure** | Medium | Early stopping (T032) and logging. If loss does not decrease, report failure code. |
| **Scaffold Split Imbalance** | Medium | If test set < 100 molecules, report high variance limitation (no fallback to random split). |
| **Runtime > 6h** | High | Monitor training time; if approaching limit, reduce epochs or sample size (pre-defined). |