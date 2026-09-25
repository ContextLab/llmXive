# Implementation Plan: Investigating the Effectiveness of Loss Functions on Small-World Graphs

**Branch**: `353-loss-functions-small-world` | **Date**: 2026-06-25 | **Spec**: `specs/353-loss-functions-small-world/spec.md`
**Input**: Feature specification from `/specs/353-loss-functions-small-world/spec.md`

## Summary

This project investigates whether contrastive learning (InfoNCE) converges faster than supervised learning (Cross-Entropy) as graph connectivity ($\beta$) increases in Watts-Strogatz small-world networks. The technical approach involves generating A set of synthetic graphs (10 per $\beta$ level from 0.0 to 1.0), training Graph Convolutional Networks (GCNs) with both loss functions, and measuring two primary metrics: (1) **Time-to-Threshold** (epochs to reach $\ge$ 0.90 accuracy via a linear probe) analyzed using Tobit Regression and Cox Proportional Hazards, and (2) **Accuracy at Fixed Epochs** (e.g., epoch 100, 500) to assess optimization efficiency independent of a binary threshold.

**Note on Effectiveness**: "Effectiveness" is defined as a combination of convergence speed and final representation quality. Slower convergence to 0.90 does not imply inferiority if the model achieves higher final accuracy or better generalization.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `networkx` (graph generation), `torch` (GCN implementation), `scikit-learn` (data handling), `lifelines` (Tobit/Cox analysis), `pandas`, `numpy`
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `artifacts/`)
**Testing**: `pytest` (unit tests for graph generation, convergence logic, schema validation)
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7GB RAM)
**Project Type**: Computational research / simulation
**Performance Goals**: Complete 220 training runs (110 graphs $\times$ 2 losses) within 6 hours; each run < 15 minutes.
**Constraints**: 
- Must run on CPU-first (no local GPU); GPU offload to Kaggle only if specific CUDA kernels are required (unlikely for small GCNs).
- Strict random seed pinning for reproducibility (Constitution Principle I).
- No external datasets; all data is synthetic and generated deterministically.
- Convergence threshold fixed at $\ge$ 0.90 (FR-005).
- Sample size fixed at N=110 (FR-001).
- **Power Limitation**: The study is underpowered to definitively detect small interaction effects. Non-significant results will be interpreted as "inconclusive due to low power" rather than definitive negatives.
- **Structural Solvability**: High $\beta$ levels may destroy community structure, making 0.90 accuracy theoretically impossible. Non-convergence is a valid outcome reflecting structural limits, not just optimization failure.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Note |
|-----------|--------|-------------------|
| I. Reproducibility | **PASS** | Random seeds pinned in `code/generate_graphs.py` and `code/train.py`. `requirements.txt` will pin exact versions. No external mutable data sources. |
| II. Verified Accuracy | **PASS** | No external citations required for synthetic graph theory (Watts-Strogatz) or standard statistical methods (Tobit/Cox). All methods are standard library/implementation. |
| III. Data Hygiene | **PASS** | `data/raw/graphs.jsonl` generated once, checksummed. No in-place modifications. Derived files (`convergence_logs.csv`, `analysis_results.json`) have distinct names. |
| IV. Single Source of Truth | **PASS** | All results in `data/analysis_results.json` derived strictly from `code/analysis.py` reading `data/processed/convergence_logs.csv`. |
| V. Versioning Discipline | **PASS** | Artifacts will be tracked via content hashes in `state/`. `code/` scripts will output their own version hash. |
| VI. Optimization Dynamics Tracking | **PASS** | `code/train.py` will log per-epoch accuracy and loss to `data/processed/trajectories/`. Convergence step recorded as first epoch $\ge$ 0.90. Fixed-epoch accuracy also recorded. |
| VII. Synthetic Topology Parameterization | **PASS** | `code/generate_graphs.py` will log `rewiring_probability_beta` and `clustering_coefficient` in every graph record metadata. |

## Project Structure

### Documentation (this feature)

```text
specs/353-loss-functions-small-world/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── graph.schema.yaml
    ├── training_run.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-353-investigating-the-effectiveness-of-diffe/
├── code/
│   ├── __init__.py
│   ├── generate_graphs.py       # US-1: Watts-Strogatz generation
│   ├── train.py                 # US-2: GCN training loop (CE + InfoNCE + Linear Probe)
│   ├── analysis.py              # US-3: Tobit/Cox/Fixed-Epoch analysis
│   └── utils.py                 # Seed management, logging helpers
├── data/
│   ├── raw/
│   │   └── graphs.jsonl         # 110 synthetic graphs
│   ├── processed/
│   │   ├── convergence_logs.csv # Training metrics per run
│   │   └── trajectories/        # Per-epoch logs
│   └── analysis_results.json    # Final output (SC-003)
├── tests/
│   ├── test_graph_generation.py
│   ├── test_convergence_logic.py
│   └── test_schema_validation.py
├── requirements.txt
├── .flake8
└── pyproject.toml               # Black configuration
```

**Structure Decision**: Single-project structure selected. All code resides in `code/` for direct execution by the GitHub Actions runner. No separate backend/frontend. Data is local files to avoid network latency and authentication issues.

## Complexity Tracking

No violations detected. The project is a self-contained simulation with deterministic data generation and standard statistical analysis.