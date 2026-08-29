# Implementation Plan: Correlational Analysis of Climate‑Smart Agricultural Practices and Yield Stability Independent of Financial Access

**Branch**: `001-climate-smart-eval` | **Date**: 2026-08-14 | **Spec**: `specs/001-climate-smart-eval/spec.md`
**Input**: Feature specification from `/specs/001-climate-smart-eval/spec.md`

## Summary

This project implements a multivariate correlational analysis to assess the marginal effect of Climate-Smart Agricultural (CSA) practices on yield stability and food security in smallholder systems, explicitly controlling for financial access. The methodology relies on classical statistics (linear regression with Cluster-Robust Standard Errors) applied to a harmonized dataset linking World Bank LSMS-ISA survey data with Sentinel-2 satellite imagery. The analysis is strictly observational, framed as associational, and includes rigorous diagnostics for collinearity (VIF), multiple hypothesis correction (Bonferroni), and sensitivity to cloud-cover thresholds and spatial fuzzing radii.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `geopandas`, `rasterio`, `requests`, `pyyaml`, `synth-pop`
**Storage**: Local file system (`data/raw/`, `data/processed/`)
**Testing**: `pytest` (unit, integration, contract)
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple CPU cores, a moderate amount of RAM, and a moderate amount of disk space.
The research question and method remain unchanged as per the planning document requirements.)
**Project Type**: Data Science / Statistical Analysis Pipeline
**Performance Goals**: Complete full pipeline (ingest -> model -> report) within 6 hours; regression models must run on CPU without GPU acceleration.
**Constraints**: 
- No GPU available on primary runner; no deep learning models.
- Data must be streamed or sampled to fit available RAM.
- LSMS-ISA coordinates are fuzzed; spatial join must handle approximate matching (handled by `src/data/spatial_join.py`).
- All results must be reproducible with pinned random seeds.
- **Synthetic Fallback**: If real data is unavailable, a statistically realistic synthetic dataset is generated for CI validation.
**Scale/Scope**: Target N > 1000 households (or village-level aggregation if N < 300); analysis of primary models and Multiple sensitivity sweeps (cloud cover, fuzzing radius).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds pinned in `src/config/constants.py`. External datasets fetched via canonical URLs (where available) or generated via the `src/data/generators/synthetic_generator.py` if real data is missing. `requirements.txt` pins every dependency. |
| **II. Verified Accuracy** | Citations in `research.md` are verified by the Reference-Validator Agent. **Blocking Gate**: The pipeline halts if any citation fails the title-overlap check or if the source is unreachable. |
| **III. Data Hygiene** | Raw data preserved in `data/raw/` with checksums recorded in `state/`. Derived data in `data/processed/` with clear derivation logs. PII scan enforced on commits. |
| **IV. Single Source of Truth** | All statistics in the final report will be generated programmatically from `data/processed/analysis_dataset.csv` and `src/analysis/`. No hand-typed numbers. |
| **V. Versioning Discipline** | Content hashes for the following artifacts are recorded in `state/projects/PROJ-006-agriculture-optimization.yaml`: `data/raw/*`, `data/processed/*`, `src/`, `contracts/`, `reports/`. |
| **VI. Multi-Source Validation Independence** | Predictor (CSA Index) derived from survey; Outcome (NDVI_CV) derived from satellite. No tautological derivation. |
| **VII. Spatial-Temporal Alignment Rigor** | `src/data/spatial_join.py` documents geospatial fuzzing (default spatial resolution) and temporal windows (growing season) for NDVI aggregation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-climate-smart-eval/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── cli/
│   ├── run_pipeline.py      # Orchestrates the full workflow
│   └── validate.py          # Validates data against contracts
├── config/
│   ├── constants.py         # Random seeds, paths, thresholds
│   └── schemas.py           # Contract definitions (if needed in code)
├── data/
│   ├── collectors/
│   │   ├── survey_collector.py    # Handles LSMS-ISA logic
│   │   └── remote_sensing_collector.py # Handles Sentinel-2 logic
│   ├── generators/
│   │   └── synthetic_generator.py # Generates mock data for CI
│   └── processing/
│       ├── spatial_join.py        # Links survey to satellite
│       └── feature_engineering.py # Constructs CSA Index, NDVI_CV
├── models/
│   └── regression_models.py       # Defines and fits statsmodels OLS
├── services/
│   ├── diagnostics.py             # VIF calculation, robust SE
│   └── sensitivity.py             # Cloud cover & fuzzing sweep
└── utils/
    └── io_helpers.py              # CSV/Parquet I/O, logging

data/
├── raw/                           # Downloaded raw data (checksummed)
└── processed/
    └── analysis_dataset.csv       # Final analysis-ready data

tests/
├── contract/                      # Schema validation tests
├── integration/                   # Pipeline end-to-end tests
└── unit/                          # Function-level tests

contracts/
├── dataset.schema.yaml
└── output.schema.yaml
```

**Structure Decision**: Selected Option 1 (Single project) with a clear separation of concerns (`data/`, `models/`, `services/`) to support the modular testing requirements (Unit, Integration, Contract) mandated by the spec and previous reviewer feedback. **Note**: `contracts/` is located at the project root, not inside `specs/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sensitivity Analysis Sweep** | Spec FR-006 requires testing cloud cover thresholds {, 0.8, and other representative values}. | A single threshold run would fail to meet the robustness requirement and the spec's acceptance criteria (SC-005). |
| **Cluster-Robust SEs** | Spec FR-004 and FR-005 require handling spatial autocorrelation from fuzzing. | Standard OLS would violate the statistical rigor requirements for heteroskedasticity and spatial clustering. |
| **Village-Level Aggregation** | Spec requires fallback if N < 300. | A hard failure would prevent the study from producing results in low-overlap scenarios, violating the "feasibility" constraint. |
| **Synthetic Generator** | CI reproducibility requires data availability without manual intervention. | A "Fail Fast" strategy prevents automated validation of the statistical pipeline. |