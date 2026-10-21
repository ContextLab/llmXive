# Data Model: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Overview
Defines the immutable schemas for raw, processed, and result artifacts. All files live under `data/` with strict versioning and checksums.

## Core Entities

### CityBoundary
| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | City name (e.g., "New York") |
| `bbox` | `array[float]` (length 4) | `[minx, miny, maxx, maxy]` in EPSG:4326 |
| `crs` | `string` | EPSG code of source CRS |

### RasterCovariate
| Field | Type | Description |
|-------|------|-------------|
| `path` | `string` | Relative path to GeoTIFF |
| `resolution` | `number` | Target resolution (30.0 m) |
| `crs` | `string` | EPSG code after reprojection |
| `variable_name` | `string` | e.g., `building_density` |
| `source` | `string` | `"OSM"` |

### TemperatureRaster
| Field | Type | Description |
|-------|------|-------------|
| `path` | `string` | Relative path to GeoTIFF |
| `resolution` | `number` | 30.0 m |
| `crs` | `string` | EPSG code after reprojection |
| `time_range` | `string` | `"2020-2025"` (summer median) |
| `source` | `string` | `"Landsat"` |

### ModelResult
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | `string` | `"OLS"`, `"SAR"` or `"GWR"` |
| `city_name` | `string` | City identifier |
| `rmse` | `number` | Root Mean Squared Error |
| `mae` | `number` | Mean Absolute Error |
| `r2` | `number` | R² |
| `p_values` | `object` | `{variable: p}` |
| `correction_method` | `string` | `"permutation‑FDR"` |
| `memory_status` | `string` | `"OK"` or `"DEGRADED"` |
| `metrics` | `object` | Additional metrics (AIC, etc.) |

## File Formats

| Category | Format | Location |
|----------|--------|----------|
| Raw OSM vectors | Parquet / GeoJSON | `data/raw/osm/` |
| Raw Landsat LST | GeoTIFF (Cloud‑screened) | `data/raw/lst/` |
| Processed rasters | GeoTIFF (30 m) | `data/processed/rasters/` |
| Aligned dataset (pixel‑wise table) | Parquet or CSV | `data/processed/aligned/` |
| Model metrics | CSV (`metrics.csv`) | `data/results/` |
| Plots | PNG/SVG | `data/results/plots/` |
| Reports | Markdown & HTML | `data/results/reports/` |

## Data Flow Diagram (logical)

1. **Ingest** → `raw/` (checksum recorded).  
2. **Transform** → `processed/` (rasterize, reproject, log).  
3. **Sample / Memory Check** → possibly sub‑sample `processed/aligned/`.  
4. **Model** → `results/ModelResult` objects written to CSV/JSON.  
5. **Validate & Visualise** → plots stored in `results/plots/`.  
6. **Report** → markdown compiled in `results/reports/`.

All steps are deterministic given fixed random seeds.

---
