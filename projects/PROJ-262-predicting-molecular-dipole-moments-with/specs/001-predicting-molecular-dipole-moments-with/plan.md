# Implementation Plan: Predicting Molecular Dipole Moments with Graph Neural Networks

**Branch**: `001-predicting-molecular-dipole-moments` | **Date**: 2026-05-22 | **Spec**: `specs/001-predicting-molecular-dipole-moments/spec.md`
**Input**: Feature specification from `/specs/001-predicting-molecular-dipole-moments/spec.md`

## Summary

This feature implements a comparative study to determine the extent to which 3D conformational geometry provides independent predictive information for molecular dipole moments beyond 2D connectivity and atom types. The approach involves downloading the QM9 dataset, extracting 3D coordinates and 2D descriptors (Morgan fingerprints), and training three models: a lightweight SchNet-style Graph Neural Network (GNN), a Random Forest baseline on 2D features, and a Combined Random Forest on 2D+3D features. 

To address causal control, an **Ablation Study** is included, comparing the SchNet GNN against a "SchNet-Randomized" variant (where 3D coordinates are shuffled) and a "2D-GNN" (identical architecture without coordinates). This isolates the contribution of geometry from model capacity. Performance is evaluated using MAE and RMSE on held-out test sets across **30 random seeds** (to ensure statistical power), with statistical significance tested via paired t-tests and Bootstrap Confidence Intervals. Feature attribution (Integrated Gradients, SHAP) identifies structural drivers of prediction accuracy. The entire pipeline is constrained to run within 6 hours on 2 CPU cores with an 8GB memory footprint, utilizing streaming for large datasets where necessary.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch Geometric (CPU-only), RDKit, scikit-learn, pandas, datasets (Hugging Face), matplotlib, seaborn, shap, captum  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/reports`); Parquet format for intermediate data  
**Testing**: `pytest` with `pytest-cov` for coverage; `conftest.py` for fixture management  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7GB RAM)  
**Project Type**: Computational research pipeline / CLI tool  
**Performance Goals**: End-to-end execution ≤ 6 hours; Memory footprint ≤ 8GB; RMSE variance across seeds < 10%  
**Constraints**: CPU-only execution for GNN training (no CUDA); streaming data loading to avoid OOM; strict adherence to QM9 DFT reference data (no physical experimental validation in this scope); hydration state and conformational ensembles are out of scope (documented limitations).  
**Scale/Scope**: A large-scale dataset of organic molecules, such as QM9, will be utilized for this study.; subset sampling determined by Power Analysis; 30 random seeds for statistical robustness.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Principle I (Reproducibility)**: The plan mandates pinned seeds in `code/`, checksums for all `data/` artifacts, and a `requirements.txt` with exact versions. The pipeline is designed to run end-to-end on a fresh runner.
2.  **Principle II (Verified Accuracy)**: All citations in `research.md` and `plan.md` will be cross-referenced against the "Verified datasets" block in the user message. No fabricated URLs will be used. The QM9 dataset will be sourced from verified Hugging Face mirrors (e.g., `lisn519010/QM9`).
3.  **Principle III (Data Hygiene)**: Raw data is downloaded once and checksummed. Transformations (filtering, feature extraction) produce new files in `data/processed` with documented derivation steps. No in-place modification of raw data. A dedicated `code/utils/hygiene.py` script records SHA-256 hashes in `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml`.
4.  **Principle IV (Single Source of Truth)**: All figures and statistics in the final report will be generated programmatically from the `data/` artifacts and `code/` outputs. No hand-typed numbers.
5.  **Principle V (Versioning)**: Content hashes for artifacts will be recorded in `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` via the `hygiene.py` script.
6.  **Principle VI (3D Geometry Preservation)**: Coordinate transformations will be validated by `code/data/validate_geometry.py`, which computes RMSD and bond angle deviations against the raw QM9 source. The pipeline fails if tolerance > 1e-4 is exceeded.
7.  **Principle VII (Chemical Interpretability)**: Feature attribution (Integrated Gradients, SHAP) will be explicitly implemented to identify specific structural components (atom types, bond angles) driving predictions. Attribution scores will be mapped back to RDKit atom indices to correlate with chemical intuition.

*Note on Reviewer Comments*: The reviewer's request for experimental validation (X-ray/dielectric spectroscopy) is acknowledged as a known limitation (FR-011). This feature scope is strictly computational, validating against QM9 DFT reference data. Physical validation is a downstream requirement, not a feature requirement. Hydration and conformational ensemble limitations are documented as out-of-scope.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-dipole-moments/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-262-predicting-molecular-dipole-moments-with/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py              # Handles QM9 download, caching, checksum
│   │   ├── preprocess.py            # Extracts 3D/2D features, handles missing coords, generates exclusion report
│   │   ├── validate_geometry.py     # Validates 3D geometry preservation (RMSD, bond angles)
│   │   └── split.py                 # Train/test splits with fixed seeds
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schnet_gnn.py            # Lightweight SchNet-style GNN (CPU-only)
│   │   ├── schnet_randomized.py     # Ablation: SchNet with shuffled coordinates
│   │   ├── schnet_2d.py             # Ablation: SchNet without coordinates
│   │   └── rf_baseline.py           # Random Forest baseline
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py                 # Training loop, early stopping, metrics
│   │   └── evaluate.py              # MAE, RMSE, confidence intervals
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── attribution.py           # Integrated Gradients, SHAP (no saliency maps)
│   │   ├── stats.py                 # Paired t-tests, bootstrap, stability validation
│   │   └── visualize.py             # RDKit-based 2D/3D heatmaps
│   ├── utils/
│   │   └── hygiene.py               # Artifact hashing and state recording
│   └── main.py                      # Orchestrator script
├── data/
│   ├── raw/                         # Downloaded QM9 (raw parquet)
│   ├── processed/                   # Feature matrices, splits
│   └── reports/
│       └── excluded_molecules.csv   # Report for missing 3D coords (T019)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── docs/
    └── README.md
```

