# Implementation Plan: Statistical Properties of Simulated Black Hole Mergers

**Branch**: `001-statistical-properties-black-hole-mergers` | **Date**: 2024-01-15 | **Spec**: `specs/001-statistical-properties-black-hole-mergers/spec.md`
**Input**: Feature specification from `specs/001-statistical-properties-black-hole-mergers/spec.md`

## Summary

This project implements a statistical pipeline to compare observational black hole merger data (GWTC-1/2) against simulated population models. The primary requirement is to download posterior samples, preprocess them into point-estimate distributions, and perform Kolmogorov-Smirnov (KS) tests with Bonferroni correction and sensitivity analysis. The technical approach relies on CPU-tractable Python libraries (`scipy`, `numpy`, `pandas`) to ensure execution within GitHub Actions free-tier limits (≤6h runtime, ≤7GB RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `matplotlib`, `requests`, `pyyaml`  
**Storage**: Local filesystem (`data/` for raw/preprocessed CSVs, `artifacts/` for plots and reports)  
**Testing**: `pytest` (unit tests for data loading, integration tests for pipeline phases)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Analysis Pipeline / Research Script  
**Performance Goals**: Total runtime ≤6 hours; Peak memory ≤7 GB; Peak disk ≤20 GB.  
**Constraints**: No GPU/CUDA; No large LLM inference; Must handle 404 errors on Zenodo with exponential backoff (per FR-001).  
**Scale/Scope**: Processing ~100-500 merger events; Generating 2 primary KDE plots and 1 sensitivity report.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan mandates pinned random seeds in `code/` and deterministic Zenodo downloads with checksum verification.
- **Principle II (Verified Accuracy)**: Plan includes a `contracts/` schema to validate dataset structure against the spec's requirements before analysis.
- **Principle III (Data Hygiene)**: Plan specifies checksumming raw data and storing derived products in new files with provenance logs.
- **Principle IV (Single Source of Truth)**: All figures and stats in the report will be generated directly from `data/` CSVs; no hand-typed numbers.
- **Principle V (Versioning Discipline)**: The plan requires content hashes for all artifacts in `data/` and `code/`.
- **Principle VI (Simulation Data Integrity)**: *Deviation Required*: The spec explicitly notes that IllustrisTNG/EAGLE (mandated by Constitution) lack the required resolved component mass/spin distributions. The plan adopts the spec's fallback: generating a synthetic catalog based on a "Power-law spin distribution" hypothesis if no verified external source exists. This deviation is documented as a temporary scientific necessity pending a Constitution amendment.
- **Principle VII (Statistical Rigor)**: Plan includes Bonferroni correction, sensitivity analysis on α, and power analysis (MDES) as required by FR-006, FR-009, and FR-010.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-properties-black-hole-mergers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── gwtc_catalog.schema.yaml
│   └── simulation_catalog.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download_gwtc.py       # Handles Zenodo download with retry logic
│   ├── download_simulation.py # Handles simulation data or synthetic generation
│   └── preprocess.py          # Filters NaNs, extracts point estimates
├── analysis/
│   ├── kde.py                 # 1D KDE computation
│   ├── ks_test.py             # KS test + Bonferroni correction
│   ├── sensitivity.py         # Alpha sweep analysis
│   └── power.py               # Power analysis + MDES
├── viz/
│   └── plot_distributions.py  # Generates divergence plots
├── utils/
│   ├── checksum.py            # SHA256 verification
│   └── config.py              # Random seeds, paths
└── main.py                    # Orchestration script

tests/
├── unit/
│   ├── test_preprocess.py
│   └── test_ks_test.py
└── integration/
    └── test_pipeline.py

data/
├── raw/                       # Downloaded Zenodo files (checksummed)
├── processed/                 # Preprocessed CSVs
└── artifacts/                 # Plots, reports, logs
```

**Structure Decision**: Single-project structure chosen for simplicity and to minimize I/O overhead on the free-tier runner. All data flows sequentially through `data/raw` → `data/processed` → `data/artifacts`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Synthetic Data Generation | No verified external simulation source exists for resolved BBH spins/masses (Constitution VI deviation). | Using a scalar merger rate (e.g., IllustrisTNG) is scientifically invalid for distributional KS tests. |
| Exponential Backoff | Zenodo rate limits or transient 404s are expected. | Simple retry loops fail on transient network glitches; backoff ensures robustness within the 6h CI window. |
| Sensitivity Analysis (α sweep) | Essential for statistical rigor to avoid threshold artifacts. | A single α=0.05 test is insufficient for population inference per community standards. |
