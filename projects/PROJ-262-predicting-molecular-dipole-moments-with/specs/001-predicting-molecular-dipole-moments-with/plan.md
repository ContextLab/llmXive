# Implementation Plan: Predicting Molecular Dipole Moments with Graph Neural Networks

**Branch**: `001-predicting-molecular-dipole-moments` | **Date**: 2026-05-22 | **Spec**: `specs/001-predicting-molecular-dipole-moments-with/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-dipole-moments-with/spec.md`

## Summary

This feature implements a comparative study to determine the extent to which 3D conformational geometry provides independent predictive information for molecular dipole moments beyond 2D connectivity and atom types. The system downloads a verified subset of the QM9 dataset, extracts 3D coordinates and 2D descriptors (Morgan fingerprints, **Topological** Coulomb matrices), and trains a lightweight SchNet-style GNN against a Random Forest baseline. Crucially, the study includes **ablation variants** (SchNet-Randomized, SchNet-2D) to causally isolate the 3D geometry signal. The pipeline rigorously validates that 3D geometry adds value, performs statistical significance testing (Wilcoxon signed-rank test + bootstrap), and generates feature attribution maps (Input Gradients) to identify structural drivers. The entire pipeline is designed to run within 6 hours on 2 CPU cores with <8GB RAM, using a reduced subset ([deferred] molecules) and simplified architecture to ensure feasibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch Geometric (CPU-only mode), RDKit, scikit-learn, pandas, numpy, pyyaml, datasets (Hugging Face), matplotlib, seaborn  
**Storage**: Local `data/` directory (parquet/csv), `data/reports/` for exclusion logs  
**Testing**: pytest (unit/integration), contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, ~7GB RAM, ~14GB disk)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Complete data download, preprocessing, training (50 epochs, 5 seeds), and evaluation within 6 hours.  
**Constraints**: The system is designed to maintain a minimal RAM footprint.; no local GPU; strict timeout; CPU-only execution for GNN (SchNet) with fallback to scaled-down GPU via Kaggle auto-offload if CUDA is detected (though plan prioritizes CPU-tractable SchNet variants).  
**Scale/Scope**: **[deferred] molecules** (sampled from QM9) to fit memory and runtime; random seeds for statistical robustness.

> **Dataset Strategy**: The plan utilizes the QM9 dataset. Per the "Verified datasets" block, the DOI `10.1038/sdata.2014.22` has **NO verified source**. However, verified Hugging Face mirrors exist (e.g., `lisn519010/QM9`). The implementation will fetch from the verified Hugging Face URL to ensure CI reproducibility, treating the DOI as the canonical reference for the dataset's scientific origin but not the download source. The mirror has been verified to contain the full set of molecules with required columns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**:
    *   *Requirement*: Random seeds pinned; external datasets from canonical sources; `code/` runnable end-to-end.
    *   *Plan Action*: `code/` will include a `seed.py` module to pin seeds globally. Data will be fetched via `datasets.load_dataset` from the verified Hugging Face URL. `requirements.txt` will pin versions.
    *   *Status*: **COMPLIANT**.

2.  **Verified Accuracy**:
    *   *Requirement*: Citations verified against primary sources; title overlap ≥ 0.7.
    *   *Plan Action*: All citations in `research.md` and `plan.md` will be cross-referenced with the "Verified datasets" block and literature. The QM9 DOI will be cited as the origin, but the download URL will be the verified HF link.
    *   *Status*: **COMPLIANT**.

3.  **Data Hygiene**:
    *   *Requirement*: Checksums recorded; no in-place modification; PII scan.
    *   *Plan Action*: `data/` files will be checksummed (SHA-256) upon download. `handle_missing_coords.py` will generate a report of excluded molecules without modifying raw data. No PII expected in QM9 (small organic molecules).
    *   *Status*: **COMPLIANT**.

4.  **Single Source of Truth**:
    *   *Requirement*: Figures/statistics trace to `data/` and `code/`.
    *   *Plan Action*: All metrics (MAE, RMSE) will be written to `data/results/metrics.json`. Plots will be generated directly from this JSON.
    *   *Status*: **COMPLIANT**.

5.  **Versioning Discipline**:
    *   *Requirement*: Content hashes; artifact updates.
    *   *Plan Action*: The build script will compute hashes for `data/`, `models/`, and `results/` artifacts and update the project state file. Checksums will be recorded in `data/reports/checksums.txt`.
    *   *Status*: **COMPLIANT**.

6.  **3D Geometry Preservation**:
    *   *Requirement*: Rotational/translational invariance; document transformations.
    *   *Plan Action*: SchNet implementation will use distance-based edge features (invariant). Preprocessing will center molecules at the origin and document this step. No rotation of coordinates will be applied that alters relative geometry.
    *   *Status*: **COMPLIANT**.

7.  **Chemical Interpretability**:
    *   *Requirement*: Attribution of atom types/bond types/3D conformation.
    *   *Plan Action*: Permutation importance (RF) and **Input Gradients** (GNN) will be implemented to rank features. Results will be mapped back to atom indices.
    *   *Status*: **COMPLIANT**.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-dipole-moments-with/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── metrics.schema.yaml
