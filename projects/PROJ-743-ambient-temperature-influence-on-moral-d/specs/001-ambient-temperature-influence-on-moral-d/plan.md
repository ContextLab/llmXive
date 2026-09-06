# Implementation Plan: Ambient Temperature Influence on Moral Decision Speed

**Branch**: `001-ambient-temp-moral-speed` | **Date**: 2026-06-24 | **Spec**: `specs/001-ambient-temp-moral-speed/spec.md`
**Input**: Feature specification from `/specs/001-ambient-temp-moral-speed/spec.md`

## Summary

This feature implements a statistical analysis pipeline to investigate the correlation between ambient temperature and moral decision-making speed using the Moral Machine dataset merged with ERA Reanalysis data. The technical approach involves:
1.  **Data Ingestion**: Downloading the Moral Machine dataset and fetching hourly ERA temperature data for the specific -2018 period via the Copernicus Climate Data Store (CDS) API.
2.  **Preprocessing**: Filtering impossible response times, handling missing data, and calculating derived covariates (dilemma complexity, time-of-day, urban/rural proxy).
3.  **Statistical Modeling**: Fitting Linear Mixed-Effects Models (LMM) with log-transformed response times, controlling for participant ID and cultural region, and testing for non-linearity.
4.  **Robustness**: Performing sensitivity analyses on temperature thresholds, outlier definitions, and urban/rural stratification.
5.  **Validation**: Generating diagnostic plots and ensuring reproducibility via checksums and pinned dependencies.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels` (for mixed-effects), `cdsapi` (for ERA5), `geopy`, `pyarrow` (for parquet), `matplotlib`, `seaborn`, `requests`.  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `results/`). Parquet for intermediate merged data.  
**Testing**: `pytest` with `pytest-cov` for code coverage; unit tests for data matching logic.  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, ~7GB RAM).  
**Project Type**: Data Analysis / Statistical Research Pipeline.  
**Performance Goals**: Process the merged dataset (estimated on the order of several gigabytes for the 2014‑2018 ERA5 subset.) within 4 hours on CPU; model convergence within 30 minutes.  
**Constraints**: Must run on CPU-only environment; ERA data must be streamed/fetched in chunks to fit memory; no PII allowed in logs.  
**Scale/Scope**: ~k moral decisions (Moral Machine), A subset of ERA5 data (2014-2018).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | `requirements.txt` pins all versions; random seeds set in `code/`; data fetched from canonical CDS API (ERA5) and Moral Machine. |
| **II. Verified Accuracy** | ✅ Pass | Dataset URLs and API endpoints verified; ERA source covers the Moral Machine period beginning in the mids., resolving temporal mismatch. |
| **III. Data Hygiene** | ✅ Pass | Checksums recorded in `state/`; raw data immutable; derived files in `data/processed/`; PII scan in CI. |
| **IV. Single Source of Truth** | ✅ Pass | All stats trace to `results/stats/` JSON/CSV; figures trace to `results/figures/`. |
| **V. Versioning** | ✅ Pass | Artifacts hashed; `state` updated on change. |
| **VI. Dataset Alignment** | ✅ Pass | Matching logic logs `grid_id`, timestamp, and exclusion reasons (`data_quality_log`). Uses ERA grid points (not 'station ID'). |
| **VII. Statistical Modeling** | ✅ Pass | Fixed/Random effects explicitly listed; diagnostics saved to `results/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-ambient-temp-moral-speed/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, thresholds
├── ingestion.py         # Moral Machine + ERA5 merge logic
├── preprocessing.py     # Filtering, outlier removal, feature engineering
├── modeling.py          # LMM/GLMM fitting, diagnostics
├── robustness.py        # Sensitivity analysis
├── validate_sources.py  # Pre-ingestion validation (FR-014)
└── utils.py             # Logging, checksum helpers

data/
├── raw/
│   ├── moral_machine.csv.gz (or original format)
│   └── era5_data/           # Streamed chunks or downloaded shards (2014-2018)
├── processed/
│   ├── merged_dataset.parquet
│   └── data_quality_log.json
└── external/
    └── checksums.txt

results/
├── figures/
│   ├── residual_qq.png
│   ├── residual_vs_fitted.png
│   └── temp_effect_plot.png
├── logs/
│   ├── processing_log.txt
│   └── validation_report.json
└── stats/
    ├── model_results.json
    └── sensitivity_analysis.csv

tests/
├── test_ingestion.py
├── test_preprocessing.py
└── test_modeling.py
```

**Structure Decision**: Single-project structure selected. The pipeline is linear (Ingest -> Process -> Model -> Report), making a monolithic `code/` directory with modular scripts appropriate. No separate backend/frontend is needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Model** | Participant ID is a random effect to account for repeated measures. | Simple OLS would ignore clustering, inflating Type I error. |
| **Streaming ERA5** | Full ERA dataset exceeds RAM (GB). | Downloading full dataset to disk would fail on CI runner; streaming is required. |
| **Log-transformation** | Response times are highly skewed. | Raw response times violate normality assumptions of LMM. |
| **CDS API Fetch** | Requires specific 2014-2018 data. | Static datasets (e.g., WorldClim) lack temporal validity for instantaneous arousal. |
