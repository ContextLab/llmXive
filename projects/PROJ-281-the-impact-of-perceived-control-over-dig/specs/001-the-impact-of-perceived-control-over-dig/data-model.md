# Data Model: The Impact of Perceived Control Over Digital Environments on Anxiety

## Overview
Defines immutable, version‑controlled data artifacts that flow through the pipeline while preserving the separation between text‑derived anxiety scores and metadata‑derived control proxies.

## Entity Schemas

### 1. `SocialPost` (Raw)
| Field | Type | Description |
|-------|------|-------------|
| `post_id` | string | Unique identifier (from source). |
| `text` | string | Tweet content. |
| `timestamp` | datetime (ISO‑8601) | Posting time. |
| `user_id` | string | Anonymized user identifier. |
| `filter_applied` *(optional)* | boolean | Flag indicating a content‑filter or edit flag; may be absent. |

*Stored as `data/raw/social_media.csv` (checksum recorded).*

### 2. `AnxietyScoreRecord`
| Field | Type | Description |
|-------|------|-------------|
| `post_id` | string | FK to `SocialPost`. |
| `anxiety_score` | float ∈[0,1] | Sum of anxiety‑related emotion probabilities. |
| `confidence_score` | float ∈[0,1] | Max class probability from the model. |
| `predicted_class` | string | Emotion class with highest probability. |
| `excluded` | boolean | True if `confidence_score` < 0.6. |

*Saved to `data/processed/scoring_results.csv`.*

### 3. `ControlProxyRecord`
| Field | Type | Description |
|-------|------|-------------|
| `post_id` | string | FK to `SocialPost`. |
| `filter_flag` | boolean | Derived from `filter_applied` (False if column missing). |
| `timestamp_regularity` | float ∈[0,1] | Normalized inverse‑std of inter‑post intervals per user. |
| `control_proxy` | float ∈[0,1] | Weighted combination (0.6 × `filter_flag` + 0.4 × `timestamp_regularity`). |

*Saved to `data/processed/proxy_results.csv`.*

### 4. `AnalysisResult`
| Field | Type | Description |
|-------|------|-------------|
| `post_id` | string | FK to `SocialPost`. |
| `anxiety_score` | float | From `AnxietyScoreRecord`. |
| `control_proxy` | float | From `ControlProxyRecord`. |
| `valid` | boolean | True if not excluded by confidence threshold. |

*Saved to `data/processed/final_analysis.csv`.*

### 5. `StatisticalSummary` (JSON)
Conforms to `contracts/analysis.schema.yaml` and includes:
- `correlation_method`
- `correlation_coefficient`
- `p_value`
- `is_significant`
- `normality_test_p_value`
- `sample_size`
- `confidence_threshold`

### 6. `CoverageReport` (JSON)
Tracks:
- total rows ingested,
- rows after language/gibberish filter,
- rows with valid anxiety scores,
- rows excluded by confidence,
- checksum verification status.

## Processing Flow
1. **Ingestion** → `SocialPost` → `data/raw/social_media.csv`  
2. **Anxiety Scoring** → `AnxietyScoreRecord` → `data/processed/scoring_results.csv`  
3. **Proxy Extraction** → `ControlProxyRecord` → `data/processed/proxy_results.csv`  
4. **Merge & Filter** → `AnalysisResult` → `data/processed/final_analysis.csv`  
5. **Statistical Test** → `StatisticalSummary` → `data/processed/analysis_results.json`  
6. **Coverage Report** → `data/processed/coverage_report.json`

All files are immutable after creation; any re‑run produces new versioned files with updated hashes.

---
