# Implementation Plan: Predicting Perovskite Stability via Compositional Fingerprints

**Branch**: `001-predicting-perovskite-stability` | **Date**: 2026-06-28 | **Spec**: `specs/001-predicting-perovskite-stability/spec.md`
**Input**: Feature specification from `/specs/001-predicting-perovskite-stability/spec.md`

## Summary

This project implements a predictive pipeline to determine the thermal decomposition temperature ($T_d$) of metal halide perovskites based solely on their elemental composition. The technical approach involves ingesting experimental data from NREL, computing compositional descriptors (atomic fractions, weighted ionic radii, electronegativity, formation enthalpy, ionization energy), and training baseline regression models (Random Forest, Gradient Boosting, Elastic Net) under strict CPU-only constraints. The plan prioritizes data hygiene, statistical rigor (VIF diagnostics, permutation testing), and external validation on held-out literature data (or family-based proxy).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `requests`, `pyyaml`, `numpy`, `pymatgen` (for formula parsing)  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed)  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7 GB RAM)  
**Project Type**: data-science-pipeline  
**Performance Goals**: Complete full pipeline (ingest, train, validate) within 4 hours (budget 6h).  
**Constraints**: No GPU/CUDA; grid search limited to ≤10 combinations per model; VIF > 5 triggers feature removal or Elastic Net fallback; external validation required for OOD assessment.  
**Scale/Scope**: Target dataset size ≤500 entries; Multiple compositional descriptors (including ionization energy).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned random seeds in `code/`, canonical source fetching for all datasets, and a `requirements.txt` for isolated environments. Formula parsing uses `pymatgen` for deterministic site assignment.
- **II. Verified Accuracy**: The ingestion script performs HTTP reachability checks AND 'title-token-overlap' validation against the primary source citation (NREL) before processing data, as required by Constitution Principle II.
- **III. Data Hygiene**: The plan enforces checksumming of raw data, immutable derivations, and exclusion of PII.
- **IV. Single Source of Truth**: The `data-model.md` defines the schema for derived data; the `contracts/` directory (specifically `contracts/descriptor.schema.yaml`) is the implementation of this SSoT, ensuring figures/stats trace back to specific rows.
- **V. Versioning Discipline**: The plan includes a dedicated task to compute SHA-256 hashes for derived artifacts (`descriptors.csv`, `model_runs.json`) and write them to the `state/...yaml` file after generation.
- **VI. Computational-Budget Discipline**: Grid search is explicitly capped at ≤10 combinations per model to ensure the 6-hour runtime limit is respected on free-tier runners.
- **VII. Statistical-Rigor Requirement**: The plan includes VIF diagnostics (threshold 5, with feature removal/Elastic Net fallback), -permutation testing (p < 0.05, Benjamini-Hochberg correction), and stratified splits by perovskite family. Success criteria (R² ≥ 0.6, R² < 0.3) are explicitly mapped to permutation test results.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-perovskite-stability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-516-predicting-perovskite-stability-via-comp/
├── code/
│   ├── requirements.txt
│   ├── data_ingestion.py
│   ├── feature_engineering.py
│   ├── model_training.py
│   ├── validation.py
│   ├── state_manager.py  # Updates state/...yaml with hashes
│   └── main.py
├── data/
│   ├── raw/
│   └── processed/
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
    └── ...
```

**Structure Decision**: A linear pipeline structure (`data_ingestion` → `feature_engineering` → `model_training` → `validation`) is selected to ensure data flows strictly from raw to processed to model, satisfying the "Data Hygiene" and "Single Source of Truth" principles. This minimizes state coupling and simplifies reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within a single data science pipeline. | N/A |