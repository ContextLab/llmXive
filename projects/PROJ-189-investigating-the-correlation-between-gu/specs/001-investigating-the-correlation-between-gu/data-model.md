# Data Model: Gut Microbiome and Cognitive Decline Analysis

## 1. Entity Definitions

### 1.1 Sample (Participant)
| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | string | Unique AGP sample identifier. |
| `participant_id` | string | Shared ID used to merge AGP & HRS. |
| `age` | integer (≥ 60) | Age at HRS assessment. |
| `sex` | enum(`Male`, `Female`, `Other`, `Unknown`) | Self‑reported sex. |
| `bmi` | number (≥ 0) | Body‑mass index (imputed if missing). |
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
| `vif` | number (optional) | Variance Inflation Factor; flagged if > 5 (pre‑CLR). |

### 1.3 ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string (UUID) | Unique identifier for the saved model. |
| `hyperparameters` | object | `n_estimators`, `max_depth`, `random_state`. |
| `performance` | object | `r2_train`, `r2_test`, `rmse_test`. |
| `null_distribution` | object | `n_permutations`, `r2_null_95th_percentile`, `r2_null_adjusted_threshold`, `is_significant`. |
| `vif_check` | object | `threshold` (5) and list of flagged taxon pairs with VIF values. |
| `collinearity_report` | object | Pearson |r| > 0.9 pairs after CLR. |
| `shap_analysis` | object | List of top‑20 genera with `mean_abs_shap`. |
| `timestamp` | string (ISO‑8601) | Creation time of the artifact. |

## 2. Data Flow
1. **Raw Input**: `agp.parquet`, `hrs.parquet`, `bmi.csv`.  
2. **Provenance**: `observed_checksums.json` compared to `expected_checksums.json`.  
3. **Intermediate**: `merged_age60.parquet` (inner join, age filter, VIF exclusion).  
4. **Processed**: `clr_normalized.parquet` (rarefied + CLR), `imputed.parquet` (BMI imputed).  
5. **Outputs** (validated against contracts):
   - `correlations.json` (correlation block)  
   - `model.json` (model block)  
   - `sensitivity.json` (sensitivity block)  
   - `unified_results.json` (covers dataset, correlation, model)  
   - `summary.md` (human‑readable report)  

All files reside under `data/` and their SHA‑256 hashes are recorded in `state/projects/...yaml`.

## 3. Constraints & Validation
- **Missing Data**: Rows missing `cognitive_score` or `age` are dropped before any analysis.  
- **Zero Inflation**: Handled by rarefaction + CLR; no direct log of zeros.  
- **Memory**: If `merged_age60.parquet` exceeds 6 GB RAM, the pipeline automatically limits taxa to the top‑200 by mean abundance (Task T011).  
- **Linkage**: Pipeline aborts with error if `len(overlap) < 500` (fatal coverage gap).  
- **Checksum Validation**: `01_download_and_provenance.py` must succeed before any downstream step.  
- **Schema Conformance**: Every result file is validated against its respective schema in `contracts/` by the CI test suite.  

---
