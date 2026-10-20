# Data Model: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Overview
The pipeline manipulates five logical data layers, each validated against a JSON/YAML schema in `contracts/`.

| Layer | Description | File Location | Schema |
|-------|-------------|---------------|--------|
| **Raw Dataset** | Unmodified download from OpenNeuro (Parquet) | `data/raw/ds000208.parquet` | `contracts/dataset.schema.yaml` |
| **Reward Availability Stub** | JSON indicating no reward dataset is available | `data/interim/reward_unavailable.json` | *inline schema validated by `validate.py`* |
| **Preprocessed Dataset** | Cleaned, outlier‑flagged, Z‑score normalized, aggregated per participant/condition | `data/processed/analysis_ready_ds000208.csv` | `contracts/dataset.schema.yaml` (extended) |
| **Outlier Log** | Per‑condition IQR thresholds and counts of flagged rows | `data/interim/outlier_log.json` | *description only* |
| **Design Branch** | Stores the chosen design type (`Between-Subjects`, `Repeated-Measures`) | `data/interim/design_branch.json` | *description only* |
| **Analysis Output** | Statistical results, FDR‑corrected p‑values, effect sizes, α‑sensitivity flags, **95 % confidence intervals** for effect size | `results/analysis_output.json` | `contracts/analysis_output.schema.yaml` |
| **Full Results Package** | Combines `analysis_output.json` with design metadata, phrasing checks, and outlier‑sensitivity summary | `results/analysis_results.json` | `contracts/analysis_results.schema.yaml` |
| **Metadata** | Checksum, download timestamp, citation for the raw dataset | `data/raw/metadata.json` | *description only* |
| **Citation File** | Human‑readable citation for the dataset | `data/raw/CITATION.md` | – |

## Entity Definitions

### 1. Raw Dataset Record
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Anonymized participant identifier. |
| `task` | string | Task name (e.g., `"cyberball"` or `"reward"`). **Optional**; present when the dataset includes multiple tasks. |
| `condition` | string | `"rejection"` or `"control"` (both must be present). |
| `reaction_time` | number (≥ 0) | RT in milliseconds. |
| `mood_rating` | number (1 – 7) | Self‑reported mood. |
| `age` | number (optional) | Age in years. |
| `gender` | string (optional) | `"male"`, `"female"` or `"other"`. |

### 2. Reward Availability Stub
```json
{
  "reward_dataset_available": false,
  "reason": "No open-access reward dataset with verified URL."
}
```
Used by downstream steps to skip reward‑related processing.

### 3. Preprocessed Record
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Same as raw. |
| `condition` | string | Same as raw. |
| `rt_normalized` | number | Z‑score of `reaction_time` within the condition. |
| `is_outlier` | boolean | `true` if flagged by IQR rule. |
| `rt_mean` | number | Mean of `rt_normalized` for the participant‑condition pair. |
| `mood_mean` | number | Mean of `mood_rating` for the participant‑condition pair. |
| `age` | number (optional) | Propagated from raw. |
| `gender` | string (optional) | Propagated from raw. |

### 4. Outlier Log (JSON)
```json
{
  "condition": "rejection",
  "iqr_lower": <number>,
  "iqr_upper": <number>,
  "flagged_count": <int>
}
```
One object per condition; stored in `data/interim/outlier_log.json`.

### 5. Design Branch (JSON)
```json
{
  "design_type": "Between-Subjects"  // or "Repeated-Measures"
}
```
Reflects the automatic selection (FR‑007).

### 6. Analysis Output – conforms to `contracts/analysis_output.schema.yaml`
| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string | `"One_Way_ANOVA"` (or `"Repeated_Measures_ANOVA"` when applicable). |
| `design_type` | string | `"Between-Subjects"` or `"Repeated-Measures"`. |
| `f_value` | number | F‑statistic. |
| `p_raw` | number (0‑1) | Unadjusted p‑value. |
| `p_fdr` | number (0‑1) | Benjamini‑Hochberg corrected p‑value (≥ `p_raw`). |
| `effect_size` | number | Eta‑squared. |
| `confidence_interval` | array[2] | 95 % CI for `effect_size`. |
| `alpha_sensitivity` | object | Keys `"0.01"`, `"0.05"`, `"0.1"` → booleans indicating significance. |

### 7. Full Results Package – conforms to `contracts/analysis_results.schema.yaml`
| Field | Type | Description |
|-------|------|-------------|
| `design_type` | string | `"Between-Subjects"` or `"Repeated-Measures"` or `"Unavailable"`. |
| `main_test` | object | Mirrors `analysis_output.json` (F, p_raw, p_fdr, effect size, CI). |
| `sensitivity_analysis` | array | Results of α sweep (α = 0.01, 0.05, 0.1). |
| `outlier_sensitivity` | object | Differences in statistics with vs. without outliers (from T010). |
| `limitations` | object | Flags for required phrasing constraints. |

## Data Flow
1. **Ingestion** (`code/ingest.py`) → `data/raw/ds000208.parquet`, `metadata.json`, `CITATION.md`.  
2. **Reward stub** (`code/ingest.py`) → `data/interim/reward_unavailable.json`.  
3. **Validation** (`code/validate.py`) → `data/interim/ingest_validation_report.json`.  
4. **Preprocessing** (`code/preprocess.py`) → `data/processed/analysis_ready_ds000208.csv`, `outlier_log.json`.  
5. **Analysis** (`code/analyze.py`) → `results/analysis_output.json`.  
6. **Packaging** (`code/report.py`) → `results/analysis_results.json` & `paper/report.md`.  

All intermediate files are immutable; any transformation writes a new file with documented provenance.

## Constraints
- **Memory**: Files must fit within 7 GB RAM; raw parquet is streamed/memory‑mapped.  
- **PII**: `participant_id` is anonymized; no personal data stored.  
- **Immutability**: Raw files never overwritten; checksums guarantee integrity.

---

