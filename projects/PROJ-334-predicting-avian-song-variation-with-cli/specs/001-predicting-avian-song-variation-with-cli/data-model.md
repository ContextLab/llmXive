# Data Model: Predicting Avian Song Variation with Climatic and Geographic Factors

## Entity Definitions

### 1. SongRecord
*Source*: `data/raw/song_record.csv` **(not provided; variables are already present in the merged dataset).**  
**Attributes**:
- `species_id` (string) – unique species identifier.  
- `song_metric_1` (float ≥ 0) – e.g., dominant frequency (kHz).  
- `song_metric_2` (float ≥ 0) – e.g., duration (s).  
- `location_lat` (float, –90 ≤ lat ≤ 90).  
- `location_lon` (float, –180 ≤ lon ≤ 180).  

### 2. ClimateSnapshot
*Source*: `data/raw/climate_snapshot.csv` **(not provided; variables are already present in the merged dataset).**  
**Attributes**:
- `location_lat` (float, –90 ≤ lat ≤ 90).  
- `location_lon` (float, –180 ≤ lon ≤ 180).  
- `temperature` (float) – mean °C.  
- `precipitation` (float) – total mm.  
- `elevation` (float) – meters above sea level.  

### 3. AnalysisDataset
*Source*: `data/raw/analysis_dataset.parquet` (verified URL).  
**Attributes** (union of the two above, plus bookkeeping):
- `species_id` (string)  
- `song_metric_1` (float)  
- `song_metric_2` (float)  
- `location_lat` (float)  
- `location_lon` (float)  
- `temperature` (float)  
- `precipitation` (float)  
- `elevation` (float)  
- `match_status` (enum: `matched` | `excluded`) – always `matched` for this curated dataset.  
- `distance_km` (float) – distance between recording point and climate raster cell centre (provided).  

## Data Flow
1. **Ingestion** (`code/ingestion.py`):  
   - Download the verified `analysis_dataset.parquet`.  
   - Validate against `contracts/analysis_dataset.schema.yaml`.  
   - (Optional) If a user supplies a separate climate raster, reproject to EPSG:4326 (fulfills FR‑001 CRS requirement).  
   - Write a copy to `data/processed/analysis_dataset.parquet` (checksum recorded).  

2. **EDA** (`code/eda.py`): consumes `AnalysisDataset`, produces `outputs/eda_report.json`.  

3. **Modeling** (`code/modeling.py`): consumes `AnalysisDataset`, produces `outputs/model_summary.csv`, `outputs/sensitivity_report.json`, and `aggregated_pvalues.parquet`.  

4. **Reporting** (`code/main.py`): orchestrates all steps, logs runtime, and writes figures to `outputs/figures/`.

## Constraints & Validation Rules
- **Coordinate ranges** must respect lat/lon bounds.  
- **Song metrics** must be strictly positive.  
- **No duplicate rows** after ingestion (checked via `record_id` composite).  
- **VIF** > 5 triggers a flag that includes the offending predictor **and** its most correlated partner (Pearson r ≥ 0.8).  
- **Checksum** for every file is stored in `data/checksums.txt`; any change updates `state/projects/...yaml`.  

---
