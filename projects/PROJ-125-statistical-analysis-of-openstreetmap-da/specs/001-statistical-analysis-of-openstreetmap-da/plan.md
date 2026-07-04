# Implementation Plan: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Branch**: `001-statistical-analysis-urban-heat` | **Date**: 2024-05-22 | **Spec**: `specs/001-statistical-analysis-urban-heat/spec.md`
**Input**: Feature specification from `/specs/001-statistical-analysis-urban-heat/spec.md`

## Summary

This project implements a statistical analysis pipeline to quantify the associational relationship between OpenStreetMap (OSM) derived urban features (building density, road networks, tree presence proxies) and Land Surface Temperature (LST) across three major US cities (New York, Chicago, Los Angeles). The approach involves ingesting vector OSM data and satellite thermal imagery (Landsat/MODIS), aligning them to a unified 30m raster grid, performing exploratory spatial diagnostics, and fitting spatial regression models (OLS, GWR, SAR) on a **statistically representative sample** to ensure CPU tractability. The pipeline includes rigorous spatial cross-validation, False Discovery Rate control, and a toroidal shift permutation test to validate spatial significance.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rasterio`, `geopandas`, `overpy`, `xarray`, `netCDF4`, `scikit-learn`, `pysal` (for `spreg`), `mgwr`, `statsmodels`, `pyproj`, `earthaccess`  
**Storage**: Local filesystem (`data/raw`, `data/processed`), NetCDF/GeoTIFF formats  
**Testing**: `pytest` (contract tests against YAML schemas, integration tests for data alignment)  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7GB RAM, no GPU)  
**Project Type**: Computational research pipeline  
**Performance Goals**: Complete full analysis of 3 cities within 6 hours runtime.  
**Constraints**: 
- **No GPU usage**; all data processing must be CPU-tractable.
- **Strict 30m resolution** for raster alignment.
- **No causal claims** (associational only).
- **Sampling for Modeling**: While the raster grid is at a medium spatial resolution, GWR and SAR models are fitted on a **stratified random sample (N ≤ 50,000 points per city)** to ensure O(N^2) complexity remains tractable on a limited number of CPU cores within 6 hours. Raster aggregation (density calculation) is performed via tiling.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: Plan mandates `requirements.txt` pinning, random seed setting in `code/`, and fetching from canonical sources (AWS, Overpass) on every run.
2.  **II. Verified Accuracy**: Plan requires citations to be verified against primary sources (AWS Open Data, Overpass) before review. No fabricated URLs.
3.  **III. Data Hygiene**: Plan includes checksumming steps for raw data and immutable derivation of processed rasters.
4.  **IV. Single Source of Truth**: Plan ensures all figures/stats trace to `data/` and `code/`. No hand-typed numbers.
5.  **V. Versioning Discipline**: Content hashes for artifacts will be recorded in state files upon generation.
6.  **VI. Spatial Resolution Integrity**: Plan explicitly details the reprojection and aggregation (30m) method for vector-raster joins.
7.  **VII. Proxy Validity Boundaries**: Plan includes:
    - Sensitivity analysis for GWR bandwidth (FR-007).
    - Explicit acknowledgment of OSM tree points as proxies.
    - **New**: Sensitivity analysis on 'material albedo' using land-cover derived albedo estimates to quantify missing factor variance.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-urban-heat/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (defined here, implemented in Phase 1)
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_ingest/
│   ├── fetch_osm.py
│   ├── fetch_thermal.py
│   └── align_rasters.py
├── 02_eda/
│   ├── spatial_stats.py
│   └── plots.py
├── 03_modeling/
│   ├── sample_data.py       # NEW: Stratified sampling logic
│   ├── fit_models.py
│   ├── cross_val.py
│   └── sensitivity.py
├── 04_validation/
│   ├── perm_test.py         # NEW: Toroidal shift implementation
│   └── report_metrics.py
├── utils/
│   ├── config.py
│   └── io_helpers.py
└── requirements.txt

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    └── test_utils.py

data/
├── raw/
│   ├── osm/
│   └── thermal/
└── processed/
    └── aligned_grid/
```

**Structure Decision**: Modular pipeline structure (`01_`, `02_`, etc.) to enforce data flow order (Ingest -> EDA -> Sample -> Model -> Validate). Contracts are defined in Phase 1 to guide implementation but referenced in this plan for consistency checks.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Stratified Sampling for GWR/SAR** | Required to fit O(N^2) models on 2 CPU cores within 6h. Full grid (large-scale) is intractable. | Fitting on full grid would cause OOM or timeout. |
| **Toroidal Shift Permutation** | Required to preserve spatial autocorrelation under the null hypothesis. | Standard permutation destroys spatial structure, invalidating the test. |
| **Albedo Sensitivity Analysis** | Required by Constitution Principle VII to account for missing material factors. | Ignoring albedo risks overclaiming OSM proxy utility. |
| **Spatial CV (Blocks)** | Required by FR-005 to prevent leakage from spatial autocorrelation. | Random K-fold would result in inflated performance metrics. |
