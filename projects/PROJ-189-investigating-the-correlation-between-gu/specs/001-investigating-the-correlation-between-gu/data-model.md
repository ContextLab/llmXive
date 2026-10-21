# Data Model: Gut Microbiome and Cognitive Decline Analysis

## 1. Entity Definitions

### 1.1 Sample (Participant)
| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | string | Unique identifier for the microbiome sample (AGP). |
| `participant_id` | string | Shared ID used to merge AGP & HRS (must exist in both). |
| `age` | integer (≥ 60) | Age at HRS assessment. |
| `sex` | enum(`Male`, `Female`, `Other`, `Unknown`) | Self‑reported sex. |
| `bmi` | number (≥ 0) | Body‑mass index; may be imputed. |
| `is_missing_bmi` | boolean | `True` if BMI was imputed via MICE. |
| `cognitive_score` | number | Continuous cognitive performance metric from HRS. |
| `age_group` | enum(`60-69`, `70-79`, `80+`) | Derived age bin for stratified splitting. |

### 1.2 Taxon (Genus)
| Field | Type | Description |
|-------|------|-------------|
| `genus_name` | string | Microbial genus name. |
| `raw_count` | integer | Raw read count before rarefaction. |
| `rarefied_count` | integer | Count after rarefaction to `min_depth`. |
| `clr_value` | number | Centered log‑ratio transformed abundance (used for modelling). |
| `vif` | number (optional) | VIF computed on CLR matrix (flagged if > 5). |

### 1.3 ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string (UUID) | Unique identifier for the saved model. |
| `hyperparameters` | object | `n_estimators`, `max_depth`, `random_state`. |
| `performance` | object | `r2_train`, `r2_test`, `rmse_test`. |
| `null_distribution` | object | `n_permutations`, `r2_null_95th_percentile`, `adjusted_threshold`, `is_significant`. |
| `vif_check` | object | `threshold` (5) and list of flagged taxon pairs with VIF values. |
| `shap_analysis` | object | List of top‑20 genera with `mean_abs_shap`. |
| `timestamp` | string (ISO‑8601) | Creation time of the artifact. |

## 2. Data Flow
1. **Raw Input**: `agp.parquet` (taxa counts) + `hrs.parquet` (metadata).  
2. **Intermediate**: `merged_age60.parquet` (inner join, age filter).  
3. **Processed**: `clr_normalized.parquet` (CLR matrix) + `imputed.parquet` (BMI imputed).  
4. **Outputs** (validated against `contracts/results.schema.yaml`):  
   - `correlations.json` (correlation block)  
   - `model_metrics.json` (model block)  
   - `sensitivity.json` (sensitivity block)  
   - `summary.md` (human‑readable report)  

All files are stored under `data/` and are version‑hashed in the project state yaml.

## 3. Constraints & Validation
- **Missing Data**: Rows missing `cognitive_score` or `age` are dropped before any analysis.  
- **Zero Inflation**: Handled by rarefaction + CLR; no direct log of zeros.  
- **Memory**: If `merged_age60.parquet` exceeds 6 GB, the pipeline caps taxa to the top‑200 by mean abundance.  
- **Linkage**: Pipeline aborts with error if `len(overlap) < 500`.  
- **Checksums**: Every raw file’s SHA‑256 checksum is recorded in `state/projects/...yaml` and verified (Task T001).  

---
