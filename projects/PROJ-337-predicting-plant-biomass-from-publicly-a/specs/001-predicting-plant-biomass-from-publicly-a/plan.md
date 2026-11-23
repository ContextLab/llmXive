# Implementation Plan: Predicting Plant Biomass from Publicly Available Hyperspectral Imagery

**Branch**: `001-predict-plant-biomass` | **Date**: 2024-05-21 | **Spec**: `specs/001-predicting-plant-biomass-from-publicly-a/spec.md`
**Input**: Feature specification from `/specs/001-predicting-plant-biomass-from-publicly-a/spec.md`

## Summary

This project implements a reproducible machine learning pipeline to predict plant biomass using publicly available hyperspectral imagery. The approach involves downloading and preprocessing the NEON dataset (and attempting HyBiomass), applying atmospheric correction (LEDAPS/FLAASH), extracting ground-truth labels, and training Random Forest and TabPFN models. The pipeline includes rigorous ablation studies to quantify the *predictive contribution* of atmospheric correction and structural complexity, followed by sensitivity analysis on feature importance. All results are benchmarked against a null baseline with statistical significance testing using the Nadeau & Bengio corrected t-test. All results are benchmarked against a null baseline with statistical significance testing and multiple-comparison corrections.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `xgboost` (as fallback), `torch` (CPU-only), `datasets` (Hugging Face), `pysptools` (or `atmcorr`), `pytest`  
**Storage**: Local file system (`data/` for raw/processed, `code/` for scripts), `data/` checksummed via SHA-256  
**Testing**: `pytest` (unit tests for data loaders, integration tests for pipeline stages)  
**Target Platform**: Linux (GitHub Actions free-tier: limited CPU, 7GB RAM, 14GB disk)  
**Project Type**: Data Science Pipeline / Research Prototype  
**Performance Goals**: Full pipeline (download → preprocess → train → evaluate) ≤ 6 hours on CPU  
**Constraints**: Memory ≤ 7GB (chunked loading), No GPU (CPU-first, TabPFN fallback), No proprietary data access  
**Scale/Scope**: ~ sites (sample) for testing; full dataset streaming for production run

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | **Pass** | Plan mandates pinned seeds, checksummed data, and isolated virtualenv. |
| II. Verified Accuracy | **Pass with Caveat** | HyBiomass source is unverified; plan attempts download but proceeds with NEON only if unavailable. All other citations verified. |
| III. Data Hygiene | **Pass** | Raw data preserved; derivations written to new files; checksums recorded. |
| IV. Single Source of Truth | **Pass** | Metrics traced to `data/` rows and `code/` blocks; no hand-typed stats. |
| V. Versioning Discipline | **Pass** | Artifacts carry content hashes; `updated_at` tracked in state YAML. |
| VI. Atmospheric Correction & Structural Integrity | **Pass** | Plan explicitly includes ablation for correction and structural features, with source independence checks. |
| VII. Public Data Signal Validation | **Pass with Caveat** | Null baseline and Nadeau & Bengio t-tests are mandated for NEON; generalizability to HyBiomass limited if data missing. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-biomass/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (finalized schemas)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-337-predicting-plant-biomass-from-publicly-a/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # FR-001: Download & checksum (incl. HyBiomass attempt)
│   │   ├── preprocess.py        # FR-002: Atmospheric correction
│   │   └── extract_labels.py    # FR-003: Ground-truth extraction (with 5% hard stop)
│   ├── models/
│   │   ├── train.py             # FR-004: RF & TabPFN training
│   │   ├── evaluate.py          # FR-005: Metrics & Nadeau & Bengio t-test
│   │   └── ablation.py          # FR-006: Ablation study
│   ├── analysis/
│   │   └── sensitivity.py       # FR-007: Sensitivity sweep
│   ├── utils/
│   │   ├── config.py            # Seed pinning, paths
│   │   ├── logger.py            # Logging exclusion rates
│   │   └── timer.py             # FR-005/SC-005: Runtime measurement
│   └── validation/
│       └── collinearity.py      # VIF checks for structural proxies
├── data/
│   ├── raw/                     # Downloaded archives (checksummed)
│   ├── processed/               # Atmospheric correction output
│   └── final/                   # Analysis-ready CSV/Parquet
├── tests/
│   ├── contract/                # Schema validation tests
│   ├── integration/             # End-to-end pipeline tests
│   └── unit/                    # Data loader tests
├── requirements.txt             # Pinned dependencies
└── README.md                    # Quickstart instructions
```

**Structure Decision**: Single-project structure with clear separation of data, models, and analysis. This aligns with the research nature of the project and simplifies reproducibility on a single runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual-model strategy (RF + TabPFN) | FR-004 mandates both; TabPFN is SOTA for small data, RF is robust fallback. | Using only RF would miss the potential signal from TabPFN; using only TabPFN risks failure without fallback. |
| Ablation study module | FR-006 requires isolating atmospheric and structural effects. | A single model run cannot quantify the specific contribution of each factor. |
| Sensitivity analysis | FR-007 requires robustness check on feature thresholds. | Fixed threshold would not reveal model stability or overfitting risks. |
| Chunked data loading | Hyperspectral cubes exceed 7GB RAM; streaming is required. | Loading full cubes would cause OOM errors on the free-tier runner. |
| Nadeau & Bengio t-test | Standard t-test on CV folds is statistically invalid (non-independent). | Using standard t-test would inflate Type I error rates. |