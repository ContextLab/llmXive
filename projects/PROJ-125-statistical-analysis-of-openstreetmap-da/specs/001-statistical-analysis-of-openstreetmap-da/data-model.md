# Data Model: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Overview

Defines immutable schemas for raw, processed, and result artifacts. All files live under `data/` with SHA‑256 checksums recorded in `data/raw/manifest.json` (Constitution Principle III).

## Core Entities

### CityBoundary
| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | City name (e.g., "New York") |
| `bbox` | `array[float]` (length 4) | `[minx, miny, maxx, maxy]` in EPSG:4326 |
| `crs` | `string` | EPSG code of source CRS |

### RasterCovariate
| Field | Type | Description |
|-------|------|-------------|
| `path` | `string` | Relative path to GeoTIFF |
| `resolution` | `number` | Target resolution (30.0 m) |
| `crs` | `string` | EPSG code after reprojection |
| `variable_name` | `string` | e.g., `building_density`, `land_use_*`, `tree_cover`, `road_density` |
| `source` | `string` | `"OSM"` |
| `description` | `string` | Rasterization/aggregation method (Principle VI) |

### TemperatureRaster
| Field | Type | Description |
|-------|------|-------------|
| `path` | `string` | Relative path to GeoTIFF |
| `resolution` | `number` | 30.0 m |
| `crs` | `string` | EPSG after reprojection |
| `time_range` | `string` | e.g., `"2020-2024"` (JJA median composites, 5‑year average) |
| `source` | `string` | `"Landsat"` (via `ingest_lst.py` contract; `DATA_GAP` if unavailable) |

### ModelResult
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | `string` | `"OLS"`, `"SAR"`, `"GWR"`, or `"OLS_DEGRADED"` |
| `city_name` | `string` | City identifier |
| `rmse` | `number` | Root Mean Squared Error |
| `mae` | `number` | Mean Absolute Error |
| `r2` | `number` | R‑squared value |
| `coefficients` | `object` | Per‑predictor coefficient map |
| `standard_errors` | `object` | Per‑predictor standard‑error map |
| `p_values` | `object` | FDR‑corrected p‑values per predictor |
| `correction_method` | `string` | `"permutation-FDR"` (SC‑003) |
| `memory_status` | `string` | `"OK"` or `"DEGRADED"` |
| `memory_peak_gb` | `number` | Peak RSS via psutil (SC‑005) |
| `n_samples` | `integer` | Cell count used in the model |
| `n_eff` | `number` | Effective sample size (heuristic) |
| `cv_metrics` | `object` | Spatial 5‑fold CV RMSE/MAE/R² |
| `sensitivity_analysis` | `object` | Bandwidth or block‑size sweep results |
| `unexplained_variance_gap` | `number` | 0.68 − Observed_R² (provisional) |
| `notes` | `string` | Bias warning / descriptive‑only label in degraded mode |
| `morans_i` | `number` | Moran's I of model residuals (always reported) |

## File Formats

| Category | Format | Location |
|----------|--------|----------|
| Raw OSM vectors | Parquet / GeoJSON | `data/raw/osm/` |
| Raw LST | GeoTIFF (cloud‑screened) | `data/raw/lst/` |
| Download manifest (checksums, timestamps) | JSON | `data/raw/manifest.json` |
| Processed 30 m rasters | GeoTIFF | `data/processed/rasters/` |
| Alignment log (reprojection/aggregation methods) | JSON | `data/processed/alignment_log.json` |
| Aligned pixel dataset | Parquet | `data/processed/aligned/` |
| Exploratory statistics | CSV (`exploratory.csv`) | `data/results/` |
| Model metrics | CSV (`metrics.csv`) | `data/results/` |
| Model outputs | JSON | `data/results/models/` |
| Plots | PNG | `data/results/plots/` |
| Lint reports / test logs | TXT | `data/results/qa/` |
| Reports | Markdown | `data/results/reports/` |

## Data Flow (Logical)

1. **Ingest** → `data/raw/` (checksums + timestamps recorded).  
2. **Transform** → `data/processed/` (reproject, rasterize, log methods).  
3. **Sample / memory check** → possibly block‑sampled subset of `processed/aligned/`.  
4. **Model** → `data/results/models/` (ModelResult JSON).  
5. **Validate & visualize** → plots, contract‑validated outputs.  
6. **QA** → lint reports, unit/contract test logs.  
7. **Report** → markdown report in `data/results/reports/`.

All steps are deterministic given fixed seeds (e.g., a designated seed identifier). Raw data is never modified in place; all transformations write new files.  

