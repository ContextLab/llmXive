# Implementation Plan: Exploring the Relationship Between Cosmic Ray Composition and Solar Activity Cycles

**Branch**: `001-cosmic-ray-composition-solar-cycle` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-exploring-the-relationship-between-cosmi/spec.md`

## Summary

This project implements a computational pipeline to analyze the relationship between cosmic ray composition (protons, helium, heavy nuclei) and solar activity cycles (sunspot numbers) using data from the recent solar cycle. The technical approach involves retrieving rigidity-binned differential flux data from the AMS-02 repository (using the most granular available public data), aligning it with solar activity indices, computing composition ratios, performing time-lagged correlation analyses with effective degrees of freedom correction, and validating results via Moving Block Bootstrap resampling and diffusion model fitting. The implementation is constrained to CPU-only execution on a GitHub Actions free-tier runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `matplotlib`, `requests`, `pyyaml`, `statsmodels`  
**Storage**: Local CSV/Parquet files under `data/`  
**Testing**: `pytest` for unit tests on data alignment and statistical functions  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: CLI/Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (retrieval, alignment, correlation, bootstrap, fitting) within 6 hours  
**Constraints**: CPU-only, ≤7 GB RAM, ≤14 GB disk, no GPU, no large model training  
**Scale/Scope**: Daily/Weekly/Monthly data points from a multi-year period (depending on data availability), multiple rigidity bins, 1000 bootstrap iterations  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Random seeds will be pinned in `code/`. External datasets will be fetched from canonical sources (verified URLs) on every run.
- **II. Verified Accuracy**: All external citations in `research.md` MUST resolve to verified URLs found in the "# Verified datasets" block. If a required dataset (e.g., specific AMS-02 heavy nuclei daily data) has no verified URL, the analysis will be restricted to available verified datasets or halted. No "fallback to name only" is permitted.
- **III. Data Hygiene**: All files under `data/` will be checksummed (SHA-256). Raw data preserved; derivations written to new filenames.
- **IV. Single Source of Truth**: Every figure/statistic in the paper MUST trace back to a specific file hash in `data/` and a specific code block in `code/`. The `state/` artifact map will record these hashes to ensure no hand-typed numbers appear in the paper.
- **V. Versioning Discipline**: Every artifact carries a content hash. Stale review records invalidated on change.
- **VI. Rigidity-Dependent Flux Calibration**: All flux measurements will be normalized by rigidity before computing modulation amplitudes.
- **VII. Multi-Source Temporal Alignment**: Solar activity indices and AMS-02 flux data will be temporally aligned using a documented lag analysis protocol (±12 months) with no interpolation of gaps.

## Project Structure

### Documentation (this feature)

```text
specs/001-cosmic-ray-composition-solar-cycle/
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
├── data/
│   ├── __init__.py
│   ├── fetch_ams02.py
│   ├── fetch_noaa.py
│   ├── align_data.py
│   └── preprocess.py
├── analysis/
│   ├── __init__.py
│   ├── correlation.py
│   ├── bootstrap.py
│   ├── model_fitting.py
│   └── visualization.py
├── utils/
│   ├── __init__.py
│   ├── logging.py
│   └── config.py
└── main.py

tests/
├── __init__.py
├── test_data_alignment.py
├── test_correlation.py
├── test_bootstrap.py
└── test_model_fitting.py

data/
├── raw/
├── processed/
└── checksums.txt

requirements.txt
```

**Structure Decision**: Single project structure (Option 1) selected for simplicity and alignment with the CLI/data analysis nature of the project. Directories are organized by function (data fetching, analysis, utilities) to support reproducibility and testing.

## Complexity Tracking

No violations detected. The project complexity is managed by:
- Breaking the pipeline into distinct, testable phases (data retrieval, alignment, correlation, bootstrap, fitting).
- Using CPU-tractable methods (pandas, scipy, scikit-learn) to stay within resource constraints.
- Explicitly handling data gaps and edge cases as defined in the spec (excluding gaps rather than interpolating).