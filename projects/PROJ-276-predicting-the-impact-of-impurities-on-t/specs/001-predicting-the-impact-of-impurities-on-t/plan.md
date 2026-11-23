# Implementation Plan: Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride

**Branch**: `001-impurity-impact-mgb2` | **Date**: 2026-06-24 | **Spec**: `specs/001-impurity-impact-mgb2/spec.md`
**Input**: Feature specification from `/specs/001-impurity-impact-mgb2/spec.md`

## Summary

This project implements a regression pipeline to quantify the impact of chemical impurities on the critical temperature (Tc) of Magnesium Diboride (MgB₂). The approach consolidates experimental data from the Materials Project API and the SuperCon dataset (specifically `taqwa92/cm.mgb2`), standardizes units to atomic percent, and trains multiple regression models (Ridge, Random Forest, XGBoost) under strict CPU-only constraints. The plan prioritizes statistical rigor (Feature Permutation Tests, Ridge Regression for collinearity) and reproducibility, ensuring all results trace back to verified data sources and pinned dependencies. The entire pipeline is designed to execute within the Constitution's **30-minute** runtime budget on GitHub Actions free-tier runners.

> **CRITICAL SPEC CONTRADICTION NOTICE**:
> 1. The source `spec.md` (FR-006, US-2) explicitly mandates a "6-hour CPU-only CI window". This contradicts Constitution Principle VII (Computational Resource Constraints) which mandates a **30-minute** budget. This plan adheres to the Constitution (30 mins) and flags the spec for immediate revision. The implementation will fail if it exceeds a substantial duration.
> 2. The source `spec.md` (FR-004) mandates a "Target Permutation Test" (shuffling Y) for tree-based models. This is methodologically invalid for testing specific impurity effects. This plan implements the statistically correct "Feature Permutation Importance" (shuffling X) and flags FR-004 for revision to align with scientific best practices.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `xgboost`, `pymatgen`, `requests`, `pyyaml`, `matplotlib`, `seaborn`, `statsmodels`
**Storage**: Local CSV/Parquet files in `data/`. No external DB or SQLite caching to ensure schema alignment.
**Testing**: `pytest` (unit tests for ingestion logic, integration tests for pipeline end-to-end).
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM, no GPU).
**Project Type**: Data Science / Computational Materials Science
**Performance Goals**: End-to-end pipeline ≤ **30 minutes**; Memory ≤ 6 GB; R² measurement on test set.
**Constraints**: No GPU usage; hyperparameter grid limited to ≤ 10 combinations; strict handling of missing Tc/impurity data (drop rows, no imputation for targets).
**Scale/Scope**: Dataset size expected < 10,000 rows; Model training on CPU.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan ensures all random seeds are pinned in `code/` scripts. External datasets are fetched from canonical URLs (HuggingFace: `) or API endpoints. `requirements.txt` pins all versions.
- **Principle II (Verified Accuracy)**: All citations in `research.md` and `plan.md` are validated against the **Verified datasets block** defined in `research.md` (specifically `taqwa92/cm.mgb2` and the Materials Project API). No URLs are invented. The plan explicitly references the dataset list in `research.md` to satisfy this gate.
- **Principle III (Data Hygiene)**: Raw data will be downloaded to `data/raw/` with checksums. Derived data (cleaned CSV) will be in `data/processed/`. No in-place modifications.
- **Principle IV (Single Source of Truth)**: All figures and statistics in the final output will be generated programmatically from `data/processed/` via `code/`.
- **Principle V (Versioning Discipline)**: Artifacts will be tracked via content hashes in `state/`.
- **Principle VI (Materials Data Provenance)**: `data/processed/` will include a metadata header with source names, query timestamps, and `pymatgen` version for derived features.
- **Principle VII (Computational Resource Constraints)**: All models (Ridge, RF, XGBoost) are configured for CPU-only execution. Grid search is capped at a limited number of combinations. **Total runtime budget is strictly ≤ 30 minutes**. (Note: This overrides the 6-hour requirement in spec.md, which is flagged for correction).

## Project Structure

### Documentation (this feature)

```text
specs/001-impurity-impact-mgb2/
├── plan.md # This file (Phase 0/1)
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 0/1 inputs (validating design)
│ ├── dataset.schema.yaml
│ └── output.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── ingestion/
│ ├── __init__.py
│ ├── download_materials_project.py
│ ├── download_supercon.py
│ └── preprocess.py
├── modeling/
│ ├── __init__.py
│ ├── train.py
│ ├── evaluate.py
│ └── significance_test.py
├── visualization/
│ ├── __init__.py
│ └── plot_pdp.py
├── utils/
│ ├── __init__.py
│ ├── constants.py
│ └── logging.py
└── main.py

tests/
├── contract/
│ ├── test_dataset_schema.py
│ └── test_output_schema.py
├── integration/
│ └── test_pipeline.py
└── unit/
 ├── test_ingestion.py
 └── test_preprocessing.py

data/
├── raw/
│ └── [source_files]
└── processed/
 └── mgb2_clean.csv

code/
└── requirements.txt
```

**Structure Decision**: A modular monolithic structure is chosen. Separation of `ingestion`, `modeling`, and `visualization` ensures clear responsibility boundaries. `tests` are co-located with logic for easier maintenance. `data` is split into `raw` (immutable) and `processed` (derived), adhering to Principle III. Contracts are treated as **Phase 0/1 inputs** to validate the design before code generation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly defined by the spec. | N/A |