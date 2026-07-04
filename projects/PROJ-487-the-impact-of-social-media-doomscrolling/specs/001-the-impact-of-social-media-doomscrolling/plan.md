# Implementation Plan: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

**Branch**: `001-news-volume-anxiety` | **Date**: 2026-06-27 | **Spec**: `specs/001-news-volume-anxiety/spec.md`
**Input**: Feature specification from `/specs/001-news-volume-anxiety/spec.md`

## Summary

This feature implements a CPU-tractable time-series analysis pipeline to investigate the relationship between aggregate negative news publication volume (proxied via GDELT EventCount) and population-level anticipatory anxiety (proxied via Google Trends search volume). The system fetches raw daily data, aligns timestamps, handles missing data via forward fill, and performs stationarity/cointegration testing. If cointegrated, an Error Correction Model (ECM) is used; otherwise, differencing is applied. The system then performs correlation and Granger causality tests using AIC/BIC for lag selection and Joint F-tests, avoiding Bonferroni correction. The analysis adheres to strict reproducibility and data hygiene standards defined in the project constitution, ensuring all results are reproducible on a free-tier GitHub Actions runner (CPU, ~7 GB RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `requests`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytrends`  
**Storage**: Local CSV files in `data/raw/` and `data/processed/`; no external database required.  
**Testing**: `pytest` for unit tests on data alignment and statistical functions; integration tests via pipeline execution.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data analysis pipeline / CLI script.  
**Performance Goals**: Total runtime ≤ 6 hours; memory usage ≤ 7 GB; disk usage ≤ 14 GB.  
**Constraints**: No GPU/CUDA; no deep learning models; no large-LLM inference; strict adherence to AIC/BIC lag selection and Joint F-tests (no Bonferroni).  
**Scale/Scope**: Daily time-series data from a multi-year period; news volume and anxiety trends.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Check | Status |
|-----------|------------------|--------|
| **I. Reproducibility** | All scripts will pin random seeds; external data fetched from canonical sources (GDELT, Google Trends) via documented APIs; `requirements.txt` will pin all dependencies. | ✅ Compliant |
| **II. Verified Accuracy** | The API endpoints (GDELT, Google Trends) themselves are the primary sources and MUST be verified against the project's accuracy gate. The plan explicitly validates the source URL and documentation of these APIs as the "verified source" rather than relying on CSVs from the user message. | ✅ Compliant |
| **III. Data Hygiene** | Raw data will be saved with checksums; derivations (aligned, normalized) saved as new files; no in-place modification. | ✅ Compliant |
| **IV. Single Source of Truth** | All figures and statistics in the final report will trace back to specific rows in `data/processed/` and code blocks in `code/`. | ✅ Compliant |
| **V. Versioning Discipline** | Artifacts will carry content hashes; state file updated on artifact changes. | ✅ Compliant |
| **VI. Temporal Data Alignment** | Lag windows are determined algorithmically via AIC/BIC criteria with sensitivity analysis across short-term intervals ranging from one day to two weeks. The plan explicitly documents the algorithmic selection process and sensitivity analysis results in `research.md` and `code/`. | ✅ Compliant |

## Project Structure

### Documentation (this feature)

```text
specs/001-news-volume-anxiety/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/
├── data/
│   ├── fetch_gdelt.py
│   ├── fetch_google_trends.py
│   ├── preprocess.py
│   └── analyze.py
├── tests/
│   ├── test_preprocess.py
│   └── test_analyze.py
├── utils/
│   └── logging.py
├── requirements.txt
└── main.py

projects/PROJ-487-the-impact-of-social-media-doomscrolling/data/
├── raw/
│   ├── gdelt_events.csv
│   └── google_trends.csv
└── processed/
    ├── aligned_timeseries.csv
    └── stationarity_check.csv
```

**Structure Decision**: Single project structure chosen for simplicity and direct alignment with the data pipeline nature of the feature. No frontend/backend split required; all logic resides in `code/` with data in `data/`.

**Schema Traceability**: The schema files in `contracts/` (`dataset.schema.yaml`, `output.schema.yaml`) are the machine-readable implementation of the entities (`TimeSeriesRecord`, `AnalysisResult`) defined in `data-model.md`. The `pyyaml` library is explicitly used in `preprocess.py` and `analyze.py` to validate data against these contracts during pipeline execution, ensuring Data Hygiene and SSoT principles.

**Complexity Tracking**: No violations detected. The single-project structure is sufficient for the data pipeline scope.