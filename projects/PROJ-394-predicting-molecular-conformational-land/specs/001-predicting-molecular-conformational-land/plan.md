# Implementation Plan: Predicting Molecular Conformational Landscapes with Variational Autoencoders

**Branch**: `001-predict-conformer-vae` | **Date**: 2026-06-25 | **Spec**: `specs/001-predict-conformer-vae/spec.md`
**Input**: Feature specification from `specs/001-predict-conformer-vae/spec.md`

## Summary

This project implements a computational pipeline to investigate the relationship between 2D molecular topology and low-energy conformational landscapes. The core approach involves training a Graph Variational Autoencoder (VAE) on 2D molecular graphs (derived from SMILES) to learn a latent representation. This latent vector is then used, via a linear regression head, to predict the relative energy rankings of conformers generated and optimized using GFN2-xTB. The system validates the hypothesis that 2D structural features contain sufficient information to *approximate* the output of a standard 2D->3D conformational search pipeline (ETKDG + GFN2-xTB).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU-only), RDKit, xtb (GFN2-xTB), scikit-learn, statsmodels, pandas, numpy, huggingface-datasets, joblib  
**Storage**: Local file system (CSV, Parquet, PT checkpoints, JSON logs)  
**Testing**: pytest (unit tests for data loading, model inference; integration tests for full pipeline)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free tier: CPU, ~7 GB RAM)  
**Project Type**: Computational chemistry research pipeline / CLI  
**Performance Goals**: Complete full training and evaluation on [deferred] test molecules (plus [deferred] training) within 6 hours on CPU.
**Constraints**: No GPU/CUDA; GFN2-xTB must be invoked via subprocess with parallelization; memory usage < 7 GB; strict reproducibility (seeds, checksums).  
**Scale/Scope**: Training on ZINC15 subset (≥5,000 molecules, 10 conformers each); Evaluation on held-out set (≥1,000 molecules, 20 conformers each).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, fixed `requirements.txt` (including xtb version), and immutable data checksums. |
| **II. Verified Accuracy** | **PASS** | All citations (e.g., GFN-xTB, ZINC15 source) are mapped to verified URLs in `research.md`. No hallucinated sources. |
| **III. Data Hygiene** | **PASS** | Raw data (ZINC15) downloaded once, checksummed. Derived data (conformer energies) stored as new files with derivation logs. |
| **IV. Single Source of Truth** | **PASS** | All metrics (Spearman ρ, p-values) derived programmatically from `data/` artifacts and logged in `code/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts (checkpoints, datasets) will be hashed; state file updated on change. |
| **VI. Computational Chemistry Reproducibility** | **PASS** | GFN2-xTB version and command-line flags (convergence criteria) will be recorded in `requirements.txt` and `data/calculation_metadata` in `molecule.schema.yaml`. |
| **VII. Model Evaluation Transparency** | **PASS** | Full statistical summaries (ρ, p-value, CI) reported for every test molecule; seeds logged. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-conformer-vae/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (molecule.schema.yaml, metrics.schema.yaml)
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-394-predicting-molecular-conformational-land/
├── code/
│   ├── __init__.py
│   ├── requirements.txt       # Pinned deps: torch, rdkit, xtb, joblib, etc.
│   ├── data/
│   │   ├── download_zinc.py   # Fetches from verified HuggingFace URL
│   │   ├── preprocess.py      # SMILES -> Graph, conformer gen (parallelized)
│   │   └── energy_calc.py     # GFN2-xTB wrapper (parallelized)
│   ├── models/
│   │   ├── vae.py             # MPNN Encoder/Decoder
│   │   └── linear_head.py     # Regression head
│   ├── train.py               # Training loop (CPU): VAE then Head
│   ├── evaluate.py            # Spearman correlation, baselines, ablations
│   ├── utils/
│   │   ├── seeds.py           # Global seed setting
│   │   └── logging.py         # Structured logging
│   └── main.py                # CLI entry point
├── data/
│   ├── raw/                   # Downloaded ZINC15 parquet
│   ├── processed/             # Graphs, conformers, energies
│   └── checksums.json         # Artifact hashes
├── tests/
│   ├── unit/
│   │   ├── test_vae.py
│   │   └── test_data_loader.py
│   └── integration/
│       └── test_full_pipeline.py
└── docs/
    └── constitution.md        # Copy of project constitution
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) is selected. This aligns with the computational chemistry nature of the project, where data processing, model training, and evaluation are tightly coupled and run sequentially in a single environment. Separating into microservices is unnecessary and would complicate the CPU-bound, sequential workflow (generate conformers -> optimize -> train VAE -> evaluate).

## Complexity Tracking

*No violations detected. The complexity is managed by strict adherence to CPU constraints, parallelization (joblib), and reduced conformer counts for training.*

## FR/SC Coverage Map

| Requirement | Plan Phase/Step | Contract Reference |
|-------------|-----------------|-------------------|
| **FR-001** (Ingest SMILES, RDKit Graphs) | `data/preprocess.py`: `smiles_to_graph` function. | `contracts/molecule.schema.yaml` |
| **FR-002** (Train VAE on CPU) | `train.py`: CPU-only training loop, checkpoint saving. | `contracts/molecule.schema.yaml` (latent_vector) |
| **FR-003** (Encode to a fixed-dimensional representation.) | `models/vae.py`: `encode` method returns 64-dim vector. | `contracts/molecule.schema.yaml` |
| **FR-004** (Conformer Gen + GFN2-xTB) | `data/energy_calc.py`: ETKDG generation + `xtb` subprocess call (parallelized). | `contracts/molecule.schema.yaml` (conformers, calculation_metadata) |
| **FR-005** (Spearman ρ) | `evaluate.py`: `compute_spearman` function (Mixed-Effects/Permutation). | `contracts/metrics.schema.yaml` |
| **FR-006** (Baselines: Fingerprint, Random) | `evaluate.py`: `run_baselines` function. | `contracts/metrics.schema.yaml` |
| **FR-007** (Ablation: 3D Descriptors) | `evaluate.py`: `run_ablation` function (using independent 3D generation). | `contracts/metrics.schema.yaml` |
| **FR-008** (Bonferroni Correction) | *Replaced by Mixed-Effects Model* (see research.md). | `contracts/metrics.schema.yaml` |
| **FR-009** (Associative Claims) | `evaluate.py`: Output formatting; `research.md` text. | N/A |
| **FR-010** (Sensitivity Analysis) | `evaluate.py`: Loop over α ∈ {low, moderate, high significance levels}. | `contracts/metrics.schema.yaml` |
| **FR-011** ([deferred] Workflow Success) | `data/energy_calc.py`: Error handling, logging, success rate metric. | `contracts/metrics.schema.yaml` (workflow_success_rate) |
| **FR-012** (Power Analysis) | `evaluate.py`: `power_analysis` function using `statsmodels`. | `contracts/metrics.schema.yaml` |
| **SC-001** (ρ ≥ 0.5, p < 0.05) | `evaluate.py`: Assertion checks, report generation. | `contracts/metrics.schema.yaml` |
| **SC-002** (Baseline ρ ≤ 0.3) | `evaluate.py`: Comparative report. | `contracts/metrics.schema.yaml` |
| **SC-003** (Sensitivity stability) | `evaluate.py`: Δp-value calculation. | `contracts/metrics.schema.yaml` |
| **SC-004** (Ablation Δρ ≤ 0.1) | `evaluate.py`: Δρ calculation. | `contracts/metrics.schema.yaml` |
| **SC-005** (6h Runtime) | `plan.md` constraints; `train.py` optimization; parallelized `energy_calc.py`. | N/A |

## Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, No GPU).
*   **Strategy**:
    *   **Parallelization**: `joblib` with `n_jobs=2` for conformer generation and energy calculation.
 * **Training Set**: [deferred] molecules, 10 conformers each (single-point GFN2-xTB).
 * **Test Set**: [deferred] molecules, 20 conformers each (multi-start GFN2-xTB).
    *   **VAE**: Small architecture (MPNN, 64-dim latent). Training on CPU using `torch.set_num_threads` with a restricted thread count to limit parallelism.. Batch size tuned to fit RAM.
    *   **Time Budget**:
        *   Data Download: min
        *   Conformer Gen/Energy (Train): A moderate duration
        *   Conformer Gen/Energy (Test): Estimated duration based on computational complexity and resource availability.
        *   VAE Training: hours
        *   Evaluation: A brief duration
 * **Total**: [deferred] (within 6h limit).

## Response to Reviewer (rosalind-franklin-simulated)

The reviewer suggested appending a validation section comparing autoencoder-generated conformers to X-ray diffraction patterns.
*   **Feasibility**: The project scope is defined by the spec as investigating the **relationship between 2D topology and low-energy conformers** (predicted via GFN2-xTB). Incorporating X-ray diffraction validation for a large set of small organic molecules is **outside the scope** of the current computational pipeline and the 6-hour CPU constraint. X-ray data is typically available only for specific crystal structures, not for arbitrary conformers of random small molecules in a dataset like ZINC15.
*   **Action**: The plan will **not** implement a diffraction validation step for the entire dataset as it is not feasible within the constraints and would require a different dataset (crystallographic data).
*   **Mitigation**: The plan explicitly states that the **reference standard** is GFN2-xTB (a physics-based method), not experimental data. The "Validation" in this context refers to the internal consistency of the GFN2-xTB workflow (convergence rates) and the statistical significance of the correlation. The plan will add a note in `research.md` acknowledging that while experimental validation is the ultimate goal, this study focuses on the **computational feasibility** of predicting relative rankings using 2D topology, validated against a rigorous physics-based baseline (GFN2-xTB).