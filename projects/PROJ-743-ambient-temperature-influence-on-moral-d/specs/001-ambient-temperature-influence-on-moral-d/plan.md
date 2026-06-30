# Implementation Plan: Ambient Temperature Influence on Moral Decision Speed

**Branch**: `001-ambient-temp-moral-speed` | **Date**: 2026-06-24 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-ambient-temp-moral-speed/spec.md`

## Summary

This feature implements a statistical analysis pipeline to quantify the association between ambient temperature and moral decision response time using the Moral Machine dataset. The approach involves ingesting raw response data, merging it with historical land-based temperature data (NOAA GHCN-Daily or ERA5-Land) via geographic coordinates or administrative regions, and fitting a Linear Mixed-Effects Model (LMM) or Generalized Estimating Equation (GEE) depending on the data structure. The model controls for participant demographics and dilemma complexity. Robustness checks include alternative temperature metrics and sensitivity analyses for outliers and non-linearity. All analysis is constrained to run on CPU-only GitHub Actions runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `requests`, `pyyaml`, `seaborn`, `matplotlib`, `geopandas`  
**Storage**: Local CSV/Parquet files in `data/` and `results/`  
**Testing**: `pytest` (unit tests for data ingestion, integration tests for model convergence)  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7 GB RAM)  
**Project Type**: Data Science / Statistical Analysis  
**Performance Goals**: Complete full pipeline (ingest -> model -> plot) within 4 hours; memory usage < 6 GB.  
**Constraints**: No GPU; no large language models; dataset must be sampled if raw size exceeds RAM (stratified by region); all random seeds pinned.  
**Scale/Scope**: ~M+ Moral Machine records (requires sampling or chunked processing); ~k NOAA station lookups.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| I. Reproducibility | **Compliant** | Random seeds will be pinned in `code/`. External datasets fetched from canonical sources. |
| II. Verified Accuracy | **Compliant** | Citations in `research.md` strictly use verified URLs (Harvard Dataverse for Moral Machine, ERA5-Land/NOAA GHCN for temperature). |
| III. Data Hygiene | **Compliant** | Raw data preserved; derivations written to new files with checksums recorded. |
| IV. Single Source of Truth | **Compliant** | All figures/stats trace to `data/` and `code/`. No hand-typed numbers in paper. |
| V. Versioning Discipline | **Compliant** | Artifacts carry content hashes; `updated_at` timestamps managed by state file. |
| VI. Dataset Alignment Integrity | **Compliant** | Matching script logs station identifier, timestamp, and exclusion reasons. Logic changes trigger version bump. |
| VII. Statistical Modeling Transparency | **Compliant** | LMM/GEE implementation, fixed/random effects, and diagnostics explicitly scripted and saved. |

## Project Structure

### Documentation (this feature)

```text
specs/001-ambient-temp-moral-speed/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-743-ambient-temperature-influence-on-moral-d/
├── code/
│   ├── __init__.py
│   ├── config.py                # Paths, seeds, thresholds
│   ├── ingestion.py             # FR-001, FR-002, FR-009, FR-010: Data loading & merging
│   ├── modeling.py              # FR-003, FR-004, FR-005, FR-011, FR-013: LMM/GEE fitting
│   ├── robustness.py            # FR-006, FR-012: Sensitivity & robustness checks
│   ├── plots.py                 # FR-007, FR-008: Diagnostic & result visualization
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded Moral Machine & NOAA data
│   ├── processed/               # Merged & cleaned datasets
│   └── checksums.yaml           # Recorded hashes
├── results/
│   ├── figures/                 # Generated plots
│   └── logs/                    # Model diagnostics, data quality logs
├── tests/
│   ├── test_ingestion.py
│   ├── test_modeling.py
│   └── test_robustness.py
└── requirements.txt
```

**Structure Decision**: Single-project structure selected. The analysis pipeline is linear (Ingest -> Merge -> Model -> Validate). A monolithic `code/` directory with modular scripts is sufficient and avoids unnecessary complexity. `data/` and `results/` are strictly separated to enforce Data Hygiene (Constitution Principle III).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-Effects Modeling / GEE | Required by FR-003 to account for non-independence of repeated measures (if present) or clustering by participant. If no repeated measures, GEE with clustered SEs is used. | Fixed-effects OLS would yield biased standard errors and invalid p-values due to clustering. |
| Log-Transformation / GLMM | Required by US-2 to handle the non-normal distribution of response times. | Raw response times are heavily skewed; linear models on raw data violate normality assumptions (Constitution Principle VII). |
| Land-Based Temperature Data | Required by FR-001 to link ambient temperature to specific decision events in urban/rural areas. | NOAA Buoy data is marine-only; using it for global land responses is a fundamental modality mismatch. |