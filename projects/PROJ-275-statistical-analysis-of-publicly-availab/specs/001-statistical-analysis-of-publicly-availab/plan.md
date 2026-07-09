# Implementation Plan: Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue

**Branch**: `001-sentiment-revenue-lag-analysis` | **Date**: 2026-07-10 | **Spec**: `specs/001-sentiment-revenue-lag-analysis/spec.md`
**Input**: Feature specification from `/specs/001-sentiment-revenue-lag-analysis/spec.md`

## Summary

This feature implements a CPU-tractable statistical pipeline to analyze the temporal lag and decay of sentiment-revenue correlation in movies. It ingests the TMDB 5000 and IMDb datasets, aligns them temporally, computes weekly sentiment scores using VADER, and performs a **Lagged Correlation Profile** analysis (instead of per-movie CCF) stratified by genre. The implementation strictly adheres to GitHub Actions free-tier constraints (CPU-only, <7GB RAM, <6h runtime) and corrects for data limitations where weekly revenue is unavailable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scikit-learn, nltk (vaderSentiment), scipy, statsmodels, fuzzywuzzy  
**Storage**: Local filesystem (`data/`), CSV/Parquet intermediates  
**Testing**: pytest (unit tests for data alignment, lag calculation, decay logic, schema validation)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Complete pipeline execution in < 4 hours; memory footprint < 6GB.  
**Constraints**: No GPU usage; no large language models; strict data versioning; all statistical claims must be backed by bootstrap or Fisher Z-transformation methods.  
**Scale/Scope**: A filtered dataset of several hundred to several thousand movies will be utilized to investigate [Research Question] using [Method], as supported by [References].; -week time-series per movie (sentiment only).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds pinned in `code/`. Dependencies pinned in `code/requirements.txt`. Data fetched from verified HuggingFace URLs only. |
| **II. Verified Accuracy** | Citations in `research.md` restricted to the "Verified datasets" block. No fabricated URLs. **Verified Accuracy Gate** implemented in pipeline. |
| **III. Data Hygiene** | Raw data stored in `data/raw/` with checksums. Derived data in `data/processed/` with explicit lineage. No in-place modification. |
| **IV. Single Source of Truth** | Final report figures generated directly from `code/` outputs. No manual transcription of stats. |
| **V. Versioning Discipline** | Content hashes recorded in `state/`. Artifact changes trigger `updated_at` updates. |
| **VI. Temporal and Genre-Stratified Analysis** | Pipeline explicitly models lag (via Lagged Correlation Profile) and decay (aggregate trend) and stratifies by genre (FR-005). Handles "Unknown" genre. |
| **VII. Distinct Signal Validation** | Sentiment derived from text (IMDb), revenue from financial records (TMDB). Lag calculation prevents signal leakage by using static revenue vs. time-varying sentiment. |

## Project Structure

### Documentation (this feature)

```text
specs/001-sentiment-revenue-lag-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── analysis_results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data_ingestion.py        # Downloads and merges datasets (FR-001, FR-002)
├── sentiment_analysis.py    # VADER scoring and weekly aggregation (FR-003)
├── lag_decay_analysis.py    # Lagged Correlation Profile, bootstrap, Fisher Z (FR-004, FR-005, FR-006)
├── reporting.py             # Generates tables and plots (FR-007)
├── requirements.txt         # Pinned dependencies (located at code/requirements.txt)
├── main.py                  # Orchestration script
└── tests/                   # Unit tests validating against contracts/
```

**Structure Decision**: Single-project structure (`code/`) selected. The project is a linear data pipeline (Ingest -> Process -> Analyze -> Report) rather than a service, making a monolithic script structure with modular functions most efficient for the 6-hour runtime constraint.

## Complexity Tracking

No violations detected. The approach uses standard CPU-tractable libraries (pandas, scipy) and avoids heavy ML training. The "Lagged Correlation Profile" method is computationally efficient and valid for the static-outcome data structure.

## Verified Accuracy Gate

To satisfy Constitution Principle II, the pipeline includes a mandatory blocking step:
1. **Pre-Execution**: The `Reference-Validator` agent (simulated or integrated) scans `research.md` and `plan.md` for all dataset URLs.
2. **Validation**: It verifies that each URL exists, matches the "Verified datasets" block, and that the dataset schema matches the expected fields.
3. **Action**: If any citation is unreachable, mismatched, or fabricated, the pipeline **HALTS** with a `VALIDATION_ERROR` and logs the specific failure. No data is downloaded or processed until this gate passes.

## Contract Validation

Unit tests in `code/tests/` explicitly validate intermediate and final outputs against the schemas defined in `contracts/`:
- `test_dataset_schema.py`: Validates `data/processed/merged.parquet` against `contracts/dataset.schema.yaml`.
- `test_analysis_results_schema.py`: Validates `results/analysis_results.csv` against `contracts/analysis_results.schema.yaml`.
- Failure to match the schema results in a test failure, preventing the generation of a final report.