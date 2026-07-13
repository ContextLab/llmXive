# Implementation Plan: Predicting Molecular Polarity from SMILES Strings with Machine Learning

**Branch**: `001-predict-molecular-polarity` | **Date**: 2026-07-13 | **Spec**: `specs/001-predict-molecular-polarity/spec.md`
**Input**: Feature specification from `specs/001-predict-molecular-polarity/spec.md`

## Summary

This project implements a machine learning pipeline to predict molecular dipole moments (polarity) using **only** 2D topological descriptors derived from SMILES strings. The core hypothesis is that 2D structural features (e.g., atom counts, connectivity indices) capture sufficient signal to approximate quantum-mechanically calculated dipole moments without the computational cost of 3D conformer generation. The implementation uses the QM9 dataset, RDKit for feature engineering, and LightGBM for regression, strictly adhering to the 6GB RAM / 6-hour runtime constraints of the GitHub Actions free-tier.

**Critical Constraint**: The pipeline must strictly exclude features definitionally derived from the target (e.g., TPSA) and must enforce 2D-only topology via runtime assertions and unit tests.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `rdkit`, `lightgbm`, `pandas`, `numpy`, `scikit-learn`, `shap`, `pyyaml`, `statsmodels` (for VIF)  
**Storage**: Local file system (CSV/Parquet) under `data/` and `artifacts/`  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Data Science / Machine Learning Pipeline  
**Performance Goals**: Peak memory < 6GB, Runtime < 6 hours, R² > null model baseline  
**Constraints**: NO 3D geometry generation, NO GPU, NO external data sources beyond verified QM9 links  
**Scale/Scope**: ~k molecules (QM9), A substantial set of features (after filtering), 5-fold CV, SHAP interpretability

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Dataset fetched via specific HuggingFace URL checksums. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to the "Verified datasets" block provided in the prompt. No invented URLs. |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with checksums recorded. Derived features saved to `data/processed/` with new filenames. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics (R², RMSE) computed by scripts in `code/` and logged to `artifacts/metrics.json`. Paper text will reference these JSON keys. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in `state/`. Content hashes updated on every code/data change. |
| **VI. 2D-Topological Fidelity** | **PASS** | **Enforcement Mechanism**: <br>1. **Unit Test**: `tests/unit/test_no_3d_conformers.py` mocks `rdkit.AllChem.EmbedMolecule` and asserts it is never called during `preprocess.py` execution.<br>2. **Runtime Assertion**: `code/data/preprocess.py` includes a wrapper around RDKit descriptor functions that raises `RuntimeError` if any 3D-dependent function (e.g., `CalcCrippenDescriptors` requiring 3D) is invoked.<br>3. **Feature Exclusion**: Explicit exclusion of TPSA and 3D-dependent descriptors in `code/data/feature_selection.py`. |
| **VII. Computational Constraint Adherence** | **PASS** | Data processed in batches. LightGBM used (CPU-optimized). Memory profiling included in the pipeline to ensure <6GB. VIF calculation optimized to run on sampled data if full matrix is too large. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-molecular-polarity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Source of Truth for Schemas)
    ├── dataset.schema.yaml
    ├── features.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-091-predicting-molecular-polarity-from-smile/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── data/
│   │   ├── download.py        # Fetches QM9 from verified URL
│   │   ├── preprocess.py      # SMILES -> 2D Descriptors (RDKit)
│   │   ├── feature_selection.py # VIF & Target Correlation Filtering (FR-007)
│   │   └── split.py           # Train/Test split (Random, no stratification)
│   ├── models/
│   │   ├── train.py           # LightGBM training with 5-fold CV
│   │   ├── evaluate.py        # Metrics calculation (R², RMSE)
│   │   └── explain.py         # SHAP analysis & Bootstrap Sensitivity
│   └── utils/
│       ├── logging.py         # Reproducible logging setup
│       └── memory_monitor.py  # Peak memory tracking
├── data/
│   ├── raw/                   # Downloaded QM9 parquet
│   └── processed/             # Feature matrices, splits
├── tests/
│   ├── contract/              # Schema validation tests (Symlinked from specs/contracts)
│   ├── integration/           # End-to-end pipeline test
│   └── unit/
│       └── test_no_3d_conformers.py # Enforces Principle VI
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected. All code resides in `code/` to maintain a tight coupling between data processing and modeling, ensuring reproducibility on a single runner. The `contracts/` directory in `specs/` holds the validation schemas. **CI Setup**: The GitHub Actions workflow will symlink `specs/.../contracts/` to `tests/contract/` before running tests to ensure path resolution matches the test runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **SHAP Analysis** | Required by FR-004 and SC-002 to interpret feature contributions. | A simple coefficient list is insufficient for non-linear tree models (LightGBM) where feature interactions are complex. |
| **Bootstrap Sensitivity** | Required to address methodology concern on stability of SHAP features. | Single-run SHAP values are unstable; bootstrapping validates the robustness of the "strongest signal" claim. |
| **VIF Filtering** | Required by methodology concern on multi-collinearity (pairwise r is insufficient). | Pairwise correlation (r > 0.95) fails to detect linear combinations of >2 features; VIF is necessary for SHAP stability. |
| **Target Correlation Check** | Required by scientific soundness concern on definitional redundancy. | Pairwise feature filtering does not remove features highly correlated with the *target* (leakage); explicit target check is needed. |
| **Batch Processing** | Required by FR-006 (Memory < 6GB) for QM9 scale. | Loading the full large-scale molecule dataset with 200+ features into RAM at once risks OOM on 7GB runners. |
| **No Stratification** | Required by methodology concern on continuous target binning. | Stratification by binning a continuous variable introduces discretization bias; random split is statistically valid. |
| **Correlation Filtering (FR-007)** | Required by FR-007 to mitigate multicollinearity. | Implemented in `code/data/feature_selection.py` using iterative VIF and target correlation checks. |

## FR/SC Coverage Matrix

| ID | Requirement | Plan Implementation Location |
|----|-------------|------------------------------|
| FR-001 | Parse SMILES, a comprehensive set of 2D descriptors, no 3D | `code/data/preprocess.py` (RDKit 2D only), `tests/unit/test_no_3d_conformers.py` |
| FR-002 | LightGBM on D features, strict separation | `code/models/train.py` (Random split, no stratification) |
| FR-003 | k-fold CV, seed logging | `code/models/train.py` (cv parameter, seed config) |
| FR-004 | SHAP analysis | `code/models/explain.py` |
| FR-005 | Sensitivity on thresholds | `code/models/explain.py` (Bootstrap sweep, not just hyperparam sweep) |
| FR-006 | Batch processing, <6GB RAM | `code/data/preprocess.py` (Chunked iteration) |
| FR-007 | Correlation filtering (r > 0.95) | **UPGRADED**: `code/data/feature_selection.py` (VIF iteration + Target Correlation Check) |
| SC-001 | R² vs Null Model | `code/models/evaluate.py` (Baseline calculation) |
| SC-002 | SHAP magnitude | `code/models/explain.py` (Top features) |
| SC-003 | Sensitivity to thresholds | `code/models/explain.py` (Bootstrap variance report) |
| SC-004 | Runtime/Memory limits | `code/utils/memory_monitor.py` (Assertions) |
| SC-005 | No 3D leakage | `tests/unit/test_no_3d_conformers.py` + Runtime Assertions |