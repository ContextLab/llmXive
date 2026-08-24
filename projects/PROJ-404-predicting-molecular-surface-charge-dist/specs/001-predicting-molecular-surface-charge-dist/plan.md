# Implementation Plan: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

**Branch**: `001-predict-molecular-surface-charge` | **Date**: 2026-08-24 | **Spec**: `specs/001-predicting-molecular-surface-charge/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-surface-charge/spec.md`

## Summary

The project implements a Geometric Message Passing Neural Network (GNN) to predict atomic partial charges (ESP-derived, specifically Merz-Kollman or equivalent) from molecular geometries, using the QM9 dataset. The system prioritizes CPU-only execution on a GitHub Actions free-tier runner with constrained resources, enforcing strict memory constraints via dynamic memory profiling and adaptive sampling.

**Core Hypothesis**: Specific 3D conformations (beyond the average geometry implied by topology) provide predictive power for charge distribution. The model is tested on its ability to predict *deviations* from the topological mean.

**Validation Strategy**: The hypothesis is validated through a three-tier baseline comparison:
1.  **Atom-Type Average**: Measures the baseline performance of chemical intuition (no topology/geometry).
2.  **Connectivity-Only GNN (2D)**: Measures the contribution of topology (bond graph).
3.  **Coordinate-Randomized GNN**: An ablation where 3D coordinates are shuffled per molecule while preserving connectivity. This isolates the signal of *specific* geometry from *topology*.

The 3D GNN must outperform the Coordinate-Randomized GNN to confirm it learns specific geometric context, and outperform the 2D GNN to confirm geometry adds value beyond connectivity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU version), PyTorch Geometric, RDKit, Hugging Face `datasets`, `scikit-learn`, `pandas`, `numpy`, `statsmodels` (for power analysis)  
**Storage**: Local file system (temporary artifacts), GitHub Actions ephemeral storage  
**Testing**: `pytest` (unit tests for data loaders, integration tests for training loops)  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Project Type**: Computational Research / Machine Learning Pipeline  
**Performance Goals**: 
- Data load time < 10 minutes (for sampled set)
- Training < 6 hours (10 epochs minimum)
- Peak RAM < 7 GB (adaptive)
- Model size < 500 MB
**Constraints**: 
- CPU-only execution (no local GPU)
- No external API calls requiring credentials (public datasets only)
- Strict memory management (streaming/sampling)
**Scale/Scope**: 
- Dataset: QM (sampled to fit RAM, target a large-scale collection of molecules, adaptive)
- Model: SchNet (small architecture)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

**Principle I: Reproducibility**
- **Status**: COMPLIANT
- **Action**: All random seeds will be pinned in `code/`. Datasets will be fetched via programmatic loaders (`datasets.load_dataset`) from verified Hugging Face URLs. `requirements.txt` will pin all versions.

**Principle II: Verified Accuracy**
- **Status**: COMPLIANT
- **Action**: Citations in `research.md` strictly use the URLs provided in the `# Verified datasets` block. No external URLs will be invented. The dataset schema is verified against the column definitions in the research document.

**Principle III: Data Hygiene**
- **Status**: COMPLIANT
- **Action**: Raw data will be loaded from Hugging Face. Derived data (processed tensors, splits) will be stored in `data/processed/` with checksums recorded in the project state YAML. No in-place modification of raw files.

**Principle IV: Single Source of Truth**
- **Status**: COMPLIANT
- **Action**: All metrics (MAE, RMSE, R) in the final report will be generated programmatically from the evaluation script output, not hand-entered.

**Principle V: Versioning Discipline**
- **Status**: COMPLIANT
- **Action**: Artifacts (models, processed data) will be hashed. The `updated_at` timestamp in the project state will be updated upon any code/data change.

**Principle VI: Computational Numerical Stability**
- **Status**: COMPLIANT
- **Action**: 3D coordinates will be normalized to the center of mass before model input. All floating-point operations will use `float32` to match the DFT ground truth precision context.

