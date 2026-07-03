# Implementation Plan: Investigating the Potential Benefits of Ecotourism in Regenerating Deforested Areas

**Branch**: `001-ecotourism-regeneration` | **Date**: 2026-06-03 | **Spec**: `specs/001-ecotourism-regeneration/spec.md`

## Summary

This project implements an **observational study** to investigate the **associational patterns** between ecotourism designation and forest regeneration rates in deforested areas. The study explicitly **does not claim causal acceleration** due to the lack of randomization. The technical approach involves:
1.  **Data Acquisition**: Programmatic retrieval of Landsat Level Surface Reflectance via USGS API for a set of paired sites (ecotourism and control groups) covering 2000-2023, processed in chunks to respect available RAM limits.
2.  **Feature Engineering**: Calculation of NDVI time series, cloud masking, and detection of deforestation events (NDVI drop ≥0.30 sustained ≥2 years).
3.  **Modeling**: Fitting a **Hierarchical Non-Linear Model (HNLMM)** to recovery trajectories (borrowing strength across sites) and a Linear Mixed-Effects Model (LMM) to test the association between ecotourism status and regeneration rate, controlling for climate (CHIRPS/MODIS) and initial severity.
4.  **Robustness**: Sensitivity analysis sweeping revenue thresholds (low, medium, and high) and proxy variables (revenue vs. visitor count), with multiple-comparison correction (Holm/Bonferroni).
5.  **Temporal Validation**: Explicit check of `designation_date` vs. `deforestation_start_date` to avoid collider bias.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `landsatxplore` (USGS API), `rasterio`, `xarray`, `scikit-learn`, `statsmodels` (LMM/HNLMM), `pandas`, `pyyaml`, `pydantic`.  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`), CSV/Parquet intermediate formats.  
**Testing**: `pytest` (unit tests for NDVI logic, integration tests for pipeline).  
**Target Platform**: GitHub Actions Free Runner (Linux, Limited CPU resources, 7GB RAM, No GPU).  
**Project Type**: Computational Research Pipeline / Data Analysis.  
**Performance Goals**: Process 30 sites in <6 hours; Peak RAM <7GB; Model convergence >90%.  
**Constraints**: No GPU; No large LLMs; Chunked processing required for satellite imagery; Observational study design (no causal claims).  
**Scale/Scope**: Multiple sites, -year time series, A set of covariates per site.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `requirements.txt` pins all deps; **USGS API query parameters and versions are explicitly recorded in `code/data_acquisition.py` and exported to `data/raw/query_log.json`** to ensure exact reproduction of data fetch. |
| **II. Verified Accuracy** | **PASS** | All dataset citations (USGS, CHIRPS, MODIS) verified against `# Verified datasets` block; no fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Raw Landsat files stored in `data/raw/landsat/` with checksums; derivations written to new files in `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | Final report figures/stats generated directly from `data/processed/` via scripts; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in `state/` manifest; `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Ecotourism Revenue Transparency** | **PASS** | Financial data (revenue/visitors) stored in `data/ecotourism/` with **`metadata.json` containing exactly `source_name`, `retrieval_date`, and `preprocessing_steps` for each site**, as mandated by the Constitution. |
| **VII. Satellite Data Integrity** | **PASS** | Raw Level-2 scenes saved unmodified in `data/raw/landsat/`; NDVI calculated via documented pipeline; **checksums recorded in `state/projects/PROJ-555-...yaml` artifact_hashes map** for every scene. |

## Project Structure

### Documentation (this feature)

```text
specs/001-ecotourism-regeneration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── site.schema.yaml
    ├── timeseries.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data_acquisition.py      # USGS API download, chunking, metadata fetch; **logs API params to data/raw/query_log.json**
├── preprocessing.py         # Cloud masking, NDVI calc, time-series alignment
├── detection.py             # Deforestation break-point detection (FR-002)
├── modeling.py              # **HNLMM**, LMM, Sensitivity analysis (FR-003, FR-004)
├── report.py                # Final report generation, sensitivity tables (FR-006)
├── config.py                # Constants, thresholds, paths
└── main.py                  # Pipeline orchestrator
tests/
├── unit/
│   ├── test_detection.py
│   └── test_preprocessing.py
└── integration/
    └── test_pipeline.py
data/
├── raw/
│   ├── landsat/             # Raw Level-2 scenes
│   └── query_log.json       # **Records USGS API query parameters and versions**
├── processed/
│   ├── ndvi_timeseries.parquet
│   └── site_metadata.csv
└── ecotourism/
    ├── revenue_data.csv
    └── metadata.json        # **Contains source_name, retrieval_date, preprocessing_steps per site**
```

**Structure Decision**: Single-project structure selected. The workflow is linear (Download -> Process -> Model -> Report) and does not require separate backend/frontend services. All logic is encapsulated in `code/` scripts for reproducibility on CPU-only runners.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Hierarchical Non-Linear Model (HNLMM)** | Required by FR-002 to accurately capture the "S-curve" of forest recovery while borrowing strength across sites to stabilize estimates for N=30. | Independent non-linear fits for each site are statistically unstable for small N and prone to non-convergence. |
| **Linear Mixed-Effects Model** | Required by FR-003 to account for the paired design (random effect 'pair') and control for site-level heterogeneity. | Standard OLS regression would violate independence assumptions due to the paired site structure and spatial autocorrelation. |
| **Chunked Streaming** | Required by FR-001 to stay under 7GB RAM when processing years of Landsat imagery for 30 sites. | Loading all raw imagery into memory simultaneously would exceed the 7GB limit and crash the runner. |
| **Temporal Validation** | Required to avoid collider bias if ecotourism designation occurred after deforestation. | Ignoring temporal ordering risks spurious correlations if sites were selected based on prior recovery. |
