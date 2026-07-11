# Implementation Plan: Predicting Molecular Interactions in Ionic Liquids via Machine Learning

**Branch**: `001-predict-molecular-interactions` | **Date**: 2026-07-05 | **Spec**: `specs/001-predicting-molecular-interactions/spec.md`

## Summary
This project implements a machine learning pipeline to predict decomposed interaction energy components (electrostatic, dispersion, hydrogen-bonding) for ionic liquid (IL) pairs. The approach ingests the ILThermo dataset (provided locally) and the SAPT2023 dataset (verified), engineers physicochemical and graph-based descriptors using RDKit and ETKDG-generated 3D geometries, and trains three independent XGBoost regressors under strict CPU constraints. The pipeline concludes with stratified MANOVA analysis on **ground truth** energies to identify structural family trends and external validation against the dft23-full dataset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `xgboost`, `scikit-learn`, `rdkit`, `pandas`, `numpy`, `optuna`, `datasets` (for HuggingFace), `pyyaml`, `requests`  
**Storage**: Local filesystem (CSV, JSON, Parquet) within GitHub Actions workspace (~14 GB limit).  
**Testing**: `pytest` (unit), `pytest-cov` (coverage), custom contract validators.  
**Target Platform**: Linux (GitHub Actions Free Runner: 2 CPU, 7 GB RAM, No GPU).  
**Project Type**: Computational Chemistry / Data Science Pipeline.  
**Performance Goals**: Full pipeline execution ≤ 5 hours; Peak RAM ≤ 3 GB; Model inference ≤ 10s.  
**Constraints**: No GPU usage; No large-LLM inference; Strict memory management for feature engineering; XGBoost hyperparameter tuning limited to a fixed time budget per trial.  
**Scale/Scope**: Training set size determined by available SAPT2023 data (target >1,000 pairs); External validation set n=50 from dft23-full.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; `requirements.txt` pins versions; External datasets fetched via verified loaders (SAPT2023, dft23-full); Local ILThermo CSV checksummed. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` restricted to verified HuggingFace datasets (SAPT2023, dft23-full). ILThermo is a local data requirement with documented schema. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/`; Derived data in `data/processed/`; Checksums computed for all artifacts; No in-place modifications. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/processed/` CSVs and `code/` scripts; No hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in `state/...yaml`; Artifact updates trigger state timestamp updates. |
| **VI. Computational Chemistry Precision** | PASS | Validation against dft23-full (total energy) and SAPT2023 (decomposed) mandated; MAE ≤ 0.5 kcal mol⁻¹ target enforced. |
| **VII. Structural Family Stratification** | PASS | Stratified splits (majority/minority/minority) by cation/anion family; MANOVA performed on ground truth energies; RDKit descriptors capture structural features. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-interactions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── unified_training_table.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-225-predicting-molecular-interactions-in-ion/
├── data/
│   ├── raw/             # Downloaded datasets (ILThermo, SAPT, DFT)
│   ├── processed/       # Unified training table, feature matrices
│   └── external/        # Validation set (DFT/SAPT)
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest_and_feature_engineering.py
│   ├── 02_train_models.py
│   ├── 03_analysis_and_validation.py
│   ├── utils/
│   │   ├── descriptors.py
│   │   ├── data_loaders.py
│   │   └── metrics.py
│   └── tests/
│       ├── test_ingest.py
│       ├── test_models.py
│       └── test_analysis.py
├── state/
│   └── projects/PROJ-225-predicting-molecular-interactions-in-ion.yaml
└── artifacts/
    ├── models/          # Trained XGBoost artifacts (.json)
    └── reports/         # MANOVA, Sensitivity, Validation reports
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to minimize overhead on the GitHub Actions runner and ensure tight coupling between data processing and modeling steps within the 3 GB RAM limit.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Three Independent Models** | Interaction components are mathematically coupled but physically distinct; joint modeling may obscure specific mechanism dominance. | Single multi-output model would complicate interpretation of "which mechanism dominates" and violate the spec's requirement for separate regressors. |
| **Stratified Split by Family** | Chemical space is sparse; random splits may leave entire families out of training, invalidating MANOVA. | Random split would likely result in data leakage or insufficient representation of specific cation/anion families for statistical testing. |
| **External DFT Validation** | Tautological validation (testing on training data) is insufficient for scientific claims. | Internal cross-validation alone cannot confirm generalization to unseen chemical space or higher-fidelity methods. |
| **ETKDG Geometry Exclusion** | Construct validity requires actual 3D geometry. | Using ionic radii approximations introduces spurious correlations and violates the physical meaning of geometric features. |

## Implementation Phases

### Phase 0: Data Ingestion and Feature Engineering
**Goal**: Construct a unified training table with valid 3D geometric features.
1.  **Ingest Data**: Download SAPT2023 and dft23-full via `datasets` library. Load local `ilthermo.csv`.
2.  **Merge**: Join datasets on cation/anion SMILES.
3.  **Feature Engineering**:
    *   Compute physicochemical descriptors (partial charges, polarizability, H-bond counts) via RDKit.
    *   Generate graph embeddings (Morgan Fingerprints).
    *   **Geometric Features**: Generate 3D conformers using ETKDG.
        *   *Constraint*: If ETKDG fails to generate a valid conformer for a pair, **exclude** the row from the training set. Log the pair ID and reason to `data/processed/invalid_rows.log`.
        *   *No Approximation*: Do not use ionic radii or other proxies for missing geometry.
4.  **Validation**: Verify row counts and non-null values for required columns.

### Phase 1: Model Training
**Goal**: Train three XGBoost regressors with strict CPU constraints.
1.  **Split**: Stratified 70/15/15 split by cation/anion family.
2.  **Tuning**: Optuna optimization with 5-minute timeout per trial.
3.  **Training**: Train separate models for Electrostatic, Dispersion, and H-Bond energies.
4.  **Artifacts**: Save models and hyperparameter logs.

### Phase 2: Analysis and Validation
**Goal**: Statistical analysis of physical trends and model performance.
1.  **MANOVA (Physical Trends)**:
    *   **Input**: Ground truth energy components from SAPT2023.
    *   **Method**: Pillai's trace MANOVA grouping by structural families.
    *   **Hypothesis**: Do physical interaction energies differ significantly across families?
    *   *Note*: This tests the physical system, not the model.
2.  **Sensitivity Analysis (FR-006)**:
    *   **Method**: Sweep error thresholds $T \in \{0.4, 0.5, 0.6\}$ kcal mol⁻¹.
    *   **Metric**: Calculate the **fraction of test predictions** where $|prediction - truth| \le T$.
    *   **Robustness**: Define `is_robust` as `True` if the fraction of predictions within the tolerance remains high (e.g., >90%) across the sweep, or if the drop-off in coverage between thresholds is minimal (<5%).
    *   **Output**: Report with coverage fractions and `is_robust` flag.
3.  **External Validation**:
    *   Compare sum of predicted components vs. `total_energy` in dft23-full (n=50).
    *   Metrics: MAE, R².

### Phase 3: Reporting
**Goal**: Generate final reports and artifacts.
1.  Compile MANOVA, Sensitivity, and Validation reports.
2.  Verify all success criteria (SC-001 to SC-005).