**Principle VII: Structural Generalization Validation**
- **Status**: COMPLIANT
- **Action**: The data split will use Bemis-Murcko scaffolds (via RDKit) with a fixed random seed, ensuring the test set contains unseen topologies. **Crucially**, the baseline hierarchy includes an **Atom-Type Average** baseline as the primary comparator for topology contribution, and a **Connectivity GNN** as the secondary comparator, satisfying the constitutional mandate.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-surface-charge/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-404-predicting-molecular-surface-charge-dist/
├── data/
│   ├── raw/             # Downloaded parquet files (symbolic links or direct download)
│   └── processed/       # Scaffolds, splits, normalized tensors
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py    # HuggingFace dataset loading & streaming + Memory Profiling
│   │   ├── preprocess.py # Coordinate normalization, scaffold splitting, Coordinate Randomization
│   │   └── dataset.py   # PyTorch Dataset wrapper
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schnet.py    # Geometric GNN implementation
│   │   ├── baseline_2d.py # Connectivity-only GNN
│   │   └── baseline_atom.py # Atom-Type Average baseline
│   ├── train.py         # Training loop with early stopping
│   ├── eval.py          # Evaluation, metrics, baseline comparison, Power Analysis
│   └── utils.py         # Logging, seed setting
├── tests/
│   ├── test_loader.py
│   ├── test_preprocess.py
│   └── test_model.py
└── reports/
    └── results.md       # Final metrics output
```

**Structure Decision**: A modular Python package structure is selected to separate data ingestion, model definition, and training logic. This supports unit testing of individual components (e.g., coordinate normalization) and ensures the training loop can be run independently. The `data/` directory is split into `raw` (source) and `processed` (derived) to enforce data hygiene.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Three-Tier Baseline (Atom-Type, 2D-GNN, 3D-GNN)** | Required by Constitution Principle VII and Methodological Rigor to isolate the marginal gain of topology vs. specific geometry. | A single 2D GNN baseline cannot distinguish between "topology matters" and "3D geometry matters". An Atom-Type baseline is required to quantify the topological contribution. |
| **Coordinate Randomization Ablation** | Required to isolate the signal of specific 3D geometry from the signal of topology. | Without this, the 3D GNN might just be learning the "average geometry" associated with the topology, which the 2D GNN also implicitly learns. |
| **Scaffold-based split (vs Random)** | Required by Constitution Principle VII and Spec FR-004 to test generalization to unseen topologies. | Random splitting would likely leak scaffold information between train/test, invalidating the hypothesis test regarding 3D geometry's unique contribution. |
| **Memory Profiling & Adaptive Sampling** | Required by Spec FR-001 and SC-005 to fit QM (~10^5 molecules) into 7 GB RAM on CPU. | Loading the full dataset into memory would trigger OOM errors. A fixed sample size is risky; dynamic profiling ensures we stay under the limit. |
| **Post-hoc Power Analysis** | Required to ensure the sample size is sufficient to detect the expected effect size. | A null result without power analysis is inconclusive (could be underpowered). |

## Memory Feasibility Strategy

The plan implements a **Dynamic Memory Profiling** strategy to guarantee feasibility:
1.  **Probe**: The loader first streams a small batch of molecules to measure per-molecule RAM overhead.
2.  **Calculate**: It computes `max_samples = (Target_RAM_GB * 1024^3) / per_molecule_bytes`.
3.  **Adapt**: The final sample size is set to a computationally feasible upper bound determined by the calculated maximum. If `calculated_max < 10000`, a warning is logged, but the run proceeds to ensure the pipeline completes.
4.  **Stream**: The dataset is loaded using `streaming=True` and iterated in batches, ensuring peak memory never exceeds the calculated limit.

This approach replaces the static "50k molecule" assumption with a runtime-safe calculation.