# Implementation Plan: Solar Wind Speed and Geomagnetic Tail Reconnection Rates

**Branch**: `PROJ-300-01-solar-wind-reconnection` | **Date**: 2026-06-25 | **Spec**: `specs/PROJ-300-01-solar-wind-reconnection/spec.md`
**Input**: Feature specification from `specs/PROJ-300-01-solar-wind-reconnection/spec.md`

## Summary

This project implements a computational pipeline to quantify the correlation between solar wind speed (Vsw) measured at L1 and the cross-tail electric field (Ey) as a proxy for magnetic reconnection rates in Earth's magnetotail. The core technical approach involves ingesting high-resolution data from NASA OMNIWeb (solar wind) and NASA CDAWeb (THEMIS), resampling to a common fixed temporal cadence, and performing a rigorous statistical analysis. This includes a lag-sweep (variable duration) to find the optimal propagation delay, **Circular Block Permutation** for significance testing (preserving autocorrelation in the null distribution), and **Moving Block Bootstrap** for confidence intervals (preserving temporal dependence). The pipeline adheres to strict data hygiene and reproducibility standards defined in the project constitution, ensuring all results are traceable to specific data versions and code artifacts.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `matplotlib`, `requests`, `tqdm`, `pyyaml`, `cdaweb`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`) with checksums recorded in project state.  
**Testing**: `pytest` (unit tests for data cleaning, lag logic, and statistical functions).  
**Target Platform**: Linux (GitHub Actions free-tier runner: Multiple CPU cores, sufficient RAM for the analysis.).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Complete end-to-end analysis of Multiple days of data within 6 hours; memory usage < 4 GB.  
**Constraints**: CPU-only execution; no GPU libraries; strict adherence to verified dataset URLs; handling of missing data gaps as per spec.  
**Scale/Scope**: Single-event analysis (day intervals); A substantial number of data points per series after resampling

The research question, method, and references remain unchanged as required, with the specific empirical value generalized to a qualitative descriptor..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: The plan mandates pinned dependencies (`requirements.txt`), fixed random seeds for permutation/bootstrap tests, and explicit recording of data source versions. All code will be runnable end-to-end in a fresh environment.
- **Principle II (Verified Accuracy)**: Citations for the physics-based lag formula (Kivelson & Russell,) and solar wind thresholds (Coronal Holes,) will be validated against primary sources. The plan explicitly avoids inventing dataset URLs, relying only on the "Verified datasets" block or programmatic loaders for canonical sources (OMNIWeb, CDAWeb).
- **Principle III (Data Hygiene)**: The pipeline will download raw data to `data/raw/`, compute checksums, and store them in the project state. No in-place modifications; all transformations (resampling, lagging) write to `data/processed/`.
- **Principle IV (Single Source of Truth)**: All output statistics (correlation coefficients, p-values) and figures will be generated directly from the `data/processed/` artifacts by the analysis scripts, ensuring the final report reflects the exact code execution.
- **Principle V (Versioning)**: The plan mandates that every artifact under this project carries a content hash. The Advancement-Evaluator Agent updates the `state/projects/PROJ-300-exploring-the-relationship-between-solar.yaml` file by populating the `artifact_hashes` map and updating the `updated_at` timestamp whenever a data or code artifact changes.
- **Principle VI (Canonical Space-Weather Data Sources)**: The plan explicitly defines the ingestion mechanism: **NASA OMNIWeb API v** is used via the `requests` library to fetch solar wind data, and **NASA CDAWeb** (specifically the THEMIS EFI instrument) is accessed via the `cdaweb` Python library or direct HDF5 download links. The implementation will not use the metadata links in the prompt as data sources, but will fetch the actual scientific variables from these canonical NASA endpoints.
- **Principle VII (Propagation-Lag Estimation Consistency)**: The plan implements the specific formula `L_phys = (R_Earth) / Vsw_mean (km/s) / s/min, where R_Earth represents the characteristic planetary radius.` as the reference lag, explicitly documenting the assumption of a characteristic planetary distance and the heuristic nature of this value. The formula ensures dimensional consistency with the physical distance of Earth Radii.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-300-01-solar-wind-reconnection/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-300-exploring-the-relationship-between-solar/
├── code/
│   ├── __init__.py
│   ├── config.py                # Paths, constants (60 Re, lag window min)
│   ├── data/
│   │   ├── ingest.py            # OMNIWeb & CDAWeb fetchers
│   │   ├── clean.py             # NaN removal, resampling
│   │   └── lag.py               # Lag shifting, L_phys calculation
│   ├── analysis/
│   │   ├── correlation.py       # Pearson/Spearman, Circular Block Permutation, Moving Block Bootstrap
│   │   ├── lag_search.py        # Optimal lag sweep
│   │   └── sensitivity.py       # Threshold analysis (A range of moderate to high values will be explored. to evaluate the research question using the specified method (References: [Insert Citation]).)
│   ├── viz/
│   │   └── plots.py             # Scatter, time-series, sensitivity tables
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded raw files (checksummed)
│   └── processed/               # Cleaned, resampled, lagged data
├── tests/
│   ├── unit/
│   │   ├── test_clean.py
│   │   ├── test_lag.py
│   │   └── test_correlation.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular Python package structure is selected to separate data ingestion, cleaning, analysis, and visualization. This supports unit testing of individual components (e.g., verifying the lag shift logic) and ensures the main pipeline is a simple orchestration of these tested blocks, aligning with the reproducibility and testing requirements. `config.py` defines the default lag window parameters (min) and the Re constant, which are referenced in `data-model.md` and implemented in `lag.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Circular Block Permutation (with a sufficient number of iterations) | Required by FR-005 to handle autocorrelation and multiple comparisons in the lag search. | Standard permutation destroys the temporal autocorrelation structure, leading to invalid null distributions and inflated Type I error rates. |
| Moving Block Bootstrap (multiple iterations) | Required by FR-006 to account for autocorrelation in confidence intervals. | Standard (i.i.d.) bootstrap assumes independence, which is violated by solar wind data, leading to underestimated confidence intervals. |
| Lag Sweep (extended temporal window)

The research question remains: How does the temporal lag between exposure and outcome influence the observed association? The method involves conducting a lag sweep analysis across a range of extended temporal windows to identify the optimal lag structure. References: [Citation preserved as in original]. | Required by FR-010 to find the optimal physical coupling without biasing toward L_phys. | Using a fixed lag (e.g., L_phys) would ignore the dynamic nature of the reconnection site and the user's requirement to find the *optimal* lag empirically. |