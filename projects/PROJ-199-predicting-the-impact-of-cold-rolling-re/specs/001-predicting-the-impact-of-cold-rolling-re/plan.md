# Implementation Plan: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

**Branch**: `001-predicting-cold-rolling-texture` | **Date**: 2026-06-12 | **Spec**: `specs/001-predicting-the-impact-of-cold-rolling-re/spec.md`
**Input**: Feature specification from `specs/001-predicting-the-impact-of-cold-rolling-re/spec.md`

## Summary

This project implements a computational pipeline to predict the evolution of crystallographic texture (Brass, Copper, S, Goss components, and Texture Index) in FCC metals (Aluminum, Copper, Nickel) as a function of cold-rolling reduction percentage. The approach combines automated ingestion of EBSD datasets, crystallographic symmetry re-indexing using `orix`, quantitative texture descriptor extraction, and the training of Gaussian Process and polynomial regression models. 

The system explicitly addresses the limitation of using only reduction percentage as a predictor by:
1.  **Variance Decomposition**: Using hierarchical modeling concepts and Shapley value regression to partition variance between 'Material Type' (SFE proxy) and unobserved confounders, rather than just reporting total residual variance.
2.  **Physics Validation**: Implementing a 'Hold-out Physics Check' to ensure the model learns underlying trends (e.g., Brass increase) rather than merely memorizing the synthetic generator's function.
3.  **Metal-Aware Success Criteria**: Acknowledging that R² ≥ 0.85 is a target, but allowing for metal-specific analysis if the threshold is not met due to distinct physical regimes (e.g., SFE differences).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `orix` (crystallography), `scikit-learn` (modeling), `pandas`, `numpy`, `pyyaml`, `requests`, `shap` (for variance decomposition)  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`); Parquet/CSV formats.  
**Testing**: `pytest` (contract tests on schema, unit tests on descriptor calculation, symmetry re-indexing).  
**Target Platform**: GitHub Actions free-tier runner (limited CPU resources, ~7 GB RAM, no GPU).  
**Project Type**: Scientific computing pipeline / CLI  
**Performance Goals**: Complete data ingestion and modeling within 6 hours; R² ≥ 0.85 on held-out test sets (SC-003), with metal-specific analysis if thresholds are not met.  
**Constraints**: Must run on CPU only; no deep learning; strict adherence to FCC symmetry handling (FR-002); no modification of raw data files.  
**Scale/Scope**: Processing of synthetic EBSD data for multiple metals across multiple reduction levels (substantial). The dataset generation script (see `research.md` Section 2) ensures the 'reduction' variable exists and is linked to texture evolution.

> **Dataset Fit Note**: The project uses a verified synthetic EBSD dataset generation script (parameters defined in `research.md`) to ensure the presence of 'reduction percentage' metadata. If a pre-packaged dataset on HuggingFace is used, it is verified to contain these specific variables. The plan explicitly models the residual variance to account for missing microstructural variables (FR-008), addressing the reviewer's concern about "statistical correlation vs. physical structure."

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action / Evidence |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `code/` will pin `requirements.txt`; random seeds set in `code/`; datasets fetched from canonical HuggingFace URLs or generated locally with pinned seeds. |
| **II. Verified Accuracy** | **PASS** | All citations (e.g., Rosenstock et al.) will be validated against primary sources; no fabricated URLs for MTEX-style definitions. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed upon download; transformations produce new files in `data/processed`; no in-place edits. |
| **IV. Single Source of Truth** | **PASS** | All metrics in `paper/` will be derived via script from `data/processed`; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; state file updated on changes. |
| **VI. Numerical-Stability** | **PASS** | Cross-validation implemented; R² ≥ 0.85 threshold enforced (SC-003); trends (Brass increase) validated against known physics (Hold-out Physics Check). |
| **VII. Crystallographic-Symmetry** | **PASS** | `orix` used for all re-indexing to FCC symmetry; unit tests in `tests/unit/test_symmetry_reindex.py` enforce this (Constitution Principle VII). |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-the-impact-of-cold-rolling-texture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-199-predicting-the-impact-of-cold-rolling-re/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── main.py                  # Orchestration entry point
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py          # FR-001: Download from HuggingFace / Generate Synthetic
│   │   └── preprocess.py        # FR-002: Filter confidence, re-index symmetry
│   ├── features/
│   │   ├── __init__.py
│   │   └── descriptors.py       # FR-003: Texture Index, Volume Fractions (Brass, Cu, S, Goss)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train.py             # FR-004, FR-009: GP & Polynomial regression, Extrapolation flagging
│   │   └── validate.py          # FR-005: K-fold CV, R², RMSE, Interaction Tests
│   └── analysis/
│       ├── __init__.py
│       ├── robustness.py        # FR-007, FR-008: Sensitivity, Residual Variance Decomposition
│       └── physics_check.py     # FR-006, SC-003: Hold-out Physics Check, Trend Validation
├── data/
│   ├── raw/                     # Downloaded ZIP/JSONL or Generated Synthetic
│   ├── processed/               # Cleaned Parquet, derived metrics
│   └── interim/                 # Intermediate EBSD objects
├── tests/
│   ├── contract/                # Schema validation
│   ├── unit/
│   │   ├── test_symmetry_reindex.py # Enforces Constitution Principle VII
│   │   └── test_descriptors.py
│   └── integration/
└── docs/
    └── constitution.md          # Project constitution
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`data`, `features`, `models`, `analysis`) to ensure separation of concerns and facilitate unit testing. This aligns with the "Scientific computing pipeline" type and supports the reproducibility requirement by isolating data fetching from modeling.

## Task Breakdown (Mapping FRs to Code)

| Functional Requirement | Code Location | Description |
| :--- | :--- | :--- |
| **FR-001** (Data Acquisition) | `code/data/download.py` | Downloads or generates synthetic EBSD data with reduction metadata. |
| **FR-002** (Filter & Re-index) | `code/data/preprocess.py` | Filters confidence < 0.1; re-indexes to FCC symmetry. |
| **FR-003** (Descriptor Extraction) | `code/features/descriptors.py` | Calculates Brass, Cu, S, Goss, Texture Index. |
| **FR-004** (Model Training) | `code/models/train.py` | Trains GP and Polynomial models; handles Material Type as categorical. |
| **FR-005** (Validation) | `code/models/validate.py` | 5-fold CV; R², RMSE; Interaction tests for joint model. |
| **FR-006** (Associational Framing) | `code/analysis/physics_check.py` | Ensures trends match physics; frames results as associational. |
| **FR-007** (Sensitivity Analysis) | `code/analysis/robustness.py` | Sweeps interpolation tolerance; checks R² stability. |
| **FR-008** (Residual Variance) | `code/analysis/robustness.py` | Decomposes variance (Shapley/HLM) to quantify unobserved confounders. |
| **FR-009** (Extrapolation) | `code/models/train.py` | Flags extrapolation; applies confidence penalty. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Gaussian Process Modeling** | Required for FR-004 to provide uncertainty estimates and handle non-linear texture evolution better than simple linear regression. | A simple linear model would fail to capture the complex, non-linear evolution of texture components (e.g., Brass vs. Copper) and would not provide the confidence intervals required for FR-009. |
| **Residual Variance Decomposition** | Required by FR-008 to address reviewer concerns about missing microstructural variables. Using Shapley values/HLM allows explicit partitioning of variance, not just a total residual. | Ignoring this would conflate statistical correlation with physical causation, violating the "Verified Accuracy" and "Reproducibility" principles regarding physical mechanisms. |
| **Symmetry Re-indexing** | Required by FR-002 and Constitution Principle VII. | Skipping re-indexing would result in inconsistent orientation data, making volume fraction calculations (Brass, etc.) invalid due to symmetry ambiguity. |
| **Hold-out Physics Check** | Required to distinguish between model learning physics vs. memorizing synthetic generator (Scientific Soundness concern). | Relying solely on R² on synthetic data is tautological; the physics check ensures the model captures real trends (e.g., Brass increase). |