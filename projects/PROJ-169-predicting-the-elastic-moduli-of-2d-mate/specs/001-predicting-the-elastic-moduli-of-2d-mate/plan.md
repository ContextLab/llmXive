# Implementation Plan: Predicting the Elastic Moduli of 2D Materials from Structure-Only Models

**Branch**: `001-predicting-elastic-moduli` | **Date**: 2026-07-09 | **Spec**: `specs/001-predicting-the-elastic-moduli/spec.md`
**Input**: Feature specification from `specs/001-predicting-the-elastic-moduli/spec.md`

## Summary

This project develops a lightweight Graph Neural Network (GNN) surrogate model to predict the elastic moduli (Young's, Shear, and Poisson's ratio) of 2D materials using **structure-only** descriptors derived from CIF files. The approach explicitly avoids solving the Schrödinger equation (first-principles) during inference, instead learning structure-property mappings from DFT-calculated ground truths stored in public repositories. The pipeline strictly adheres to a compute budget of 6 hours on a 2-core CPU runner with ≤7GB RAM, utilizing CPU-tractable libraries (`pymatgen`, `torch-geometric`, `scikit-learn`) and sampled datasets.

**Critical Note on Physical Validity**: This study tests the hypothesis that structural descriptors alone are sufficient to approximate DFT-calculated elastic moduli. It acknowledges that electronic structure effects (d-orbital hybridization, charge transfer) are likely primary drivers of elasticity in 2D materials. Therefore, the model's performance is interpreted as a measure of **descriptor sufficiency** rather than a discovery of new physical laws. A performance drop in inter-family splits is explicitly framed as evidence of missing electronic information, not model failure.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen`, `torch` (CPU-only), `torch-geometric`, `scikit-learn`, `pandas`, `networkx`, `shap`  
**Storage**: Local CSV/JSON artifacts in `data/` (derived from unified verified sources)  
**Testing**: `pytest` for unit tests; integration tests verify end-to-end pipeline on sampled data.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7GB RAM, No GPU)  
**Project Type**: Data Science / Machine Learning Research Pipeline  
**Performance Goals**: Total runtime ≤6h; Peak RAM ≤7GB; Model convergence via **Early Stopping** (patience=3 epochs) on validation loss.  
**Constraints**: No GPU usage; No deep learning frameworks requiring CUDA; Strict separation of training and test material families.  
**Scale/Scope**: Dataset limited to verified 2D materials with complete elastic tensors. **Final sample size is contingent on the availability of a unified data source** (see `research.md` for Data Availability Gate). The specific target range of 500-2000 samples is **deferred** pending verification of the unified source.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; Data fetched from canonical verified URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | Citations restricted to verified unified source; No fabricated dataset links. |
| **III. Data Hygiene** | PASS | Raw data checksummed; Derivations written to new files; No in-place modification. |
| **IV. Single Source of Truth** | PASS | All metrics traced to `data/` CSVs; No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in state YAML; `updated_at` updated on artifact change. |
| **VI. Numerical Stability & DFT Fidelity** | PASS (Conditional) | Elastic tensors derived strictly from DFT ground truth; Predictions via continuum mechanics relations in code; **Primary success metric is Inter-Family MAPE** (contingent on execution of inter-family split). |
| **VII. Structural Descriptor Attribution** | PASS | SHAP interaction values computed for all claims; Generalization tested on unseen families; Joint contribution reported for correlated features. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-elastic-moduli/
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
├── data/
│   ├── raw/                 # Downloaded parquet/cif files (checksummed)
│   ├── processed/           # Graph representations (JSON/CSV)
│   ├── filtered/            # Final dataset after bias check & filtering
│   └── splits/              # Train/val/test indices
├── code/
│   ├── requirements.txt     # Pinned dependencies
│   ├── ingest/
│   │   ├── download.py      # Unified dataset loader
│   │   ├── parse_cif.py     # CIF -> Graph conversion (pymatgen)
│   │   ├── filter.py        # 2D & Elastic Tensor completeness filter
│   │   └── bias_check.py    # Bias detection for excluded entries
│   ├── model/
│   │   ├── gnn.py           # Lightweight GNN definition
│   │   ├── train.py         # Training loop (CPU, Early Stopping)
│   │   └── eval.py          # Metrics & Cross-validation
│   ├── analysis/
│   │   ├── importance.py    # SHAP Interaction & Permutation importance
│   │   └── ablation.py      # Composition-only baseline
│   └── utils/
│       ├── constants.py     # Physical constants, conversion factors
│       └── metrics.py       # MAPE, RMSE, R² calculators
├── tests/
│   ├── unit/
│   │   ├── test_parse_cif.py
│   │   └── test_metrics.py
│   └── integration/
│       └── test_pipeline.py
└── paper/
    └── figures/             # Generated plots (SHAP, Parity)
```

**Structure Decision**: Chosen a modular `code/` structure separating `ingest`, `model`, and `analysis` to ensure reproducibility and testability. This aligns with the Constitution's requirement for isolated virtualenvs and end-to-end runnable scripts.

## Complexity Tracking

No violations identified. The complexity is managed by strict adherence to CPU-only constraints, pre-filtered datasets, and a unified data source to avoid join biases. The "Early Stopping" strategy replaces arbitrary epoch limits to ensure convergence without overfitting.