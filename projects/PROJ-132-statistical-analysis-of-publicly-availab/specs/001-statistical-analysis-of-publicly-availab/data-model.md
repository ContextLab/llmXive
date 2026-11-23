# Data Model: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## 1. Entity Definitions

### MigrationRecord
| Field | Type | Description |
|-------|------|-------------|
| `species_id` | `string` | Unique species identifier (e.g., `"TURDUS-MIGRATORIOUS"`). |
| `latitude` | `float` | Observation latitude (WGS84). |
| `longitude` | `float` | Observation longitude (WGS84). |
| `date` | `date` | Observation date (`YYYY‑MM‑DD`). |
| `count` | `int` | Number of individuals observed (`≥ 1`). |
| `checklist_id` | `string` | eBird checklist identifier. |
| `grid_cell` | `string` | `"lat_lon"` identifier at 0.5° resolution (e.g., `"45.5_-75.0"`). |
| `checklist_duration` | `int` | Checklist duration in minutes (effort covariate). |
| `observer_count` | `int` | Number of observers contributing to the checklist (effort covariate). |

### PhenologyMetric
| Field | Type | Description |
|-------|------|-------------|
| `species_id` | `string` | Species identifier. |
| `grid_cell` | `string` | 0.5° grid cell identifier. |
| `year` | `int` | Observation year (`2020 – 2024`). |
| `first_arrival_date` | `date` | Earliest spring observation (Mar‑May). |
| `median_arrival_date` | `date` | Date when cumulative count reaches [deferred] of spring total. |
| `stopover_duration` | `float` | Days between 10th and 90th percentile arrival dates. |
| `observation_count` | `int` | Total observations (effort‑weighted) in the cell‑year. |
| `data_quality` | `string` | `"sufficient"` if `observation_count ≥ 5`; otherwise `"insufficient"`. |

### ClimateVariable
| Field | Type | Description |
|-------|------|-------------|
| `grid_cell` | `string` | 0.5° grid cell identifier. |
| `week_start` | `date` | ISO week start date. |
| `mean_temperature` | `float` | Mean temperature (°C). |
| `total_precipitation` | `float` | Total precipitation (mm). |
| `extreme_weather_index` | `float` | Normalized index (0 – 1) for extreme events. |
| `source` | `string` | Fixed value `"PRISM"` (for provenance). |
| `imputed` | `bool` | `true` if value was spatially interpolated (see edge case). |

### Trajectory
| Field | Type | Description |
|-------|------|-------------|
| `species_id` | `string` | Species identifier. |
| `year` | `int` | Year of the trajectory. |
| `centroids` | `list[dict]` | Weekly centroids: `{"week": int, "lat": float, "lon": float}`. |
| `shift_vector` | `dict` | `{"magnitude": float, "direction": float}` (km, radians). |
| `p_value` | `float` | Permutation test p‑value for shift significance. |
| `is_shift_significant` | `bool` | `true` if `p_value < 0.05`. |

### ProvenanceFile
| Field | Type | Description |
|-------|------|-------------|
| `processed_row_id` | `string` | Unique ID in processed CSV/JSON. |
| `original_checklist_id` | `string` | eBird checklist ID. |
| `original_row_index` | `int` | Row number in the raw CSV. |
| `filter_reason` | `string` | Reason for inclusion/exclusion (`"sufficient"`, `"insufficient"`, `"date_filter"`, `"species_filter"`). |

## 2. Data Flow
1. **Download** (`src/data/download.py`) → streamed directly; no full raw files are persisted.  
2. **Preprocess** (`src/data/preprocess.py`) reads streamed records, filters, aggregates, computes `PhenologyMetric`, joins with `ClimateVariable`, writes `data/processed/phenology_climate.csv`.  
3. **Provenance** (`row_mapping.json`) links each processed row back to its original checklist.  
4. **Model Input** (`src/models/gamm.py`) consumes rows where `data_quality == "sufficient"` and fits GAMMs. Results written to `data/output/gamm_results.csv`.  
5. **Trajectory** (`src/models/manifold.py`) consumes weekly centroids, outputs `data/output/trajectory.json`.  
6. **Analysis** (`src/analysis/*`) produces final summary tables, figures, and `pipeline_report.json`.

---



## 3. Validation Rules
- **Grid Cell Format** – Must match pattern `^[+-]?\d+(\.\d+)?_[+-]?\d+(\.\d+)?$` with one decimal (0.5°).  
- **Date Range** – All dates ∈ [2020‑01‑01, 2024‑12‑31].  
- **Missing Climate** – If a cell‑week lacks PRISM data, impute via inverse‑distance weighting from neighboring cells within 1°; set `imputed: true`.  
- **Sparse Phenology** – If `observation_count < 5`, set `data_quality: "insufficient"` and exclude from modeling.  
- **Latitude/Longitude Bounds** – Latitude ∈ [‑90, 90]; Longitude ∈ [‑180, 180].

---



## 4. Alignment with Functional Requirements
- **FR‑001** – Streaming download in `src/data/download.py`.  
- **FR‑002** – Filtering and grid aggregation in `src/data/preprocess.py`.  
- **FR‑003** – Phenology computation (including effort weighting) in `src/data/preprocess.py`.  
- **FR‑004** – GAMM fitting in `src/models/gamm.py`.  
- **FR‑005** – Permutation testing and FDR correction in `src/analysis/correlation.py`.  
- **FR‑006** – Trajectory construction in `src/models/manifold.py`.  
- **FR‑007** – Block‑bootstrap CI in `src/analysis/routes.py`.
