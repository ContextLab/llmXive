# Data Model: Predicting Species Distribution Shifts

## Entity Definitions

### Occurrence Record
Represents a single sighting of a species.
- **Attributes**:
  - `gbif_key` (str): Unique GBIF identifier.
  - `scientific_name` (str): Species name.
  - `decimalLatitude` (float): Latitude in WGS84.
  - `decimalLongitude` (float): Longitude in WGS84.
  - `eventDate` (str): ISO 8601 date (YYYY-MM-DD).
  - `year` (int): Extracted year.
  - `month` (int): Extracted month.
  - `basisOfRecord` (str): Source type (e.g., "OBSERVATION").
  - `source` (str): "GBIF" or "eBird".
  - `download_timestamp` (str): ISO 8601 timestamp of fetch.
  - `dataset_name` (str): **Original dataset name** from GBIF (Constitution Principle VI).

### Climate Point
Represents climate variables at a specific occurrence location.
- **Attributes**:
  - `gbif_key` (str): Link to Occurrence Record.
  - `bio1` ... `bio19` (float): WorldClim bioclimatic variables.
  - `temp_mean` (float): Mean annual temperature.
  - `precip_total` (float): Annual precipitation.

### Model Artifact
Represents a trained SDM.
- **Attributes**:
  - `model_id` (str): Unique identifier (e.g., `rf_species_2024`).
  - `algorithm` (str): "RandomForest", "Bioclim", "TargetGroupLogisticRegression".
  - `species` (str): Target species.
  - `train_period` (str): "1970-2000" or "2005-2020".
  - `metrics` (dict): AUC, TSS, and standard deviations.
  - `file_path` (str): Path to serialized model (`.pkl`).

### Metric Record
Aggregated performance statistics.
- **Attributes**:
  - `species` (str).
  - `algorithm` (str).
  - `metric_name` (str): "AUC", "TSS".
  - `value` (float).
  - `cv_fold` (int): Fold number (1-5).
  - `data_sufficiency` (bool): True if records >= calculated $N_{min}$.

### Niche Stability Record
Represents the result of the niche stability test (FR-009).
- **Attributes**:
  - `species` (str).
  - `algorithm` (str).
  - `auc_hist_to_recent` (float): Performance of Historical Model on Recent Data.
  - `auc_recent_to_recent` (float): Performance of Recent Model on Recent Data.
  - `non_stationarity_metric` (float): $AUC_{hist\_to\_recent} - AUC_{recent\_to\_recent}$.
  - `p_value` (float): From permutation test.
  - `significance` (bool): True if p < 0.05.
  - `interpretation` (str): "Niche Stable" or "Niche Shift".

## Data Flow

1.  **Ingestion**: `download.py` fetches raw GBIF records -> `data/raw/occurrence_YYYY_YYYY.csv`.
2.  **Preprocessing**: `preprocess.py` reads raw CSV, filters by breeding month, thins spatially -> `data/processed/thinned_YYYY_YYYY.csv`.
3.  **Enrichment**: Climate values extracted from rasters and joined to occurrence points.
4.  **Training**: `train.py` reads processed data, splits spatially, trains models (Historical and Recent) -> `models/`.
5.  **Evaluation**: `evaluate.py` projects models, computes metrics, runs permutation tests -> `metrics/model_metrics.json`, `metrics/niche_stability.json`.

## Constraints

- **Spatial Thinning**: Minimum distance must be respected (computed dynamically, not hardcoded).
- **Data Sufficiency**: Species with < calculated $N_{min}$ records in the test period are excluded from aggregation.
- **Null Handling**: Occurrences with null climate values are dropped.
- **Niche Stability Logic**: The `non_stationarity_metric` is calculated as $AUC_{hist\_to\_recent} - AUC_{recent\_to\_recent}$. A significant negative value indicates niche shift.