**Structure Decision**: Single project structure with modular `code/` directories for data, models, training, and analysis. `preprocess.py` consolidates all data handling (including missing coords) to resolve naming inconsistencies. `validate_geometry.py` and `hygiene.py` are added to satisfy Constitutional Principles VI and V.

## Implementation Phases

### Phase 0: Research & Dataset Strategy
- **Goal**: Confirm dataset availability and perform Power Analysis.
- **Actions**: 
  - Verify QM9 dataset accessibility via `datasets.load_dataset(..., streaming=True)`.
 - Perform Power Analysis: Calculate minimum sample size to detect effect size (Cohen's d=0.5) with [deferred] power.
  - Select subset size (e.g., large-scale) based on Power Analysis and 6h constraint.
- **Deliverable**: `research.md` updated with Power Analysis results and subset size justification.

### Phase 1: Data Preparation & Validation
- **Goal**: Download, clean, and validate data.
- **Actions**:
  - **Download**: Fetch QM9 from verified Hugging Face mirror.
  - **Preprocess**: Extract 3D coordinates, atom types, and 2D Morgan fingerprints.
  - **Exclusion Handling**: Identify molecules with missing 3D coordinates. Write `data/reports/excluded_molecules.csv` (columns: `mol_id`, `reason`, `original_row`).
  - **Geometry Validation**: Run `code/data/validate_geometry.py` to compute RMSD and bond angle deviations against raw data. Fail if tolerance > 1e-4.
  - **Feature Engineering**: Generate 2D fingerprints and 3D distance matrices.
- **Deliverable**: `data/processed/feature_matrix.parquet`, `data/reports/excluded_molecules.csv`.

### Phase 2: Model Training
- **Goal**: Train models on 30 random seeds.
- **Actions**:
  - **Baseline**: Train Random Forest on 2D features (Morgan fingerprints).
  - **Combined**: Train Random Forest on 2D + 3D features (Morgan + Distance Matrix).
  - **GNN**: Train SchNet on 3D coordinates.
  - **Ablation**: Train SchNet-Randomized (shuffled coords) and SchNet-2D (no coords).
  - **Parameters**: 50 epochs, early stopping (patience=10), 30 seeds.
- **Deliverable**: Model checkpoints, prediction logs.

### Phase 3: Evaluation & Statistical Analysis
- **Goal**: Quantify performance and significance.
- **Actions**:
  - Compute MAE, RMSE for all models.
  - **Marginal Gain Test**: Paired t-test (α=0.05) comparing RF (2D) vs RF (2D+3D).
  - **Geometry Sensitivity Test**: Paired t-test comparing SchNet vs SchNet-Randomized.
  - **Bootstrap**: Generate -resample Bootstrap CIs for RMSE.
  - **Stability Validation**: Calculate RMSE variance across 30 seeds; verify < 10%.
- **Deliverable**: `data/reports/metrics.json` (with CIs), `data/reports/stats_results.json`.

### Phase 4: Feature Attribution & Visualization
- **Goal**: Identify structural drivers and visualize.
- **Actions**:
  - **Attribution**: Apply Integrated Gradients (GNN) and SHAP (RF) to identify top features.
  - **Feature Count Validation**: Verify at least 3 distinct structural features (e.g., atom type, bond angle) have significant attribution scores.
  - **Visualization**: Generate RDKit-based D/3D heatmaps for top 5 molecules.
  - **Mapping**: Map attribution scores to RDKit atom indices to correlate with chemical intuition.
- **Deliverable**: `data/reports/attribution.parquet`, `docs/figures/`.

### Phase 5: Reporting & Artifact Hashing
- **Goal**: Finalize reports and ensure reproducibility.
- **Actions**:
  - Compile final report.
  - Run `code/utils/hygiene.py` to compute SHA-256 hashes for all `data/` artifacts and update `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml`.
- **Deliverable**: Final `plan.md`, `research.md`, and updated state file.

## Complexity Tracking

No violations of the Constitution are present in this plan. The structure is minimal and focused on the core requirements: data ingestion, feature extraction, model training, and statistical analysis. The use of streaming for large datasets and CPU-only execution for GNNs ensures feasibility within the 6h/2CPU/8GB constraints. The inclusion of 30 seeds and ablation studies ensures statistical rigor and causal validity.