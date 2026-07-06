# Implementation Plan: Predicting Molecular Permeability of Polymers via Graph Neural Networks

**Branch**: `001-predicting-molecular-permeability` | **Date**: 2026-06-27 | **Spec**: `specs/001-predicting-molecular-permeability/spec.md`

## Summary

This project implements a computational pipeline to predict the gas permeability of polymers using Graph Neural Networks (GNNs). The approach converts polymer SMILES strings into graph representations (nodes: atoms, edges: bonds) and trains a message-passing network to predict log-transformed permeability coefficients. 

**Critical Scope Limitation**: The verified datasets block does not contain a source for experimental polymer permeability data (e.g., NIST). Consequently, the project **cannot** validate the hypothesis against real experimental ground truth. Instead, the project scope is redefined to:
1.  Validate the *methodology* (graph construction, GNN training, statistical tests) using a high-fidelity physics-based simulation (**PolyPerme**) that generates permeability from free-volume and chain dynamics.
2.  Explicitly document that real-world experimental validation is blocked pending the acquisition of a verified NIST permeability dataset.
3.  Compare the GNN against a Random Forest baseline and a **Randomized Topology Control** to ensure the model learns graph structure, not just atomic composition.

The implementation adheres to strict CPU-only constraints (GitHub Actions free tier) and rigorous statistical validation (Wilcoxon signed-rank test, VIF analysis).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit` (chemistry), `torch` (CPU-only), `scikit-learn`, `pandas`, `numpy`, `networkx`  
**Storage**: Local HDF5/Parquet files for processed data; JSON artifacts for model metrics.  
**Testing**: `pytest` for unit tests on graph construction and data splits; integration tests for full pipeline execution.  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7 GB RAM).  
**Project Type**: Computational Chemistry / Machine Learning Library (Methodology Validation).  
**Performance Goals**: Full training and evaluation pipeline must complete within 6 hours on CPU.  
**Constraints**: No GPU, no mixed-precision training, no large-LLM inference. Data must be subset to fit available system memory.

The research question, method, and references remain unchanged as no specific empirical values were asserted in the original passage beyond the memory constraint, which has now been generalized.  
**Scale/Scope**: Dataset size capped at a feasible scale (selected deterministically) for feasibility; K-fold cross-validation.

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action Required / Traceability |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`. External predictor source (PubChem) is verified. Target source is simulation (documented). |
| **II. Verified Accuracy** | **Partial Compliance** | Predictor source (PubChem SMILES) is verified. Target source (Permeability) is **not** verified (simulation used). See `research.md` Section 2.1 for gap analysis. |
| **III. Data Hygiene** | **Compliant** | Raw data checksums recorded; transformations produce new files. No in-place modification. |
| **IV. Single Source of Truth** | **Compliant** | All metrics in `plan.md` and `research.md` will trace to generated artifacts, not hand-typed values. |
| **V. Versioning Discipline** | **Compliant** | Content hashes tracked; `updated_at` timestamps managed by the system. |
| **VI. Graph Representation Fidelity** | **Compliant** | RDKit version pinned in `code/requirements.txt`. Node/edge features strictly defined in `code/data/preprocessing.py`. |
| **VII. Scaffold-Aware Validation** | **Compliant** | Murcko scaffold splits implemented in `code/data/preprocessing.py`. Random splits prohibited. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-permeability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
projects/PROJ-512-predicting-molecular-permeability-of-pol/code/
├── data/
│   ├── ingestion.py          # Load PubChem SMILES, generate PolyPerme target (FR-001)
│   ├── preprocessing.py      # Scaffold split, graph construction, feature extraction (FR-002)
│   └── utils.py              # Logging, checksumming, seed setting
├── models/
│   ├── gnn.py                # Message-passing GNN (multiple layers, 64 dims) (FR-003)
│   ├── baselines.py          # Random Forest (ECFP4), Linear Regression, Randomized Topology (FR-004)
│   └── trainer.py            # Training loop, gradient clipping, early stopping
├── evaluation/
│   ├── metrics.py            # R², MAE, Pearson correlation
│   ├── stats.py              # Wilcoxon test, VIF calculation, sensitivity analysis (FR-005, FR-006, FR-007)
│   └── report.py             # JSON report generation
├── main.py                   # Orchestration script
└── requirements.txt          # Pinned dependencies
```

**Structure Decision**: Single-project structure chosen to minimize overhead and ensure tight coupling between data ingestion, model training, and evaluation on a constrained CI environment. The `code/` directory contains all logic; `data/` is for intermediate artifacts.

## Complexity Tracking

No violations detected. The scope is tightly constrained by the CPU-only environment and the specific requirement to compare GNNs against simpler baselines on a scaffold-split dataset. The complexity is managed by:
1. Limiting GNN depth to a shallow range.
2. Capping dataset size to ensure RAM compliance.
3. Using standard float32 precision.
4. Using a deterministic selection rule for data subsetting.