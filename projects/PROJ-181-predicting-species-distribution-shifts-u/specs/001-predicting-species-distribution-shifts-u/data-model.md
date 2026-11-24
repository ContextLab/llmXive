# Data Model: Predicting Species Distribution Shifts

## 1. Entity Relationship Overview
The model comprises six primary entities: `OccurrenceRecord`, `ClimateVariable`, `BiasLayer`, `ModelArtifact`, `ModelMetrics`, and `DataSufficiency`. Relationships are anchored on spatial coordinates and temporal metadata.

```mermaid
erDiagram
    OccurrenceRecord ||--o{ ClimateVariable : "has"
    OccurrenceRecord ||--o{ ModelPrediction : "used_for"
    ModelArtifact ||--o{ ModelPrediction : "generates"
    ClimateRaster ||--o{ ClimateVariable : "contains"
    ModelArtifact ||--o{ ModelMetrics : "evaluated_by"
    ModelArtifact ||--o{ DataSufficiency : "checked_by"
    BiasLayer ||--o{ OccurrenceRecord : "informs"
```

## 2. Data Entities

### 2.1 OccurrenceRecord
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID (string) | Unique identifier generated during preprocessing. |
| `species_name` | string | Latin name of the bird species. |
| `latitude` | float | WGS84 latitude (‑90 → 90). |
| `longitude` | float | WGS84 longitude (‑180 → 180). |
| `event_date` | date (YYYY‑MM‑DD) | Observation date. |
| `source_id` | string | Original GBIF/eBird identifier. |
| `download_timestamp` | datetime (ISO‑8601) | Timestamp of data download (Constitution VI). |
| `breeding_season` | boolean | True if record falls within species‑specific breeding months. |
| `thinned` | boolean | True if the record survived spatial thinning. |
| `bias_weight` | float | Weight from the bias‑layer raster (higher where observer effort is higher). |
| `dataset_name` | string | Name of the original dataset (e.g., “GBIF”). |

### 2.2 ClimateVariable
| Field | Type | Description |
|-------|------|-------------|
| `occurrence_id` | string (FK → `OccurrenceRecord.id`) | Link to occurrence. |
| `variable_name` | string (e.g., `bio1`) | Bioclim variable name. |
| `value` | float | Extracted climate value. |
| `raster_source` | string (URL/identifier) | Provenance of the raster. |
| `year` | integer | Year of the climate data (e.g., 2000, 2050). |

### 2.3 BiasLayer
| Field | Type | Description |
|-------|------|-------------|
| `layer_id` | string | Unique identifier. |
| `description` | string | Kernel‑density raster of observation effort used for bias‑corrected background sampling. |
| `period` | string | Either `historic` (1970‑2000) **or** `recent` (2005‑2020). |
| `file_path` | string | Relative path to the raster file. |
| `checksum_sha256` | string | SHA‑256 checksum for integrity verification. |

### 2.4 ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `modelID` | string | Unique model identifier (matches `model_artifact.schema.yaml`). |
| `species` | string | Target species name. |
| `algorithm` | string | Model algorithm (e.g., `RF`, `Bioclim`, `MaxEnt`). |
| `trainPeriod` | string | Temporal window of training data (e.g., `1970-2000`). |
| `testPeriod` | string | Temporal window of validation data (`2005-2020`). |
| `auc` | number | Area Under the ROC Curve (recorded at training time). |
| `tss` | number | True Skill Statistic (recorded at training time). |
| `filePath` | string | Relative path under `models/`. |
| `seed` | integer | Random seed for reproducibility. |
| `checksum` | string | SHA‑256 hash of the model file. |

### 2.5 ModelMetrics
| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string (FK → `ModelArtifact.modelID`) | Associated model. |
| `species` | string | Target species. |
| `algorithm` | string (`RF`, `Bioclim`, `MaxEnt`) | Algorithm used. |
| `test_set_period` | string (`2005-2020`) | Validation period. |
| `auc` | number (0 → 1) | Area Under the ROC Curve (recent test set). |
| `tss` | number (‑1 → 1) | True Skill Statistic (recent test set). |
| `threshold` | number | Probability cutoff used for TSS calculation. |
| `sample_size` | integer | Number of validation records. |
| `status` | string (`PASS` / `INSUFFICIENT_DATA`) | Sufficiency flag per FR‑018. |
| `delta_auc` | number | Calibrated difference between historic CV AUC and recent test‑set AUC. |
| `calibration_brier` | number | Brier score on recent test set. |
| `mop_proportion` | number | Proportion of future pixels within analogous climate space (MESS). |
| `composite_stability` | number | Weighted combination of calibrated ΔAUC and MOP proportion. |
| `p_value` | number (0 → 1) | P‑value from hierarchical bootstrap (FR‑018). |
| `effect_size` | number | Effect size (Cohen’s h = 0.50, source verified). |
| `corrected_p_value` | number (0 → 1) | After Benjamini‑Hochberg correction (FR‑009). |

### 2.6 DataSufficiency
| Field | Type | Description |
|-------|------|-------------|
| `species` | string | Species name. |
| `period` | string (`1970-2000` or `2005-2020`) | Temporal window. |
| `recordCount` | integer | Number of records after thinning. |
| `status` | string (`SUFFICIENT` / `INSUFFICIENT_DATA`) | Flag per FR‑018. |
| `power_value` | number | Calculated power to detect a minimum AUC difference of 0.05 (source: statistical power analysis). |

## 3. File Formats

| Artifact | Format | Validation |
|----------|--------|------------|
| Raw occurrence CSVs | UTF‑8, comma‑separated, Darwin Core fields | `contracts/occurrence.schema.yaml` |
| Processed features CSV | UTF‑8, comma‑separated (one row per thinned occurrence + selected climate vars) | `contracts/occurrence_record.schema.yaml` |
| Climate rasters | GeoTIFF (LZW compressed) | `contracts/climate_raster.schema.yaml` |
| Bias layer raster | GeoTIFF | `contracts/climate_raster.schema.yaml` (re‑used for metadata) |
| Model files | Pickle (`.pkl`) | `contracts/model_artifact.schema.yaml` |
| Metric JSONs | JSON | `contracts/model_metrics.schema.yaml` |
| Data sufficiency JSON | JSON | `contracts/data_sufficiency.schema.yaml` |
| Data acquisition completeness JSON | JSON | No separate schema required (SC‑004 metric). |
| Logging counts YAML | YAML (`logs/preprocess_counts.yaml`) – a **list of objects** each matching `contracts/log_counts.schema.yaml` | `contracts/log_counts.schema.yaml` |
| Logging configuration | YAML (`logs/logging_config.yaml`) | Stored as `logs/logging_config.yaml`; validated by implementation. |

## 4. Data Flow
1. **Download** (`code/download.py`) → `data/raw/` (occurrence CSVs, climate GeoTIFFs).  
2. **Preprocess** (`code/preprocess.py`) → `data/processed/features.csv`, `data/processed/bias_layer_historic.tif`, `data/processed/bias_layer_recent.tif`, `metrics/data_sufficiency.json`, `metrics/data_acquisition_completeness.json`, `logs/preprocess_counts.yaml`.  
3. **Train** (`code/train.py`) → `models/*.pkl`.  
4. **Evaluate & Project** (`code/evaluate.py`) → `metrics/model_performance.json`, `results/summary_table.csv`, `logs/evaluate.log`.  
5. **Report** (`code/report.py`) → `reports/findings.md`.  

All intermediate files are immutable; each transformation writes a new file with a documented checksum and provenance (Constitution III).

---



