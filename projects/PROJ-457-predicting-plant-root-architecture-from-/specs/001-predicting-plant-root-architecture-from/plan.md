# Implementation Plan: 001-predict-root-architecture

**Branch**: `001-predict-root-architecture` | **Date**: 2024-05-21 | **Spec**: `specs/001-predict-root-architecture/spec.md`
**Input**: Feature specification from `/specs/001-predict-root-architecture/spec.md`

## Summary

This project implements a statistical pipeline to quantify the associational relationships between soil nutrient availability (Phosphorus, Nitrogen) and plant root architectural traits (length, branching density, surface area). The approach utilizes Linear Mixed-Effects Models (LMM) with species as random intercepts, supplemented by Random Forest baselines, all processed within strict CPU-only constraints (GitHub Actions free tier). The pipeline strictly adheres to the project constitution regarding data hygiene, reproducibility, and cross-species stratified validation.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`, `geopandas`
**Storage**: Local filesystem (`data/` for raw/processed, `artifacts/` for outputs)
**Testing**: `pytest` (contract testing against YAML schemas, unit tests for preprocessing logic)
**Target Platform**: Linux (GitHub Actions free-tier runner: limited CPU resources, ~7 GB RAM, no GPU)
**Project Type**: Computational Research Pipeline
**Performance Goals**: End-to-end execution ≤ 6 hours; Memory usage ≤ 6 GB; Output size ≤ 100 MB.
**Constraints**:
- No GPU/CUDA usage.
- No large model training or inference.
- Strict species-level data splitting to prevent leakage (Constitution Principle VI).
- All external citations must be verified against the "Verified datasets" block.
- **Spatial Logic**: Implementation of nearest-neighbor interpolation within a A defined radius for data merging (FR-002).

> Domain-specific empirical specifics (exact dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **CONDITIONAL** | Random seeds pinned in `code/`; PlantPheno fetched via verified loader. ISRIC data requires manual provision (user-provided file) to ensure reproducibility of scientific results. |
| **II. Verified Accuracy** | **CONDITIONAL** | Dataset URLs in `research.md` restricted to the "Verified datasets" block for PlantPheno. ISRIC source is user-provided; no automated fetching. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`; checksums recorded in state file; transformations write to new files. |
| **IV. Single Source of Truth** | **PASS** | All statistics in reports generated directly from `code/` outputs; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts tracked via content hashes; state file updated on artifact changes. |
| **VI. Cross-Species Stratified Validation** | **PASS** | Data splits performed strictly by `species` column; no row-level shuffling across species. |
| **VII. Nutrient-Specific Metric Normalization** | **PASS** | Nutrients z-score normalized; root metrics log-transformed prior to modeling. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-root-architecture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── raw_root_phenotype.schema.yaml
│   ├── raw_soil_nutrient.schema.yaml
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, constants (loaded via pyyaml)
├── data_ingestion.py    # FR-001, FR-002 (10km spatial join), FR-012
├── preprocessing.py     # FR-003 (KNN fit-apply), FR-012 (filtering, transformation)
├── modeling.py          # FR-004, FR-005, FR-006, FR-008 (LRT), FR-010
├── visualization.py     # FR-007, FR-011
├── reporting.py         # FR-009, SC-001..SC-006
└── main.py              # Orchestrator

tests/
├── contract/
│   └── test_schemas.py
├── unit/
│   └── test_preprocessing.py
└── integration/
    └── test_pipeline.py

data/
├── raw/                 # Downloaded datasets (checksummed)
└── processed/           # Merged, cleaned, transformed data

artifacts/
├── models/              # Serialized models (pickle/joblib)
├── plots/               # PNG files
└── reports/             # Final JSON/Markdown reports
```

**Structure Decision**: Single project structure (`code/`, `tests/`, `data/`, `artifacts/`) selected to align with the linear nature of the research pipeline (Ingest -> Process -> Model -> Report). This minimizes overhead and fits the 7GB RAM constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **LMM vs. OLS** | Required to handle species-level random effects and non-independence of observations within species (FR-004, Const. VI). | Simple OLS would violate Constitution Principle VI (Cross-Species Stratified Validation) and ignore hierarchical data structure. |
| **KNN Imputation** | Required to preserve covariance structure in nutrient/root metrics (FR-003). | Mean imputation would distort variance and bias coefficient estimates, failing FR-003. |
| **Species-Level Split** | Required to prevent data leakage (FR-006, Const. VI). | Row-level splitting would allow the model to memorize species-specific traits rather than generalizing nutrient effects. |
| **Spatial Join (10km)** | Required by FR-002 to merge root and soil data when exact coordinates are missing. | Direct merge would exclude too many observations; 10km is the specified tolerance. |
| **PyYAML** | Required for loading `config.yaml` and validating schemas (FR-001, Const. III). | Hardcoding config would violate reproducibility and flexibility. |