│   └── attribution.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-262-predicting-molecular-dipole-moments-with/
├── code/
│   ├── __init__.py
│   ├── seed.py                  # Global seed pinning
│   ├── data/
│   │   ├── download_qm9.py      # Fetch from verified HF URL
│   │   ├── preprocess.py        # Extract 3D/2D, handle missing coords
│   │   └── handle_missing_coords.py  # Exclusion logic & reporting (writes excluded_molecules.csv)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schnet.py            # Lightweight SchNet (CPU)
│   │   └── rf_baseline.py       # Random Forest baseline
│   ├── train/
│   │   ├── train_gnn.py
│   │   ├── train_rf.py
│   │   └── train_ablation.py    # NEW: Trains SchNet-Randomized, SchNet-2D, RF-Combined
│   ├── eval/
│   │   ├── metrics.py           # MAE, RMSE, CI calculation (Bootstrap)
│   │   ├── attribution.py       # Permutation importance, Input Gradients
│   │   └── stats.py             # Wilcoxon signed-rank test
│   └── viz/
│       └── plot_feature_importance.py
├── data/
│   ├── raw/                     # Downloaded parquet
│   ├── processed/               # Featurized matrices
│   └── reports/
│       ├── excluded_molecules.csv
│       └── checksums.txt
├── tests/
│   ├── unit/
│   └── contract/
└── requirements.txt
```

**Structure Decision**: A modular CLI structure is selected to separate data ingestion, modeling, and evaluation. This aligns with the "Reproducibility" and "Data Hygiene" principles, ensuring each step is isolated and testable. The `data/` directory is strictly hierarchical (raw vs. processed) to prevent in-place modification.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **SchNet (GNN) + RF Baseline + Ablation** | Required to isolate 3D vs. 2D signal (FR-004, FR-005). | A single model cannot answer the comparative research question. |
| **Streaming Data Loading** | QM9 full size may exceed 8GB RAM. | Loading full dataset into memory risks OOM failure on CI. |
| **5 Random Seeds** | Required for statistical significance (SC-001, SC-005). | Single seed results are not robust and fail paired t-test requirements. |
| **Ablation Variants** | Required to prove 3D contribution (Plan Phase 2). | Baseline-only comparison cannot distinguish 3D signal from noise. |
| **Reduced Subset (5k)** | Required to meet 6h runtime on 2 vCPUs. | Full dataset exceeds compute budget. |

## Methodology

### 1. Data Preprocessing
*   **Download**: Fetch QM9 from verified HF URL (`lisn519010/QM9`). Record SHA-256 checksum.
*   **Filter**: Remove molecules with missing 3D coordinates. Log to `excluded_molecules.csv`.
* **Subset**: Randomly sample [deferred] molecules.
*   **Featurization**:
    *   **3D**: Atom types, 3D coordinates (centered).
    *   **2D**: Morgan Fingerprints, **Topological Coulomb Matrices** (using graph distances).
*   **Streaming**: Use chunked loading to process data in memory-efficient batches.

### 2. Model Training
*   **Base Models**:
    *   **SchNet (3D)**: 2 interaction blocks, 32 hidden units.
    *   **Random Forest (2D)**: `n_estimators=100`.
*   **Ablation Models**:
    *   **SchNet-Randomized**: SchNet trained with shuffled 3D coordinates (breaks geometry signal).
    *   **SchNet-2D**: SchNet architecture trained **without** 3D coordinates (only 2D features).
    *   **RF-Combined**: Random Forest trained on 2D + 3D features.
*   **Protocol**:
    *   **Splits**: Random 80/10/10 (Train/Val/Test).
    *   **Seeds**: 5 independent random seeds.
    *   **Epochs**: 50 epochs with early stopping (patience=10).

### 3. Evaluation & Statistics
*   **Metrics**: MAE, RMSE on test set.
*   **Confidence Intervals**: Bootstrap (multiple resamples) on the 5 seed results.
*   **Statistical Test**: **Wilcoxon signed-rank test** (non-parametric) comparing RMSE distributions of SchNet vs. SchNet-Randomized and SchNet vs. RF.
*   **Interpretability**:
    *   **RF**: Permutation Importance.
    *   **SchNet**: **Input Gradients** (w.r.t. coordinates) and Integrated Gradients.

### 4. GPU Escape Hatch
*   If CPU run exceeds a reasonable duration threshold or fails, the runner will detect CUDA availability (if offloaded to Kaggle) and re-run with `device="cuda"` and 8-bit quantization. This is a fallback only; the primary plan is CPU-tractable.

## Compute Feasibility
*   **CPU-First**: SchNet with 32 hidden units and 5k samples is computationally feasible on 2 vCPUs within 6 hours.
*   **Memory**: Streaming and chunked processing ensure <8GB RAM usage.
*   **GPU Escape Hatch**: If the CPU run exceeds the 6h limit, the runner will auto-offload to Kaggle GPU. The plan includes a `device` flag that defaults to `cpu` but switches to `cuda` if available, with a reduced batch size to fit available VRAM.

## Versioning & Checksums
*   All artifacts in `data/`, `models/`, and `results/` will be checksummed (SHA-256).
*   Checksums will be recorded in `data/reports/checksums.txt`.
*   The build script will update the project state file with these hashes.

## Output Contracts
*   **Metrics**: `results/metrics.json` (MAE, RMSE, CI, Seed).
*   **Attribution**: `results/attribution.json` (Top features, importance scores, structural descriptions).
*   **Exclusion**: `data/reports/excluded_molecules.csv` (mol_id, reason, original_row).