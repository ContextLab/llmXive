# Implementation Plan: Predicting Avian Song Variation with Climatic and Geographic Factors

**Branch**: `001-predict-avian-song-variation` | **Date**: 2026-06-25 | **Spec**: `specs/001-predict-avian-song-variation/spec.md`
**Input**: Feature specification from `/specs/001-predict-avian-song-variation/spec.md`

## Summary

This project implements a computational pipeline to investigate the associational relationship between avian song metrics (frequency, duration) and environmental predictors (temperature, precipitation, elevation, latitude, longitude). The system ingests real-world avian acoustic data (Xeno-Canto) and climatic data (WorldClim v2), aligns them via geographic coordinates, performs exploratory data analysis (EDA) with multicollinearity diagnostics, fits multiple linear regression models (Model A: Climate Only; Model B: Climate + Geo), and conducts a sensitivity analysis across p-value thresholds. The entire pipeline is designed to run within GitHub Actions free-tier constraints (CPU-only, ≤7GB RAM, ≤6h runtime).

## Technical Context

**Language/Version**: Python
**Primary Dependencies**: pandas, numpy, scikit-learn, statsmodels, scipy, matplotlib, seaborn, pyyaml, requests, rasterio, geopandas, pyproj
**Storage**: Local CSV/Parquet files in `data/` and `code/` directories
**Testing**: pytest (unit tests for data loading, schema validation, model metrics)
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Computational research pipeline / CLI
**Performance Goals**: Complete ingestion, EDA, modeling, and sensitivity analysis within 1 hour on 2 CPU cores / 7GB RAM.
**Constraints**: No GPU; no causal claims (observational study); strict adherence to FR-001 through FR-006; FDR control mandatory.
**Scale/Scope**: Single dataset alignment; ~k-50k rows (sampled if necessary to fit RAM); model re-runs for sensitivity.

> **Dataset Variable Fit Note**: The spec requires `SongRecord` and `ClimateSnapshot` datasets. The implementation plan uses **real, verified datasets**: **Xeno-Canto** (avian acoustic metadata) and **WorldClim v2.1** (global climate). The pipeline fetches these directly. If fetch fails or required variables are missing, the pipeline aborts with a clear error rather than using synthetic data, ensuring compliance with the research question's validity.

## Constitution Check

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `requirements.txt` pins versions; `random_state` set in all modeling steps; data checksums recorded. |
| **II. Verified Accuracy** | PASS | Citations restricted to Xeno-Canto and WorldClim (verified sources). Pipeline aborts if real data fetch fails; no synthetic fallbacks used for primary analysis. |
| **III. Data Hygiene** | PASS | Raw data immutable; derivations written to new files; PII scan assumed passed on public metadata. |
| **IV. Single Source of Truth** | PASS | All statistics generated programmatically; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in state file; `updated_at` timestamp on artifact changes. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-avian-song-variation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── song_record.schema.yaml       # Validated by ingestion.py
    ├── climate_snapshot.schema.yaml  # Validated by ingestion.py
    └── analysis_dataset.schema.yaml  # Validated by eda.py, modeling.py
```

### Source Code (repository root)

```text
projects/PROJ-334-predicting-avian-song-variation-with-cli/
├── data/
│   ├── raw/                 # Input CSVs (SongRecord, ClimateSnapshot) - fetched from Xeno-Canto/WorldClim
│   ├── processed/           # Merged AnalysisDataset
│   └── checksums.txt        # SHA256 hashes of raw files
├── code/
│   ├── __init__.py
│   ├── ingestion.py         # FR-001: Load, align, merge (Validates against song_record.schema.yaml, climate_snapshot.schema.yaml)
│   ├── eda.py               # FR-002, FR-005: Correlation, VIF (Validates against analysis_dataset.schema.yaml)
│   ├── modeling.py          # FR-003, FR-004, FR-006: Regression, Sensitivity, FDR (Validates against analysis_dataset.schema.yaml)
│   ├── utils.py             # Helper functions
│   └── main.py              # Orchestration script
├── tests/
│   ├── test_ingestion.py
│   ├── test_eda.py
│   └── test_modeling.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure chosen to minimize overhead for a linear research pipeline. All scripts are modular but executed via a single `main.py` entry point to ensure reproducibility and sequential data flow.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The project scope is linear and data-centric. | A multi-service architecture is unnecessary for a single-file analysis pipeline. |

## Success Criteria (Updated for Magnitude & Stability)

- **SC-001**: The proportion of song recordings successfully matched with climate data is measured against the total number of recordings.
- **SC-002**: The model's predictive performance (R²) is measured against a null model, **requiring a quantifiable improvement in R² that meets the Minimum Detectable Effect Size (MDES) and demonstrates stability (Jaccard index > 0.5) across thresholds.**
- **SC-003**: The stability of the model's variable selection is measured against the threshold sweep (Jaccard index).
- **SC-004**: The multicollinearity diagnostic is measured against a standard VIF threshold..
- **SC-005**: The computational execution time is measured against the free-tier runner time limit..
