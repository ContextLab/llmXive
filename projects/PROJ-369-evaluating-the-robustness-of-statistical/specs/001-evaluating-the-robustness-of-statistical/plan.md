# Implementation Plan: Evaluating Robustness of Statistical Methods to Non-Independence

**Branch**: `001-evaluating-the-robustness-of-statistical-methods-to-non-independence` | **Date**: 2024-05-21 | **Spec**: `specs/001-evaluating-the-robustness-of-statistical-methods-to-non-independence/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-robustness-of-statistical-methods-to-non-independence/spec.md`

## Summary

This project evaluates the robustness of standard statistical tests (one-sample t-test, F-test) to non-independence in time series data. The technical approach involves: (1) ingesting diverse public time series (NOAA, financial, energy), (2) applying a dual-path preprocessing strategy (ADF for unit roots; DFA for long-memory preservation), (3) quantifying dependence via Hurst exponent and ACF on *stationary* series, (4) generating synthetic ground-truth data (fGn/ARFIMA) with *varying* sample sizes (N) and known Hurst parameters, (5) running Monte Carlo hypothesis tests to measure Type I error inflation across a (H, N) grid, and (6) fitting a non-linear regression of error rates against H and log(N_eff) to validate the theoretical VIF mechanism. The plan strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and null distribution validation via [deferred] shuffles per series.

## Technical Context

**Language/Version**: Python +  
**Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `arch` (for Hurst/ARFIMA), `yfinance`, `requests`, `pyyaml`, `matplotlib`, `seaborn`, `statsmodels` (for GLM), `xarray` (for NOAA)  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `results/`) with checksums; no external DB.  
**Testing**: `pytest` (unit tests for preprocessing, synthetic generation, and hypothesis test logic).  
**Target Platform**: GitHub Actions Free Tier (Multiple CPU cores, ample RAM, ample disk, no GPU).  
**Project Type**: Statistical Research Pipeline / CLI Tool  
**Performance Goals**: Complete full pipeline (ingestion, N-variation grid, Multiple synthetic trials per cell, regression) in ≤ 6 hours.  
**Constraints**: Must run on CPU; memory usage < 7 GB; no external API keys required; datasets must be directly downloadable (no gated access).  
**Scale/Scope**: + real datasets, Several Hurst levels spanning a broad range of values will be examined. × sample sizes (, A range of sample sizes (from hundreds to tens of thousands) will be evaluated.), a substantial number of Monte Carlo trials per configuration. A sufficient number of shuffled null distributions per series.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan includes pinned `requirements.txt`, random seed management in `code/`, and explicit dataset source URLs. All scripts are designed to run end-to-end on a fresh runner.
- **Principle II (Verified Accuracy)**: All dataset URLs in `research.md` are restricted to the "# Verified datasets" block provided in the spec. No hallucinated URLs.
- **Principle III (Data Hygiene)**: Plan mandates checksumming of raw downloads, immutable raw data, and derivation of processed files with documented transformations.
- **Principle IV (Single Source of Truth)**: All figures and statistics in the output paper will trace to specific rows in `data/processed/` and code blocks in `code/`.
- **Principle V (Versioning Discipline)**: Artifact hashes will be recorded in `state/projects/PROJ-369-evaluating-the-robustness-of-statistical.yaml`.
- **Principle VI (Temporal Dependence Quantification)**: Every dataset processing step includes ACF (lag)

The research question remains: How does the autocorrelation structure evolve over time? The method involves computing the autocorrelation function at multiple lags to identify significant dependencies. References: [Citation preserved verbatim]., Hurst exponent (via DFA), and spectral density peak ratio calculation before hypothesis testing.
- **Principle VII (Null Distribution Validation via Shuffling)**: Plan explicitly includes generating **[deferred] shuffled versions per series** (for *every* real and synthetic series) to create a null distribution for comparison. This count is hardcoded and validated in tests to ensure the specific comparison mechanism is applied to every series as required.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-robustness-of-statistical-methods-to-non-independence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── ingestion.py          # Download and cache datasets (FR-001)
│   ├── preprocessing.py      # ADF (unit root) OR DFA (long memory), missing value fill (FR-002)
│   └── metrics.py            # ACF, Hurst (DFA), Spectral Density (FR-002, FR-007)
├── synthesis/
│   ├── generators.py         # fGn, ARFIMA, Shuffling (FR-003, FR-007)
│   └── validation.py         # Baseline validity check (FR-008)
├── analysis/
│   ├── hypothesis_tests.py   # One-sample t-test, F-test (FR-004)
│   └── regression.py         # Error rate vs. H, log(N_eff), interaction; GLM (FR-005)
├── viz/
│   └── plots.py              # ACF, scatter, QQ-plots, VIF curves (FR-006)
├── utils/
│   ├── config.py             # Seeds, constants
│   └── logging.py            # Warning/error logging
└── main.py                   # Orchestrator

tests/
├── unit/
│   ├── test_ingestion.py
│   ├── test_preprocessing.py
│   ├── test_synthesis.py
│   └── test_hypothesis.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/                      # Downloaded datasets (checksummed)
├── processed/                # Stationary, detrended, metrics, shuffled nulls
└── results/                  # Test results, regression outputs
```

**Structure Decision**: Single project structure with modular `src/` packages. Chosen for simplicity and direct mapping to the statistical workflow (Ingest → Process → Synthesize → Analyze → Visualize). No frontend/backend split needed for a research pipeline.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project scope is strictly defined by the spec and fits within the CPU constraints. The N-variation grid increases trials but remains within 6h budget via efficient vectorization. | N/A |

## Fr/Sc Coverage Matrix

| ID | Type | Coverage in Plan |
|----|------|------------------|
| FR-001 | Req | `src/data/ingestion.py` downloads multiple datasets from verified sources (NOAA, Yahoo, Energy). |
| FR-002 | Req | `src/data/preprocessing.py` implements ADF (unit root) OR DFA (long memory); `src/data/metrics.py` computes ACF, Hurst, Spectral Density. |
| FR-003 | Req | `src/synthesis/generators.py` implements shuffling for **every** time series (real and synthetic) to create a null distribution ([deferred] versions per series). |
| FR-004 | Req | `src/analysis/hypothesis_tests.py` implements one-sample t-test and F-test; excludes two-sample. |
| FR-005 | Req | `src/analysis/regression.py` implements non-linear/GLM regression of error rate vs. H and log(N_eff); includes interaction term; excludes Max_ACF_Lag1 as predictor. |
| FR-006 | Req | `src/viz/plots.py` generates ACF, scatter, QQ-plots, VIF curves. |
| FR-007 | Req | `src/synthesis/generators.py` generates fGn/ARFIMA with H={, a moderate threshold, a high value} and N={a range of sample sizes from small to large, including representative small, medium, and large cohorts}; calculates theoretical VIF/N_eff. |
| FR-008 | Req | `src/synthesis/validation.py` verifies baseline validity (H=0.5, A series of trials) before proceeding. |
| SC-001 | Metric | Measured in `src/analysis/hypothesis_tests.py` against nominal α=0.05. |
| SC-002 | Metric | Measured in `src/analysis/regression.py` (slope, p-value, non-linear fit). |
| SC-003 | Metric | Measured in `src/analysis/regression.py` (observed - nominal). |
| SC-004 | Metric | Runtime monitored in `main.py` and logged; target ≤ 6h. |