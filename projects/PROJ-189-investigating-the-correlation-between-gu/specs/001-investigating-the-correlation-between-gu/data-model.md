# Data Model: Gut Microbiome and Cognitive Decline Analysis

## 1. Entity Definitions

### 1.1 Sample (Participant)
| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | string | Unique AGP sample identifier. |
| `participant_id` | string | Identifier that links microbiome and cognition within the paired dataset. |
| `age` | integer (≥ 60) | Age at assessment. |
| `sex` | enum(`Male`, `Female`, `Other`, `Unknown`) | Self‑reported sex. |
| `bmi` | number (≥ 0) | Body‑mass index (imputed if missing). |
| `is_missing_bmi` | boolean | `True` if BMI was imputed via MICE. |
| `cognitive_score` | number | Continuous cognitive performance metric (e.g., HRS memory score). |
| `age_group` | enum(`60-69`, `70-79`, `80+`) | Derived age bin for stratified splitting. |
| `education_years` | integer (≥ 0) | Years of formal education (covariate). |
| `genera_abundance` | object (key=genus name, value=relative abundance [0‑1]) | Raw (or rarefied) abundance values per genus. |
| `genera_clr` | object (key=genus name, value=CLR‑transformed value) | CLR‑transformed abundances. |

### 1.2 ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string (UUID) | Unique identifier for the saved model. |
| `hyperparameters` | object | `n_estimators`, `max_depth`, `random_state`. |
| `performance` | object | `r2_train`, `r2_test`, `rmse_test`. |
| `null_distribution` | object | `n_permutations`, `r2_null_95th_percentile`, `r2_null_adjusted_threshold`, `is_significant`. |
| `vif_check` | object | `threshold` (5) and list of flagged taxon pairs with VIF values. |
| `collinearity_report` | object | Pearson |r| threshold (0.9) and list of flagged taxon pairs after CLR. |
| `shap_analysis` | object | Top‑20 genera with `mean_abs_shap`. |
| `timestamp` | string (ISO‑8601) | Creation time of the artifact. |

## 2. Data Flow
1. **Raw Input**: `agp.parquet` (downloaded from Qiita/EBI) and `paired_dataset.parquet` (user‑provided).  
2. **Provenance**: `observed_checksums.json` compared to `expected_checksums.json`.  
3. **Intermediate**: `paired_dataset_age60.parquet` (filter to age ≥ 60) – **only created if ≥ 200 participants**; otherwise the pipeline aborts.  
4. **Processed**: `clr_normalized.parquet`, `imputed.parquet` (if step 3 succeeded).  
5. **Outputs** (validated against contracts):  
   - `correlations.json` (Spearman results)  
   - `model.json` (Random Forest artifact)  
   - `sensitivity.json` (rarefaction sweep)  
   - `unified_results.json` (covers dataset metadata, correlation, model)  
   - `summary.md` (human‑readable report).  

All files reside under `data/`; their SHA‑256 hashes are recorded in `state/projects/...yaml`.

## 3. Constraints & Validation
- **Missing Data**: Rows missing `cognitive_score` or `age` are dropped before any analysis.  
- **Zero Inflation**: Handled by rarefaction + CLR; no explicit zero‑inflation model needed.  
- **Memory**: If `paired_dataset_age60.parquet` would exceed 6 GB RAM, the pipeline automatically limits to the top‑most abundant taxa (Task T011).  
- **Size Requirement**: Pipeline aborts with error if the filtered dataset contains **< 200 participants** (satisfies SC‑001).  
- **Checksum Validation**: Must succeed before any downstream step (Task T001).  
- **Schema Conformance**: Every result file is validated against its respective schema in `contracts/` by the CI test suite.  

---



