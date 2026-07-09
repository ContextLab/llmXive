# Implementation Plan: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

**Branch**: `001-assessing-orbital-period-dependence` | **Date**: 2026-06-28 | **Spec**: [link]
**Input**: Feature specification from `specs/001-assessing-orbital-period-dependence/spec.md`

## Summary

This project implements a statistical pipeline to assess the dependence of the exoplanet radius gap on orbital period using Kepler DR25 data. The approach involves downloading and cleaning the Kepler catalog (including completeness weights), binning planets by log-period, fitting two-component Gaussian Mixture Models (GMM) to identify gap locations, validating via Synthetic Ground Truth, and comparing the measured slope against theoretical predictions (Photoevaporation vs. Core-Powered Mass Loss) via a Permutation Test. The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `astropy`, `requests`, `tqdm` (CPU-optimized, no GPU/CUDA).  
**Storage**: Local CSV/Parquet files under `data/` (derived from raw MAST downloads).  
**Testing**: `pytest` with unit tests for filtering logic, GMM fitting stability, and regression calculations.  
**Target Platform**: Linux server (GitHub Actions `ubuntu-latest`).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Complete full analysis (download, clean, GMM, regression, validation) in ≤ 6 hours on 2 CPU cores, ~7 GB RAM.  
**Constraints**: No GPU acceleration; strict memory management (streaming/chunking if needed); **NO FABRICATED DATA** — all results must be derived from real Kepler observations. The pipeline must fail if the dataset is empty or synthetic.  
**Scale/Scope**: Processing ~[deferred] confirmed Kepler planets (Based on Kepler DR25 confirmed planet count).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External datasets fetched from canonical MAST sources via scripts. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations to Kepler DR25 and Input Catalogs will be validated against primary sources (MAST archive) before use. No secondary summaries used for core data. |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with checksums. Derived data written to `data/processed/` with new filenames. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in the final report will be generated programmatically from `data/processed/` via `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for all artifacts in `data/` and `code/` will be recorded in `state/projects/PROJ-787-assessing-orbital-period-dependence-of-t.yaml` via an automated update script. |
| **VI. Statistical Gap Detection Rigor** | **PASS** | GMM (2-component) with BIC selection (BIC difference > 10 required) and **1000+ bootstrap resamples**. KDE validation (internal consistency) AND **Synthetic Ground Truth** validation (accuracy). Minimum 30 planets per bin. Bins failing BIC check are flagged 'UNRESOLVED' and **excluded** from regression. |
| **VII. Period-Binning Integrity** | **PASS** | Log-spaced bins (lower bound to 100 days). Minimum 30 planets enforced. **Weighted linear regression** (errors-in-variables) on log(period) vs gap radius. **Permutation test** for theory comparison. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-orbital-period-dependence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-787-assessing-orbital-period-dependence-of-t/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, thresholds, seeds
│   ├── data/
│   │   ├── download.py        # MAST fetching with retries
│   │   ├── clean.py           # Filtering & deduplication
│   │   └── bin.py             # Log-binning logic
│   ├── analysis/
│   │   ├── gmm.py             # GMM fitting & bootstrapping
│   │   ├── kde.py             # KDE validation
│   │   └── regression.py      # Weighted regression & theory comparison
│   └── main.py                # Pipeline orchestrator
├── data/
│   ├── raw/                   # Downloaded CSVs (checksummed)
│   └── processed/             # Cleaned CSVs, bin results
├── tests/
│   ├── unit/
│   │   ├── test_clean.py
│   │   └── test_gmm.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead for a data analysis pipeline. Modular separation of data ingestion, cleaning, analysis, and orchestration ensures testability and maintainability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project adheres strictly to the spec and constitution. | N/A |

## Phased Implementation Plan

### Phase 0: Data Ingestion & Cleaning
- Download Kepler DR25, Input Catalog (KIC), and **Kepler Completeness Map**.
- Apply strict filtering (radius <20%, period <1% uncertainty).
- Deduplicate and merge stellar parameters.
- **Apply completeness map weights** to each planet record.
- **Output**: `data/processed/cleaned_planets.csv`

### Phase 1: Binning & Gap Detection
- Bin planets by log-period (5-100 days).
- Merge bins with <30 planets.
- Fit 2-component GMM; check BIC difference > 10.
- **Exclude 'UNRESOLVED' bins** (BIC fail or GMM divergence) from regression.
- Bootstrap (sufficient iterations) for gap location uncertainty.
- **Output**: `data/processed/binned_results.csv`

### Phase 2: Regression & Theory Comparison
- Perform weighted linear regression (errors-in-variables) on 'PASS' bins only.
- Generate theoretical slope distributions via Monte Carlo (stellar + **model parameter** uncertainties).
- Compare measured slope vs theoretical distributions using **Permutation Test**.
- **Output**: `data/processed/final_analysis_results.json`

### Phase 3: Sensitivity Analysis & Validation
- **Synthetic Validation**: Generate synthetic data with known gap slope; run full pipeline; measure recovery error (Accuracy check).
- **Sensitivity**: Re-run full pipeline with KDE as primary method; compare results (Stability check).
- **Bin Width Sensitivity**: Re-run with varied bin widths to check for binning bias.
- **Output**: `reports/summary.md` with validation status.
