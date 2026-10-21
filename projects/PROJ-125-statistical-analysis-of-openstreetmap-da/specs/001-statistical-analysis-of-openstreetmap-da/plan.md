# Implementation Plan: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Branch**: `PROJ-125-statistical-analysis-of-openstreetmap-da` | **Date**: 2026-10-21 | **Spec**: `specs/001-statistical-analysis-of-openstreetmap-da/spec.md`  
**Input**: Feature specification from `specs/001-statistical-analysis-of-openstreetmap-da/spec.md`

## Summary
The pipeline will:

1. **Data Ingestion** – Download city boundaries, OSM vector layers (buildings, land‑use, trees, roads) from verified HuggingFace parquet datasets, and download a **verified, openly downloadable Landsat LST composite** from HuggingFace (`https://huggingface.co/datasets/earthlab/landsat8_lst`). The ingestion creates `CityBoundary`, `RasterCovariate`, and `TemperatureRaster` records.

2. **Preprocessing** – Reproject all layers to the local UTM zone (or EPSG:3857 fallback) and rasterize to a 30 m grid, documenting aggregation methods per Constitution Principle VI. This step produces `RasterCovariate` and `TemperatureRaster` artifacts and writes the aligned pixel‑wise dataset that conforms to `contracts/dataset.schema.yaml`. Environmental covariates (albedo, elevation, water proximity, humidity) are also rasterized and included.

3. **Exploratory Spatial Statistics** – Compute Pearson correlation matrix and Moran’s I for each variable (including the added environmental covariates). Store results in `data/results/exploratory.csv`.

4. **Memory Safety & Effective Sample Size** – After rasterization, calculate total cell count **N** and Moran’s I, then compute an **effective sample size** `N_eff = N / (1 + Moran’s I)`. If `N ≥ 500 000` cells or `N_eff ≥ 500 000`, apply spatial block sampling to bring `N_eff` ≤ 500 k. Monitor peak RSS via `psutil`; trigger **OLS_DEGRADED** mode if `peak_memory_gb > 5` (log `model_type: OLS_DEGRADED`). Abort with exit code 99 if `peak_memory_gb > 6` (SC‑005). Record `memory_status` in `metrics.csv`.

5. **Model Fitting** –  
   - **OLS** (baseline) with clustered standard errors.  
   - **SAR** (Spatial Lag) via `pysal`.  
   - **GWR** via `mgwr` (bandwidth selected by AICc).  
   In degraded mode only OLS is fitted. All models output `ModelResult` objects validated against `contracts/model_output.schema.yaml`.

6. **Spatial 5‑fold Cross‑Validation** – Create spatial blocks (k‑means on coordinates) to prevent leakage, fit each model on 4 blocks, predict on the held‑out block, and aggregate RMSE, MAE, R². Store CV metrics in `metrics.csv`.

7. **Multiple‑Comparison Correction** – Gather all predictor p‑values and apply **permutation‑based FDR** (α = 0.05) using `statsmodels`. Record `correction_method = "permutation‑FDR"`.

8. **Sensitivity Analysis** –  
   - For GWR: sweep bandwidth from 50 m to 500 m (step 25 m) and plot R² vs. bandwidth.  
   - For OLS_DEGRADED: sweep block size to assess coefficient stability. Save plot `sensitivity_<model>.png`.  
   Results are linked to `contracts/model_output.schema.yaml`.

9. **Reporting & Export** – Assemble `metrics.csv` (validated against `contracts/metrics.schema.yaml`), model output JSON files, and plots. Generate a markdown report referencing all artifacts. **The Unexplained Variance Gap metric (FR‑010) is omitted pending a validated literature ceiling.**  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `osmnx`, `geopandas`, `rasterio`, `xarray`, `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `pysal`, `mgwr`, `psutil`  
- **Compute**: CPU‑first; all steps fit within 2 CPU cores, ~7 GB RAM, ≤6 h on GitHub Actions free tier. No GPU required.

## Constitution Check

| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed seeds, deterministic URLs, no stochastic shortcuts |
| II. Verified Accuracy | PASS | All datasets now have verified open URLs (including LST) |
| III. Data Hygiene | PASS | Checksums recorded, immutable transformations |
| IV. Single Source of Truth | PASS | All metrics trace to rows in `metrics.csv` |
| V. Versioning Discipline | PASS | Artifact hashes stored in project state |
| VI. Spatial Resolution Integrity | PASS | Reprojection/aggregation methods logged |
| VII. Proxy Validity Boundaries | PASS | Sensitivity analysis included; Unexplained Variance Gap omitted pending validation |

## Project Structure
```text
specs/001-statistical-analysis-of-openstreetmap-da/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml   <-- aligned dataset schema (includes env covariates)
│   ├── metrics.schema.yaml
│   ├── model_output.schema.yaml
│   └── output.schema.yaml
└── tasks.md   # generated later
```

## Implementation Phases & FR/SC Coverage
| Phase | Tasks | FR IDs | SC IDs | Core Entity | Contract |
|-------|-------|--------|--------|-------------|----------|
| **1. Data Ingestion** | Download city boundaries, OSM vectors, LST; create `CityBoundary`, `RasterCovariate`, `TemperatureRaster`. | FR‑001, FR‑002, FR‑012 | SC‑001, SC‑002 | CityBoundary, RasterCovariate, TemperatureRaster | `contracts/dataset.schema.yaml` |
| **2. Preprocessing** | Reproject, rasterize to 30 m, log methods, include environmental covariates. | FR‑003, FR‑011 | SC‑001 | RasterCovariate, TemperatureRaster, EnvironmentalCovariate | `contracts/dataset.schema.yaml` |
| **3. Exploratory Stats** | Correlation matrix, Moran’s I. | FR‑004 | SC‑001 | (uses RasterCovariate) | `contracts/dataset.schema.yaml` |
| **4. Memory & Power** | Compute N, Moran’s I → N_eff; spatial block sampling; memory monitor → OLS_DEGRADED. | FR‑005, Memory rule | SC‑005 | — | `contracts/metrics.schema.yaml` (memory_status) |
| **5. Model Fitting** | OLS, SAR, GWR (or OLS only in degraded). | FR‑005, FR‑007 | SC‑001, SC‑005 | ModelResult | `contracts/model_output.schema.yaml` |
| **6. Spatial CV** | 5‑fold spatial block CV. | FR‑006 | SC‑001 | ModelResult (cv_metrics) | `contracts/model_output.schema.yaml` |
| **7. FDR Correction** | Permutation‑based FDR on all p‑values. | FR‑008 | SC‑003 | ModelResult (`correction_method`) | `contracts/model_output.schema.yaml` |
| **8. Sensitivity** | Bandwidth sweep (GWR) or block‑size sweep (OLS). | FR‑009 | SC‑004 | ModelResult (`sensitivity_analysis`) | `contracts/model_output.schema.yaml` |
| **9. Reporting** | Export `metrics.csv`, model JSON, plots; generate markdown report. | FR‑010 (omitted), all other FRs | SC‑001, SC‑004 | — | `contracts/metrics.schema.yaml`, `contracts/output.schema.yaml` |

## Scope Clarifications
- **Linting (ruff/black)**, **Unit Tests**, **Quickstart Validation**, **Spec Amendment**, and **CI Integration** phases are **outside** the documented functional requirements and success criteria; they are therefore omitted from the implementation plan.

## Causal Inference Disclaimer
The observational design **does not support causal claims** about how OSM‑derived features *cause* temperature differences. All findings are presented as descriptive associations, and any language implying causality has been removed.  

--- 
