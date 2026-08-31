# Implementation Plan: Structure-Only Surrogate Model for 2D Material Elastic Moduli

**Branch**: `PROJ-169-surrogate-elastic-moduli` | **Date**: 2026-07-08 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md`

## Summary

This project implements a **Structure-Only Surrogate Model** (GNN) to predict Young's, Shear, and Poisson's ratios for 2D materials. The model acts as a fast interpolator of pre-computed DFT data, avoiding the computational cost of solving the Schrödinger equation. The pipeline ingests [deferred]+ entries from verified HuggingFace DFT datasets, constructs graph representations, trains a lightweight GNN on CPU, and validates inter-family generalization with a strict RMSE/MAPE hard gate.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `torch-geometric`, `pandas`, `pyarrow`, `rdkit`, `scikit-learn`, `networkx`, `datasets`, `pymatgen`, `shap`  
**Storage**: `data/processed/` (Parquet, JSON, Pickle), `data/results/` (JSON logs)  
**Testing**: `pytest` (unit), `pytest-cov`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Data Science / Machine Learning Pipeline  
**Performance Goals**: Inference < 100ms per material; Training < 6 hours; Memory < 7GB peak.  
**Constraints**: CPU-only execution; Single canonical data source per run; No synthetic data generation; Strict constitutional compliance (Surrogate vs. First-Principles).  
**Scale/Scope**: [deferred] material entries; 3 target properties.

> All dataset URLs are restricted to the verified list in `research.md`. No access-gated data (e.g., Materials Project API requiring keys) is permitted.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: Random seeds pinned in `code/utils/seeds.py`. External datasets fetched via `datasets.load_dataset` with pinned version hashes.
2.  **II. Verified Accuracy**: All citations in `research.md` and `data-model.md` restricted to verified URLs. No fabricated dataset links.
3.  **III. Data Hygiene**: `data/` files checksummed in `state/`. Raw data preserved; derivations written to new files (e.g., `graphs_v1.parquet`).
4.  **IV. Single Source of Truth**: All figures/metrics trace to `data/results/*.json` and `code/`.
5.  **V. Versioning Discipline**: Artifacts carry content hashes. `state` file updated on artifact change.
6.  **VI. Numerical Stability**: Elastic moduli derived *exclusively* from elastic tensor via continuum mechanics in `code/physics/tensors.py`. No hard-coded values.
7.  **VII. Structural Descriptor Attribution**: Feature importance via SHAP (with interaction values) on the final GNN.

**Critical Correction**: The Constitution title "First-Principles Calculations" is explicitly contradicted by the Spec. 
- **Violated Principles**: Principle I (SSoT) and Principle VI (Numerical Stability) are violated if the title remains "First-Principles".
- **Action**: Task T060b will update the Constitution title. Task T060c will verify the update. 
- **Hard Gate**: All subsequent tasks (T004, T013d1, etc.) depend on T060c. If T060c fails, the pipeline exits with code 1.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-169-surrogate-elastic-moduli/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/
├── code/
│   ├── utils/
│   │   ├── seeds.py                 # Random seed pinning
│   │   ├── disclaimer_template.py   # Feynman quote & scientific integrity statement
│   │   └── verify_constitution_title.py # T060c: Hard gate validator
│   ├── physics/
│   │   └── tensors.py               # Elastic tensor -> Moduli conversion (VI)
│   ├── data/
│   │   ├── loader.py                # HuggingFace dataset ingestion (Single Source)
│   │   ├── graph_builder.py         # CIF/Structure -> Graph conversion (PBC aware)
│   │   └── splitter.py              # T017b: Inter-family stratified split
│   ├── model/
│   │   ├── gnn.py                   # Lightweight GNN architecture
│   │   ├── train.py                 # T018b: Training loop, memory profiling, CPU enforcement
│   │   └── eval_runner.py           # Evaluation, MAPE calculation, disclaimer injection
│   └── analysis/
│       └── feature_importance.py    # T003: SHAP with interaction values
├── data/
│   ├── raw/                         # Downloaded parquet (checksummed)
│   ├── processed/
│   │   ├── graphs_v1.parquet        # T013d4
│   │   ├── split_indices.json       # T013f
│   │   └── model_v1.pt              # T018b
│   └── results/
│       ├── training_logs.json       # T002
│       ├── generalization_metrics.json # T003, T021b
│       ├── feature_importance_report.md # T003
│       ├── constitution_title_audit.json # T060c
│       └── inference_benchmark.json # T022
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

**Structure Decision**: Single project structure. All data and code paths are explicitly defined to ensure reproducibility and strict dependency ordering (Data -> Split -> Train -> Eval -> Audit).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Hard Gate on Constitution Title (T060c) | Prevents "First-Principles" misclassification which violates Spec & Reviewer feedback. | Removing the gate risks propagating a fundamental scientific error. |
| Inter-Family Stratified Split (T017b) | Required for SC-002 (generalization to unseen families). | Random split would allow family-specific memorization. |
| CPU-Only Enforcement | GitHub Actions free tier has no GPU. | Using GPU-specific code without a fallback would cause CI failure. |
| SHAP over Permutation | Handles collinearity in structural descriptors. | Permutation importance is unstable with correlated features. |
| PBC-Aware Graph Builder | 2D materials require periodic boundary conditions. | Fixed cutoff without PBC creates incorrect connectivity. |

## Tasks

### Phase 0: Setup & Constitution
- [X] T001a: Initialize repository structure.
- [X] T001b: Create initial `state/...yaml`.
- [ ] T060b: Update Constitution Title (Edit `constitution.md` title to "Structure-Only Surrogate Model").
- [ ] T060c: Verify Constitution Title (Run `verify_constitution_title.py`; exit code 1 if FAIL; write `constitution_title_audit.json`). **HARD GATE**.
  - *Dependencies*: T060b.
  - *Downstream Dependencies*: T004, T013d1, T013d0_impl, T017b, T018b, T021b, T022, T003, T008a, T001c.

### Phase 1: Data Pipeline (US1)
- [ ] T013d0_define: Define data loading interfaces.
- [ ] T013d1: Download verified dataset (`matbench/elasticity` or equivalent). Validate schema (elastic_tensor, structure). Checksum file.
- [ ] T013d0_validation: Verify row count > 1,000. Exit code 1 if fail.
- [ ] T013d2: Parse structures (Pymatgen).
- [ ] T013d3: Generate graphs (PBC-aware, adaptive cutoff).
- [ ] T013d4: Save `graphs_v1.parquet`. Record Python version and pickle protocol in `state/...yaml`.
- [ ] T013f: Generate `split_indices.json` (Inter-family by Space Group + Chemical Motif).
- [ ] T017b: Validate Stratified Split. Write `split_validation.json`.

### Phase 2: Model Training (US2)
- [ ] T016: Define loss function (Weighted/Normalized MSE for Young/Shear/Poisson).
- [ ] T018c-def: Define GNN architecture (2-3 layers, hidden dim <= 64).
- [ ] T018c-impl: Implement training loop with `tracemalloc` for memory profiling.
- [ ] T018b: Train model. Save `model_v1.pt`, `training_logs.json` (include `peak_memory_gb`, `memory_limit_exceeded` boolean). **Hard Gate**: Exit code 1 if `peak_memory_gb` > 7.0.
- [ ] T022: Inference Benchmark. Measure time per material. Save `inference_benchmark.json`. **Hard Gate**: Exit code 1 if > 100ms.

### Phase 3: Evaluation & Analysis (US3)
- [ ] Tb: Inter-Family Validation. Compute RMSE and MAPE on test families. Compute 95% CI for MAPE.
  - *Hard Gate*: Exit code 1 if RMSE > threshold OR (MAPE > 15% AND Lower CI Bound > 15%).
  - *Output*: `generalization_metrics.json`.
- [ ] T003: Feature Importance. Run SHAP with interaction values. Identify >= 3 descriptors with p < 0.05.
  - *Hard Gate*: Exit code 1 if < 3 descriptors found.
  - *Output*: `feature_importance_report.md`.

### Phase 4: Finalization
- [ ] T001c: Compute and Record Artifact Hashes (Run after US1/US2).
- [ ] T008a: Implement integration test (Run after US1/US2).
- [ ] T057: Final Title Audit.

## Reproducibility Notes
- **Streaming**: `datasets.load_dataset(..., streaming=True)` used to manage memory.
- **Sampling**: If metadata index > 7GB, fallback to random sample of [deferred] rows (log power limitation).
- **PBC**: `pymatgen` used for structure parsing with periodic boundary conditions enabled.
- **Collinearity**: SHAP with interaction values used to disentangle correlated structural descriptors.
- **Ground Truth**: All validation is against DFT-derived values. Claims are framed as "surrogate accuracy relative to DFT".