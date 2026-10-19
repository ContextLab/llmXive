# Data Model: Predicting Species Distribution Shifts

## 1. Entity Relationship Overview
The model comprises five primary entities: `OccurrenceRecord`, `ClimateVariable`, `ModelArtifact`, `ModelMetrics`, and `DataSufficiency`. Relationships are anchored on spatial coordinates and temporal metadata.

```mermaid
erDiagram
    OccurrenceRecord ||--o{ ClimateVariable : "has"
    OccurrenceRecord ||--o{ ModelPrediction : "used_for"
    ModelArtifact ||--o{ ModelPrediction : "generates"
    ClimateRaster ||--o{ ClimateVariable : "contains"
    ModelArtifact ||--o{ ModelMetrics : "evaluated_by"
    ModelArtifact ||--o{ DataSufficiency : "checked_by"
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
| `download_timestamp` | datetime (ISO‑8601) | When the record was fetched (Constitution VI). |
| `breeding_season` | boolean | True if the record falls within the species‑specific breeding months. |
| `thinned` | boolean | True if the record survived spatial thinning. |
| `dataset_name` | string | Name of the original dataset (e.g., “GBIF”). |

### 2.2 ClimateVariable
| Field | Type | Description |
|-------|------|-------------|
| `occurrence_id` | string (FK → `OccurrenceRecord.id`) | Link to occurrence. |
| `variable_name` | string (e.g., `bio1`) | Bioclim variable name. |
| `value` | float | Extracted climate value. |
| `raster_source` | string (URL/identifier) | Provenance of the raster. |
| `year` | integer | Year of the climate data (e.g., 2000, 2050). |

### 2.3 ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `model_id` | UUID (string) | Unique model identifier. |
| `species` | string | Target species. |
| `algorithm` | string (`RF`, `Bioclim`, `MaxEnt`) | Algorithm used. |
| `train_period` | string (`1970-2000`) | Temporal window of training data. |
| `file_path` | string | Relative path under `models/`. |
| `checksum` | string (SHA‑256) | File integrity hash. |
| `hyperparameters` | JSON object | Algorithm‑specific settings. |
| `seed` | integer | Random seed used for reproducibility. |

### 2.4 ModelMetrics
| Field | Type | Description |
|-------|------|-------------|
| `metric_id` | UUID (string) | Unique identifier. |
| `model_id` | string (FK → `ModelArtifact.model_id`) | Associated model. |
| `test_set_period` | string (`2005-2020`) | Validation period. |
| `auc` | float (0 → 1) | Area Under the ROC Curve. |
| `tss` | float (‑1 → 1) | True Skill Statistic. |
| `threshold` | float | Probability cutoff used for TSS. |
| `sample_size` | integer | Number of validation records. |
| `status` | string (`PASS` / `INSUFFICIENT_DATA`) | Sufficiency flag (FR‑006). |
| `delta_suitability` | float | Mean suitability shift (2050 – 2005‑2020). |
| `p_value` | float (0 → 1) | From hierarchical bootstrap. |
| `effect_size` | float | Cohen’s h (expected = 0.50, source: Wikipedia). |
| `corrected_p_value` | float (0 → 1) | After Benjamini‑Hochberg correction. |

### 2.5 DataSufficiency
| Field | Type | Description |
|-------|------|-------------|
| `species` | string | Species name. |
| `period` | string (`1970-2000` or `2005-2020`) | Temporal window. |
| `recordCount` | integer | Number of records after thinning. |
| `status` | string (`SUFFICIENT` / `INSUFFICIENT_DATA`) | Flag per FR‑006. |
| `power_value` | float | Calculated power for detecting h = 0.50 (FR‑011). |

## 3. File Formats

| Artifact | Format | Validation |
|----------|--------|------------|
| Raw occurrence CSVs | UTF‑8, comma‑separated, Darwin Core fields | `contracts/occurrence.schema.yaml` |
| Processed features CSV | UTF‑8, comma‑separated (one row per thinned occurrence + 19 climate vars) | `contracts/occurrence_record.schema.yaml` |
| Climate rasters | GeoTIFF (LZW compressed) | `contracts/climate_raster.schema.yaml` |
| Model files | Pickle (`.pkl`) | `contracts/model_artifact.schema.yaml` |
| Metric JSONs | JSON | `contracts/model_metrics.schema.yaml` |
| Data sufficiency JSON | JSON | `contracts/data_sufficiency.schema.yaml` |
| Logging configuration | YAML (Python `logging.config.dictConfig`) | No schema required but must exist in `logs/`. |

## 4. Data Flow
1. **Download** (`code/download.py`) → `data/raw/` (occurrence CSVs, climate GeoTIFFs).  
2. **Preprocess** (`code/preprocess.py`) → `data/processed/features.csv` + `metrics/data_sufficiency.json`.  
3. **Train** (`code/train.py`) → `models/*.pkl`.  
4. **Evaluate** (`code/evaluate.py`) → `metrics/model_performance.json` + `results/summary_table.csv`.  
5. **Report** (`code/report.py`) → `reports/findings.md`.  

All intermediate files are immutable; new derivations receive fresh filenames and are logged with checksums (Constitution III).

---
