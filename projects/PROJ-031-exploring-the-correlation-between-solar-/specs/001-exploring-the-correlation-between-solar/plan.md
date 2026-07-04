# Implementation Plan: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

**Branch**: `001-solar-flare-storm-correlation` | **Date**: 2024-01-15 | **Spec**: `specs/001-solar-flare-storm-correlation/spec.md`
**Input**: Feature specification from `specs/001-solar-flare-storm-correlation/spec.md`

## Summary

This project implements a reproducible, CPU-only pipeline to analyze the associational correlation between solar flare X-ray peak flux, CME speeds, and geomagnetic storm intensities (Dst index). The system ingests historical data from NOAA SWPC and CDAWeb, aligns events within a 3-day window, performs statistical analysis (Spearman correlation with 95% Confidence Intervals, linear regression with VIF checks, and bootstrap-resampled threshold sensitivity), and identifies predictive thresholds using a strict time-series hold-out validation (Train: **2010-01-01 to 2020-12-31**, Test: **2021-01-01 to 2023-12-31**). All outputs are validated against strict JSON schemas and reported with full transparency regarding statistical limitations and dataset provenance.

The core associational claim (correlation strength) is computed on the full aligned dataset (descriptive), while the predictive threshold validation is strictly performed on the hold-out set (2021-2023) using bootstrap resampling to estimate confidence intervals for detection rates.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `requests`, `pyyaml`, `tqdm`, `psutil`, `scikit-learn` (all CPU-only, no CUDA).  
**Storage**: Local filesystem (`data/`, `results/`). Data downloaded via `requests` from NOAA/CDAWeb endpoints.  
**Testing**: `pytest` for unit tests; contract validation via `jsonschema` against `contracts/`.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, no GPU).  
**Project Type**: Data analysis CLI / Research pipeline.  
**Performance Goals**: Total runtime ≤ 6 hours; Peak RAM ≤ 7 GB.  
**Data Scale**: Raw ingestion of k to tens of thousands of rows (10 years of flare/CME data); Final aligned analysis dataset expected to be <500 rows (all storms) or <50 rows (severe storms, Dst ≤ -100).  
**Constraints**: No GPU/CUDA; No large language models; Strict adherence to FR-011 (Fixed 2010-2020 / 2021-2023 split) and FR-006 (VIF fallback logic).  
**Validation Logic**: Contract validation MUST block the writing of `aligned_events.csv` and the update of `data/source_manifest.yaml` if validation fails.  
**Performance Metrics**: Execution time and peak RAM MUST be written to `results/metrics.json` under the `performance` key.  
**VIF Fallback Logic**: If VIF > 5, the system selects the **univariate model with the higher absolute correlation coefficient** as the primary report. The selected model type (e.g., "univariate_flare") MUST be recorded in `results/metrics.json`. The joint R² is NOT reported if the joint model is discarded.  
**Multiple Comparison Correction**: **Bonferroni** correction is used for the family of 5 tests (2 primary correlations + 3 threshold sensitivity tests). The method name MUST be recorded in `results/metrics.json`.  
**Threshold Justification**: The implementation MUST cite the specific NOAA SWPC definition document: "https://www.swpc.noaa.gov/phenomena/geomagnetic-storms" for the "severe storm" (Dst ≤ -100 nT) threshold.  
**Non-Linear Model**: If R² < 0.1, the system MUST test a piecewise model and report the improvement in fit in `results/metrics.json` under the key `piecewise_r2_improvement`.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | Random seeds pinned in `code/`. Data fetched from canonical NOAA/CDAWeb URLs. `requirements.txt` pinned. |
| **II. Verified Accuracy** | ⚠️ PENDING | Citations in `research.md` will be verified. **CME Source Status**: Currently unverified in research.md. **Strategy**: Implementation must verify the CDAWeb URL before finalizing `data/source_manifest.yaml`. If verification fails, the manifest will reflect the "Unverified" status and the project will be flagged for manual review. |
| **III. Data Hygiene** | ✅ PASS | Raw data preserved in `data/raw/`. Checksums recorded in `state/`. No in-place modifications. |
| **IV. Single Source of Truth** | ✅ PASS | All stats in `results/metrics.json` trace to `code/analysis.py` and `data/aligned_events.csv`. |
| **V. Versioning Discipline** | ✅ PASS | Artifacts hashed in `state/`. `updated_at` timestamps managed by agent workflow. |
| **VI. Solar Event Data Provenance** | ⚠️ PENDING | `data/source_manifest.yaml` will record exact URLs. **CME Source Status**: Currently unverified. **Strategy**: Implementation must verify the CDAWeb URL. If unverified, the manifest will explicitly state "Unverified" and the plan will not claim full compliance until verified. |
| **VII. Statistical Analysis Transparency** | ✅ PASS | `requirements.txt` pins `scipy`/`statsmodels`. `results/metrics.json` contains coefficients, p-values, CIs, and method names. |

## Project Structure

### Documentation (this feature)

```text
specs/001-solar-flare-storm-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── aligned_event.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

**Note on tasks.md**: The `tasks.md` file generated in Phase 2 will explicitly map to FR-011 (Fixed 2010-2020 / 2021-2023 split) and FR-006 (VIF fallback logic) to ensure deterministic execution and prevent silent relaxation of constraints.

### Source Code (repository root)

```text
projects/PROJ-031-exploring-the-correlation-between-solar-/
├── code/
│   ├── __init__.py
│   ├── ingest.py          # Downloads and parses raw data from NOAA/CDAWeb
│   ├── align.py           # Aligns events within 3-day window, flags missing data
│   ├── analyze.py         # Correlation, regression, VIF, bootstrap threshold sweep
│   ├── validate.py        # Validates CSV against contracts; BLOCKS write on failure
│   ├── profiler.py        # Measures RAM/CPU time, writes to results/metrics.json
│   └── main.py            # Orchestrates pipeline execution
├── data/
│   ├── raw/               # Downloaded raw files (preserved)
│   ├── processed/         # Aligned events CSV
│   └── source_manifest.yaml
├── results/
│   └── metrics.json       # Final statistical outputs and performance metrics
├── contracts/
│   ├── aligned_event.schema.yaml
│   └── metrics.schema.yaml
└── requirements.txt
```

**Structure Decision**: Single project structure selected to maintain a linear, reproducible research pipeline. `code/` contains modular scripts for ingest, alignment, and analysis. `contracts/` and `results/` are separated to enforce validation gates before data commitment.

## Complexity Tracking

No complexity violations identified. The plan strictly adheres to the spec's constraints (CPU-only, fixed time split, VIF fallback) without introducing unnecessary abstraction layers.