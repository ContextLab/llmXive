# Data Model: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Overview
The pipeline manipulates five logical data layers, each validated against a JSON/YAML schema in `contracts/`.

| Layer | Description | File Location | Schema |
|-------|-------------|---------------|--------|
| **Raw Dataset (Rejection)** | Unmodified download from OpenNeuro (Parquet) | `data/raw/ds000208.parquet` | `contracts/dataset.schema.yaml` |
| **Raw Dataset (Reward)** | Unmodified download from OpenNeuro (Parquet) | `data/raw/ds003392.parquet` | `contracts/dataset.schema.yaml` |
| **Preprocessed Dataset (Rejection)** | Cleaned, outlier‑flagged, Z‑score normalized, optional covariates retained, and aggregated per participant/condition | `data/processed/analysis_ready_ds000208.csv` | `contracts/dataset.schema.yaml` (extended with `rt_normalized`, `is_outlier`, `rt_mean`, `mood_mean`, optional `age`, `gender`) |
| **Preprocessed Dataset (Reward)** | Same processing as the rejection file, yielding per‑participant/condition aggregates | `data/processed/analysis_ready_ds003392.csv` | `contracts/dataset.schema.yaml` (extended as above) |
| **Merged Analysis Ready** | Merged table joining the two preprocessed files on `participant_id` (and condition where applicable) for Mixed ANOVA; if no overlap, only the rejection file is used. | `data/processed/merged_analysis_ready.csv` | `contracts/dataset.schema.yaml` (includes `design_type` field) |
| **Analysis Output** | Statistical results, FDR‑corrected p‑values, and sensitivity flags | `results/analysis_output.json` | `contracts/analysis_output.schema.yaml` |
| **Full Results Package** | Combines `analysis_output.json` with design metadata and phrasing checks | `results/analysis_results.json` | `contracts/analysis_results.schema.yaml` |
| **Metadata** | Contains checksum entries for both raw datasets, timestamps, and citation information. | `data/raw/metadata.json` | *see description below* |
| **Overlap Report** | Lists matched and unmatched participant IDs and a boolean `is_single_cohort`. | `data/interim/overlap_report.json` | *see description below* |
| **Design Branch** | Stores the chosen design type (`Within-Subjects` or `Between-Subjects`). | `data/interim/design_branch.json` | *see description below* |

## Entity Definitions

### 1. Raw Dataset Record
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Anonymized participant identifier. |
| `task` | string | Fixed value `"cyberball"` for ds000208, `"reward"` for ds003392. |
| `condition` | string | `"rejection"` / `"control"` (ds000208) or `"reward"` (ds003392). |
| `reaction_time` | number (≥ 0) | RT in milliseconds. |
| `mood_rating` | number (1 – 7) | Self‑reported mood. |
| `timestamp` | string (optional) | Event timestamp, if present. |
| `age` | number (optional) | Age in years (if available). |
| `gender` | string (optional) | `"male"`, `"female"` or `"other"` (if available). |

### 2. Preprocessed Record
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Same as raw. |
| `condition` | string | Same as raw. |
| `rt_normalized` | number | Z‑score of `reaction_time` within the condition. |
| `is_outlier` | boolean | `true` if flagged by IQR rule. |
| `rt_mean` | number | Mean of `rt_normalized` for the participant‑condition pair. |
| `mood_mean` | number | Mean of `mood_rating` for the participant‑condition pair. |
| `age` | number (optional) | Propagated from raw if present. |
| `gender` | string (optional) | Propagated from raw if present. |

### 3. Merged Analysis Ready Record
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Same as raw. |
| `condition_rejection` | string | `"rejection"` or `"control"` (from ds000208). |
| `condition_reward` | string | `"reward"` or `"no_reward"` (derived). |
| `rt_mean_rejection` | number | From preprocessed rejection file. |
| `mood_mean_rejection` | number | From preprocessed rejection file. |
| `rt_mean_reward` | number (optional) | From preprocessed reward file, if matched. |
| `mood_mean_reward` | number (optional) | From preprocessed reward file, if matched. |
| `design_type` | string | `"Within-Subjects"` or `"Between-Subjects"` (derived from overlap report). |

### 4. Analysis Output (per outcome)
| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string | `"One_Way_ANOVA"` (or `"Paired_T_Test"` if fallback). |
| `design_type` | string | `"Within-Subjects"` or `"Between-Subjects"`. |
| `f_value` | number | F‑statistic (or t‑value for paired test). |
| `p_raw` | number (0‑1) | Unadjusted p‑value. |
| `p_fdr` | number (0‑1) | Benjamini‑Hochberg corrected p‑value (must be ≥ `p_raw`). |
| `effect_size` | number | Effect size (e.g., eta‑squared or Cohen’s d). |
| `alpha_sensitivity` | object | Keys `"0.01"`, `"0.05"`, `"0.1"` → boolean significance at each α. |

### 5. Analysis Results Package
| Field | Type | Description |
|-------|------|-------------|
| `design_type` | string | `"Within-Subjects"` or `"Between-Subjects"` or `"Unavailable"`. |
| `main_test` | object | Contains `f_statistic`, `p_raw`, `p_fdr`, `effect_size`, `confidence_interval`. |
| `sensitivity_analysis` | array of objects | Each with `alpha` (0.01/0.05/0.1) and `power_at_alpha`. |
| `limitations` | object | `contains_associational` (must be `true`), `modulation_claim_valid` (false when reward modulation cannot be tested). |

### 6. Metadata (raw data provenance)
| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | `"ds000208"` or `"ds003392"`. |
| `checksum_sha256` | string | SHA‑256 hash of the downloaded parquet file. |
| `download_timestamp` | string (ISO‑8601) | When the file was fetched. |
| `citation` | string | Full citation text for the dataset (written to `CITATION.md`). |

### 7. Overlap Report
| Field | Type | Description |
|-------|------|-------------|
| `matched_ids` | array[string] | Participant IDs present in **both** datasets. |
| `unmatched_ids` | array[string] | IDs present in only one dataset. |
| `is_single_cohort` | boolean | `true` if every participant appears in both datasets. |

### 8. Design Branch
| Field | Type | Description |
|-------|------|-------------|
| `design_type` | string | `"Within-Subjects"` or `"Between-Subjects"` (derived from `is_single_cohort`). |

## Data Flow
1. **Ingestion** (`code/ingest.py`) → `data/raw/ds000208.parquet` & `data/raw/ds003392.parquet` (checksums recorded, `metadata.json` & `CITATION.md` generated).  
2. **Validation** (`T003`‑`T007`) → schema checks, overlap report, design branch.  
3. **Preprocessing** (`code/preprocess.py`) → `data/processed/analysis_ready_*.csv`, `outlier_log.json`, `features_*.csv`.  
4. **Merging** (`code/analyze.py`) → `data/processed/merged_analysis_ready.csv` (if Within‑Subjects).  
5. **Analysis** (`code/analyze.py`) → `results/analysis_output.json`.  
6. **Packaging** (`code/report.py`) → `results/analysis_results.json` & `paper/report.md`.  

All intermediate files are immutable; any transformation writes a new file with documented provenance.

## Constraints
- **Memory**: All files must fit within 7 GB RAM; streaming is enabled for raw parquet if needed.  
- **PII**: `participant_id` is anonymized; no personal data is stored.  
- **Immutability**: Raw files never overwritten; checksums guarantee integrity.

---



