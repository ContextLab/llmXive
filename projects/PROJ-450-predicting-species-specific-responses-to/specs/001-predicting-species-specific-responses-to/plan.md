# Implementation Plan: Predicting Species‑Specific Responses to Climate Change from Museum Collection Data

**Branch**: `450-predicting-species-niche-shifts` | **Date**: 2026-06-24 | **Spec**: `specs/450-predicting-species-niche-shifts/spec.md`
**Input**: Feature specification from `specs/450-predicting-species-niche-shifts/spec.md`

## Summary

This project implements a computational pipeline in **R** to quantify species-specific realized climatic niche shifts over the past century. The system retrieves georeferenced museum occurrence records (GBIF), extracts climate data from WorldClim layers for two historical periods (1970-2000, 1991-2020), computes niche centroids, and analyzes the relationship between niche shift magnitude and regional warming rates using **Phylogenetic Generalized Least Squares (PGLS)** regression. The implementation prioritizes reproducibility, strict adherence to functional requirements (FR-001 to FR-012), and computational feasibility on CPU-only CI runners.

## Technical Context

**Language/Version**: R 4.3+
**Primary Dependencies**: `rgbif`, `raster`, `sf`, `ggplot2`, `dplyr`, `tidyr`, `caper` (for PGLS), `phylolm`, `pwr`, `tibble`, `lubridate`, `here`, `renv`
**Storage**: Local filesystem (`data/`, `results/`), CSV/Parquet intermediate formats
**Testing**: `testthat` (unit tests for data parsing, integration tests for pipeline steps)
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)
**Project Type**: Data analysis pipeline / CLI tool (R Script)
**Performance Goals**: Complete analysis of ~50-100 species within 6 hours; memory usage < 6GB.
**Constraints**: No GPU; strict adherence to WorldClim v2 data availability; no manual data modification.
**Scale/Scope**: Processing of multiple focal species per run (test), scalable to 100+ species.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan includes explicit random seed pinning (`set.seed()`) in `research.md` and `data-model.md`. External datasets (GBIF, WorldClim) are fetched via deterministic API calls (`rgbif::occ_search`) or local checksums. `sessionInfo()` is logged.
- **Principle II (Verified Accuracy)**: All dataset references in `research.md` are restricted to the "Verified datasets" block. No URLs are fabricated. The GBIF API endpoint is referenced as the standard ` accessed via `rgbif`.
- **Principle III (Data Hygiene)**: `data-model.md` defines checksumming for all raw inputs. Transformations produce new files. No in-place edits.
- **Principle IV (Single Source of Truth)**: Plan mandates that all output statistics trace back to `results/` CSVs and `code/` scripts.
- **Principle V (Versioning Discipline)**: `plan.md` and `research.md` will include content hashes for artifacts.
- **Principle VI (Provenance)**: `research.md` details the exact GBIF query parameters (occurrence, PRESERVED_SPECIMEN) via `rgbif` and WorldClim v2 versions. Query timestamps are logged in `data/metadata.yaml`.
- **Principle VII (Statistical Transparency)**: `research.md` specifies the PGLS model formula, seed, and diagnostic output requirements.

## Project Structure

### Documentation (this feature)

```text
specs/450-predicting-species-niche-shifts/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│ ├── raw/ # Downloaded GBIF CSVs, WorldClim rasters
│ ├── processed/ # Centroids, shifted data
│ └── metadata.yaml # Checksums, query logs
├── code/
│ ├── fetch_gbif.R # FR-001, FR-002
│ ├── extract_climate.R # FR-003, FR-006 (Species Centroids)
│ ├── compute_regional_warming.R # FR-006 (Independent Grid)
│ ├── compute_centroids.R # FR-004
│ ├── analyze_shifts.R # FR-005, FR-007, FR-011 (PGLS)
│ ├── sensitivity.R # FR-009
│ ├── power_analysis.R # FR-012
│ ├── plotting.R # FR-008
│ └── utils.R # Logging, validation
├── tests/
│ ├── unit/
│ └── integration/
└── results/
 ├── regression_summary.csv
 ├── power_analysis_report.csv
 ├── sensitivity_summary.csv
 └── plots/
```

**Structure Decision**: Single project structure (Option 1) chosen. The pipeline is linear (Fetch -> Extract -> Compute -> Analyze -> Plot), making a modular `code/` layout with a `data/` separation for raw vs. processed data the most maintainable approach. All scripts are R-based to comply with Constitution Principle VI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly defined by the spec. | N/A |

## Statistical Rigor & Methodological Notes

- **Global Z-Scoring (FR-005)**: The plan strictly adheres to the spec's requirement for global z-scoring. However, the interpretation of the resulting ΔN is explicitly defined as "relative deviation from the global community shift" to avoid tautological misinterpretation.
- **Phylogenetic Non-Independence**: To address the violation of independence in OLS, the primary regression model is **PGLS** (via `caper` or `phylolm`). If a phylogenetic tree is unavailable, a sensitivity analysis with WLS (Weighted Least Squares) will be performed, but PGLS is the primary inference method.
- **Heteroscedasticity**: The PGLS/WLS models will use inverse-variance weights derived from the sensitivity analysis (FR-009) to ensure valid standard errors.
- **Power Analysis**: An a priori power analysis is conducted to justify n=30, with a dedicated script and output artifact.

## Known Constraints & Limitations

- **Temporal Gap**: WorldClim provides multiple bioclimatic versions covering distinct historical periods.. The "century-scale" inference relies on the difference between these two periods.
- **Sampling Bias**: Museum data is biased towards accessible locations. The sensitivity analysis (FR-009) mitigates this.
- **Global Z-Scoring Limitation**: The metric ΔN is relative to the global mean. If the global community shifts, the baseline shifts. This is a known limitation of the spec's FR-005, documented in the results.
- **Coordinate Precision**: GBIF records may have high coordinate uncertainty. Records with `coordinateUncertaintyInMeters` > 10km (configurable) may be filtered.