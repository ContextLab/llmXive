# Data Model: Ambient Temperature Influence on Moral Decision Speed (Re‑scoped)

## 1. Entity Relationship (Textual)

```mermaid
erDiagram
    MORAL_RESPONSE ||--o{ GRID_CELL : "matched via lat/long"
    MORAL_RESPONSE ||--o{ PARTICIPANT : "belongs to"
    MORAL_RESPONSE ||--o{ DILEMMA : "presents"
    PARTICIPANT ||--o{ MORAL_RESPONSE : "makes"
    GRID_CELL ||--o{ MORAL_RESPONSE : "provides temperature"
    GHSL_CLASS ||--o{ MORAL_RESPONSE : "indoor/outdoor proxy (optional)"
```

## 2. Schema Definitions

### 2.1. Raw Moral Machine Data (`data/raw/moral_machine.csv`)

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `response_id` | STRING | Unique row identifier | PK |
| `participant_id` | STRING | Anonymous participant ID | |
| `country` | STRING | ISO‑country code | |
| `latitude` | FLOAT | Decimal latitude | NOT NULL |
| `longitude` | FLOAT | Decimal longitude | NOT NULL |
| `timestamp` | TIMESTAMP | UTC timestamp of decision | NOT NULL |
| `dilemma_id` | INTEGER | Scenario identifier | |
| `age_group` | STRING | Age bracket (optional) | |
| `gender` | STRING | Gender (optional) | |
| `choice` | STRING | `"utilitarian"` / `"non_utilitarian"` | NOT NULL |

> **Response‑time** (`response_time_ms`) is **not** present in the public CSV; it must be supplied via the auxiliary experiment (see below). The merge is performed **by `scenario_id`**, assigning each Moral Machine record the *scenario‑level* average latency.

### 2.2. Auxiliary Response‑Time Data (`data/raw/aux_response_times.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `scenario_id` | STRING | Identifier matching `dilemma_id` in the Moral Machine data |
| `mean_response_time_ms` | INTEGER | Average latency (ms) for that scenario from the crowdsourced experiment |

### 2.3. ERA5 Climate Grid (`data/raw/era5_subset.h5`)

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `grid_id` | STRING | Unique grid cell identifier | |
| `latitude` | FLOAT | Center latitude of cell | |
| `longitude` | FLOAT | Center longitude of cell | |
| `temperature_c` | FLOAT | Hourly 2 m air temperature (°C) | -50 ≤ temp ≤ 50 |
| `timestamp` | TIMESTAMP | Hour of observation | |
| **Note** | | The file contains only grid cells intersecting the convex hull of all Moral Machine locations (≈ few hundred MB), satisfying the free‑tier compute limits. | |

### 2.4. GHSL Urban/Rural Classification (`data/raw/ghsl_urban_rural.parquet`)

| Column | Type | Description |
|--------|------|-------------|
| `grid_id` | STRING | Matches ERA5 grid cells |
| `urban_rural` | STRING | `"urban"` or `"rural"` |

### 2.5. Processed Merged Dataset (`data/processed/merged_dataset.parquet`)

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| `record_id` | STRING | `{response_id}_{grid_id}` composite | Derived |
| `response_id` | STRING | From Moral Machine | MM |
| `participant_id` | STRING | From Moral Machine | MM |
| `country` | STRING | From Moral Machine | MM |
| `latitude` | FLOAT | From Moral Machine (kept) | MM |
| `longitude` | FLOAT | From Moral Machine | MM |
| `response_time_ms` | INTEGER | **Scenario‑level average latency** from auxiliary experiment (FR‑016) | AUX |
| `log_rt` | FLOAT | `log(response_time_ms)` | Derived |
| `temperature_c` | FLOAT | Hourly temperature (ERA5) | ERA5 |
| `temperature_c_squared` | FLOAT | Square of temperature | Derived |
| `distance_km` | FLOAT | Haversine distance to nearest ERA5 grid cell | Derived |
| `dilemma_complexity` | FLOAT | Static score (lives + difficulty) | Derived |
| `time_of_day` | INTEGER | Hour of day (0‑23) | Derived |
| `age_group` | STRING | Optional | MM |
| `gender` | STRING | Optional | MM |
| `urban_rural_proxy` | STRING | `"urban"` or `"rural"` (optional) | GHSL |
| `quality_flag` | STRING | Data quality status | Enum |
| `scenario_id` | STRING | Identifier linking to auxiliary latency data (`dilemma_id`) | MM |
| `exclusion_flag` | BOOLEAN | True if record excluded (distance >100 km, temperature out of range, etc.) | Derived |

**Note**: `response_time_ms` is a *scenario‑level* average latency, not an individual participant measurement. This limitation is documented in the research plan and treated as an association rather than a causal effect.

### 2.6. Data Quality Log (`data/processed/data_quality_log.json`)

Conforms to `contracts/exclusion_log.schema.yaml`. Each entry records `response_id`, reason for exclusion, original coordinates, and timestamp.

## 3. Data Flow

1. **Download Moral Machine CSV** (`download_moral_machine.py`).  
2. **Download ERA5 Hourly (spatial subset)** (`download_era5.py`).  
3. **Validate Sources** (`validate_sources.py`) – abort if ERA5 not hourly (FR‑014).  
4. **Download GHSL raster** (`download_ghsl.py`) – optional (FR‑012).  
5. **Ingest & Match** (`ingestion.py`): nearest‑grid join, compute haversine distance, flag > 100 km (FR‑009), merge hourly temperature, compute match % (SC‑001).  
6. **Merge Auxiliary RTs** (`preprocessing.py`): left‑join `aux_response_times.csv` on `scenario_id` (matching `dilemma_id`); abort if any scenario lacks latency (FR‑016).  
7. **Preprocess** (`preprocessing.py`): filter implausible RTs, apply temperature range filter, create covariates, write `merged_dataset.parquet`. Validate against `contracts/merged_dataset.schema.yaml` (FR‑018).  
8. **Fit Primary Mixed‑Effects Model** (`modeling.py`): MixedLM on `log_rt`; output `model_results.json` (`contracts/model_output.schema.yaml`).  
9. **Robustness Analyses** (`robustness.py`): alternative temperature metric, outlier thresholds, indoor/outdoor stratified models or bootstrap, produce `sensitivity_analysis.csv`.  
10. **Power Analysis** (`power_analysis.py`).  

All artifacts are validated against the schemas in `contracts/`.

--- 



