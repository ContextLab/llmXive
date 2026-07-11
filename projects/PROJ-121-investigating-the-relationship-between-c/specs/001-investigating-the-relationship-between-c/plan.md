# Implementation Plan: Cosmic Ray Anisotropy Solar‑Cycle Modulation

**Branch**: `121-cosmic-ray-anisotropy-solar-cycle` | **Date**: 2026-06-24 | **Spec**: `specs/121-cosmic-ray-anisotropy-solar-cycle/spec.md`
**Input**: Feature specification from `specs/121-cosmic-ray-anisotropy-solar-cycle/spec.md`

## Summary

This project implements a reproducible, CPU-only pipeline to investigate correlations between cosmic ray anisotropy (dipole amplitude/phase) and solar activity proxies (sunspot, solar wind, IMF) over the 2010-2020 period. 

**Scientific Scope & Limitations**: The analysis window (a decade-scale period) is insufficient to resolve a multi-year solar cycle (frequency in the low-frequency regime) with statistical power (resolution sufficient for low-frequency analysis). The system will **not** claim detection of the 11-year cycle. Instead, it will:
1. Perform Lomb-Scargle analysis to identify any significant peaks within the observable frequency range.
2. Explicitly report the frequency resolution limit and flag the inability to distinguish the 11-year peak from DC/trend.
3. Search for *any* significant periodicity or trend and report it with appropriate caveats.

**Data Strategy**: 
- **IceCube**: Uses the verified HuggingFace dataset.
- **Pierre Auger**: If no verified URL is found, the system proceeds with IceCube-only analysis and logs a warning. Combined analysis is only performed if both detectors independently pass a statistically significant threshold (Constitution Principle VI).
- **Sampling**: To fit within 7GB RAM and 6h runtime, the pipeline applies a data sampling strategy (e.g., using only events >10 TeV or random [deferred] sampling) if the full dataset exceeds memory limits.

**Statistical Protocol**: 
- **Block Bootstrap**: Uses a data-driven block length (Stationary Bootstrap) estimated from the autocorrelation of the residuals, with a minimum of 27 days (Constitution Principle VII) to avoid underestimating uncertainty.
- **Phase Sensitivity**: Includes circular-linear correlation and lagged cross-correlation to account for the vector nature of anisotropy.
- **FAP Estimation**: Uses phase randomization of *both* series (or block-shuffling both) to preserve temporal structure, correcting the methodological error of shuffling only the proxy.
- **Fallback**: If bootstrap blocks < 10, switches to Fourier-based surrogate generation (FR-005).

**Output**: Time-series CSV, periodogram plots (with resolution warnings), correlation heatmaps, and a LaTeX report containing a programmatically generated hypothesis support statement.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `astropy`, `healpy`, `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `requests`, `lxml`, `jinja2`, `pyyaml`, `statsmodels` (for autocorrelation/Stationary Bootstrap)  
**Storage**: Local file system (`data/` for raw/processed data, `output/` for results)  
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline flow)  
**Target Platform**: Linux (Ubuntu 22.04, GitHub Actions runner)  
**Project Type**: Scientific CLI / Data Analysis Pipeline  
**Performance Goals**: Complete end-to-end analysis within 6 hours on 2 CPU, 7 GB RAM; no GPU usage.  
**Constraints**: 
- All data downloads must handle retries with **exponential back-off** (1s, 2s, 4s).
- Statistical methods must be CPU-tractable; no CUDA dependencies.
- Strict adherence to Bonferroni correction and multiple hypothesis testing protocols.
- **Block Length**: Fixed at 27 days (Constitution Principle VII) or estimated via Stationary Bootstrap (min 27 days).
- **Data Sampling**: Apply sampling if dataset > 7GB RAM.
- **Combined Analysis**: Only if both detectors pass 3σ independently.

**Scale/Scope**: 
- **Time Window**: 2010-01-01 to 2020-12-31.
- **Expected Intervals**: ~135 intervals (27-day bins).
- **Detectors**: IceCube (verified), Pierre Auger (fallback if unavailable).
- **Solar Proxies**: 3 (sunspot, solar wind, IMF).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Notes |
|-----------|--------|--------------|
| I. Reproducibility | **PASS** | Plan mandates `requirements.txt` with pinned versions, random seed pinning, and automated re-runs on fresh runners. |
| II. Verified Accuracy | **PASS** | Plan uses verified IceCube URL. For Auger/NOAA (unverified), plan explicitly logs fallback to IceCube-only or standard API, avoiding fabricated URLs. |
| III. Data Hygiene | **PASS** | Plan includes SHA-256 checksum verification for all downloads; raw data preserved, derivations written to new files. |
| IV. Single Source of Truth | **PASS** | All figures/statistics in report trace to `data/` CSVs and `code/` scripts. No hand-typed numbers. |
| V. Versioning Discipline | **PASS** | Plan includes artifact hashing logic for `state/` updates; content hashes for all data/code. |
| VI. Multi-Detector Consistency | **PASS** | Analysis runs independently. Combined analysis is **gated**: only generated if both detectors pass 3σ. If one fails, combined analysis is skipped and report states which failed. |
| VII. Statistical Analysis Protocol | **PASS** | Plan implements Lomb-Scargle, data-driven block bootstrap (min 27 days), and Monte-Carlo shuffle (phase randomization of both series) as required. |

## Project Structure

### Documentation (this feature)

```text
specs/121-cosmic-ray-anisotropy-solar-cycle/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── anisotropy-interval.schema.yaml
│   ├── solar-proxy.schema.yaml
│   ├── event-dataset.schema.yaml        # NEW
│   └── correlation-result.schema.yaml   # NEW
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Handles IceCube, Auger, NOAA downloads with retries (exponential back-off) & checksums
│   ├── preprocess.py        # Bins events, generates HEALPix maps, fits spherical harmonics, applies sampling if needed
│   └── solar_proxy.py       # Fetches and aligns solar indices
├── analysis/
│   ├── correlation.py       # Lomb-Scargle, data-driven block bootstrap, phase-sensitive correlation
│   ├── significance.py      # Bonferroni correction, FAP (phase randomization of both series), Fourier fallback (FR-005)
│   └── stats_utils.py       # Autocorrelation estimation, Stationary Bootstrap
├── report/
│   ├── generate_plots.py    # Time-series, periodograms (with resolution warnings), heatmaps
│   └── latex_report.py      # Jinja2 template rendering to PDF, includes programmatically generated hypothesis statement
├── cli/
│   └── run_all.sh           # Main entry point orchestrating pipeline
├── utils/
│   ├── checksum.py          # SHA-256 verification
│   └── logging.py           # Structured logging
└── tests/
    ├── unit/                # Unit tests for modules
    └── integration/         # End-to-end pipeline tests

data/
├── raw/                     # Downloaded raw files (checksummed)
├── processed/               # Binned events, HEALPix maps
└── results/                 # CSVs, plots, report.pdf

requirements.txt
```

**Structure Decision**: Single project structure (`src/`, `data/`, `tests/`) chosen for simplicity and alignment with CLI-driven scientific workflows. Modular separation of data, analysis, and reporting ensures maintainability and testability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Data Sampling Strategy | Required to fit 10-year dataset into 7GB RAM. | Processing full raw dataset is infeasible on 2 CPU/7GB RAM without distributed frameworks. |
| Phase Randomization (Both Series) | Required to preserve temporal structure in FAP estimation. | Shuffling only the proxy destroys the null hypothesis validity for time-series. |
| Data-Driven Block Length | Required to avoid underestimating uncertainty in autocorrelated data. | Fixed 2x bin size is too short and may miss true autocorrelation length. |
