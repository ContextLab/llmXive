# Data Model: Predicting Avian Song Variation with Climatic and Geographic Factors

## Entity Definitions

### 1. SongRecord
*Source*: not directly provided; fields are already present in the merged dataset.  
**Attributes**:
- `species_id` (string) – unique species identifier.  
- `song_metric_1` (float ≥ 0) – e.g., dominant frequency (kHz).  
- `song_metric_2` (float ≥ 0) – e.g., song duration (s).  
- `location_lat` (float, –90 ≤ lat ≤ 90).  
- `location_lon` (float, –180 ≤ lon ≤ 180).  

### 2. ClimateSnapshot
*Source*: not directly provided; fields are already present in the merged dataset.  
**Attributes**:
- `location_lat` (float, –90 ≤ lat ≤ 90).  
- `location_lon` (float, –180 ≤ lon ≤ 180).  
- `temperature` (float) – mean °C.  
- `precipitation` (float) – total mm.  
- `elevation` (float) – meters above sea level.  

### 3. AnalysisDataset
*Source*: `data/raw/analysis_dataset.parquet` (verified URL).  
**Attributes** (union of SongRecord & ClimateSnapshot, plus bookkeeping):
- `species_id` (string)  
- `song_metric_1` (float ≥ 0)  
- `song_metric_2` (float ≥ 0)  
- `location_lat` (float, –90 ≤ lat ≤ 90)  
- `location_lon` (float, –180 ≤ lon ≤ 180)  
- `temperature` (float)  
- `precipitation` (float)  
- `elevation` (float)  
- `match_status` (enum: `matched` | `excluded`) – always `matched` for this curated dataset.  
- `distance_km` (float) – distance between recording point and climate raster cell centre (provided by the dataset).  

## Data Flow
1. **Ingestion** (`code/ingestion.py`)  
   - Download `analysis_dataset.parquet`.  
   - Verify SHA‑256 checksum (`data/checksums.txt`).  
   - Validate against `contracts/analysis_dataset.schema.yaml`.  
   - (Optional) Reproject any user‑supplied raster to EPSG:4326.  
   - Write a copy to `data/processed/analysis_dataset.parquet`.  

2. **Merge Validation** (`code/ingestion.py` step T018)  
   - After loading, compare species IDs and coordinate precision between the original song and climate components (embedded in the parquet).  
   - Log any mismatches; abort if >5 % of rows are affected.  

3. **EDA** (`code/eda.py`) consumes the processed `AnalysisDataset` and produces `outputs/eda_report.json`.  

4. **Power Analysis** (`code/power.py`) computes a priori sample‑size requirements and reports achieved power.  

5. **Modeling** (`code/modeling.py`) consumes the same dataset and produces:  
   - `outputs/model_summary.csv` (validated by `contracts/analysis_output.schema.yaml`)  
   - `aggregated_pvalues.parquet` (validated by `contracts/aggregated_pvalues.schema.yaml`)  
   - `outputs/sensitivity_report.json`.  

6. **Reporting** (`code/main.py`) orchestrates all steps, logs runtime, and writes figures to `outputs/figures/`.  

## Constraints & Validation Rules
- **Coordinate ranges** must respect latitude/longitude bounds.  
- **Song metrics** must be strictly positive.  
- **No duplicate rows** after ingestion (checked via composite key `(species_id, location_lat, location_lon)`).  
- **VIF** > 5 triggers a flag that includes the offending predictor **and** its most correlated partner (Pearson |r| ≥ 0.8).  
- **Checksum** for every file is recorded in `data/checksums.txt`; any change updates `state/projects/...yaml`.  

---

