# Data Model: Predicting Species Distribution Shifts

## 1. Entity Definitions

### 1.1 Occurrence Record
Represents a single species sighting.
* **Attributes**:
  * `species_name` (string): Scientific name.
  * `latitude` (float): Decimal degrees.
  * `longitude` (float): Decimal degrees.
  * `event_date` (date): ISO 8601.
  * `source` (string): "GBIF" or "eBird".
  * `dataset_id` (string): Source dataset identifier.
  * `breeding_season` (boolean): True if date falls within breeding months.
  * `thinned` (boolean): True if record survived spatial thinning.
  * `bias_weight` (float): Relative sampling effort weight from bias raster (≥ 0).

### 1.2 Climate Variable
Environmental data at a grid cell.
* **Attributes**:
  * `variable_code` (string): e.g., "bio1" (Annual Mean Temp).
  * `value` (float): Scaled value (e.g., temp × 10).
  * `resolution` (string): "2.5 arc‑min".
  * `source` (string): "WorldClim v2" or "CMIP6".
  * `time_period` (string): "1970‑2000" or "2050‑SSP2‑4.5".

### 1.3 Model Artifact
Trained model instance.
* **Attributes**:
  * `algorithm` (string): "Random Forest", "Bioclim", **"Regularized Logistic Regression (PB)"**.
  * `species` (string).
  * `training_data_version` (string): Checksum of processed data.
  * `hyperparams` (json): Dictionary of parameters.
  * `metrics` (json): AUC, TSS, CV scores.

### 1.4 Bias Layer (new)
Raster representing spatial sampling effort.
* **Attributes**:
  * `layer_path` (string): File path to `.tif`.
  * `resolution` (string): Same as climate rasters.
  * `source` (string): Derived from eBird/GBIF effort records.
  * `creation_timestamp` (string, ISO 8601).

### 1.5 Preprocess Log (new)
Machine‑readable log of thinning counts.
* **Attributes**:
  * `species` (string)
  * `before_count` (integer): Count of records before thinning/filtering.
  * `after_count` (integer): Count of records after thinning/filtering.
  * `timestamp` (string, ISO 8601)
* **Location**: `logs/preprocess_counts.yaml`
* **Format**: YAML list of objects.

## 2. Data Flow

1. **Raw Ingestion**: `data/raw/occurrence_*.csv`, `data/raw/climate_*.tif`.  
2. **Bias Generation**: `bias_correction.py` → `data/processed/bias_layer.tif`.  
3. **Processed**: `data/processed/filtered_thinned.csv` (joined with climate + bias weights).  
4. **Artifacts**: `data/artifacts/model_{species}_{algo}.pkl`.  
5. **Metrics**: `metrics/performance_summary.csv`, `metrics/baseline_performance.csv`, `metrics/sensitivity_report.csv`.  
6. **Logs**: `logs/preprocess_counts.yaml`.

## 3. Constraints & Validation Rules

* **Coordinate Range**: Lat [-90, 90], Lon [-180, 180].  
* **Date Range**: 1970‑01‑01 to 2020‑12‑31.  
* **Null Handling**: No nulls in `latitude`, `longitude`, `species_name`, or climate predictors. Rows with nulls are dropped and logged.  
* **Thinning**: Minimum Euclidean distance ≥ 10 km between any two retained points (FR‑002).  
* **Record Count**: Species with < 100 records after thinning are excluded from training/evaluation (FR‑006).  
* **Bias Weights**: Must be ≥ 0; a weight of 0 indicates exclusion from background sampling.  
* **Preprocess Log**: Every species processed MUST have an entry in `logs/preprocess_counts.yaml` with `before_count` ≥ `after_count`.

## 4. Schema Versioning

* **v1.0**: Initial schema for occurrence, climate, and model artifacts.  
* **v1.1**: Added `bias_weight` to occurrence, `Bias Layer` entity, and `Preprocess Log`.  

