# Data Model: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

## Overview
The data model defines the schema for raw, processed, and analysis artifacts. All scripts read/write data conforming to the JSON/YAML contracts in `contracts/`.

## Entity Definitions

### 1. MotionFeature
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `feature_type` | string | `"latency"` | `"smoothness"` | `"lead_time"` | Enum, required |
| `value` | float | Numeric measurement | ≥ 0 |
| `unit` | string | `"ms"` or `"dimensionless"` | Required |
| `source_dataset` | string | Name of raw dataset or `"synthetic"` | Non‑empty |
| `participant_id` | string | UUID linking to agency score | UUID format |

### 2. AgencyScore
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `participant_id` | string | UUID | UUID format |
| `scale_items` | array[int] | Likert responses (1‑7) | Length ≥ 3 |
| `aggregated_score` | float | Continuous 0‑100 | 0 ≤ value ≤ 100 |
| `instrument_name` | string | Name of questionnaire | Non‑empty |
| `validity_flag` | boolean | True if DOI, ≥10 citations **and** Cronbach's α ≥ 0.70 (FR‑013) | Required |

### 3. Covariate (optional)
| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | e.g., `"age"`, `"vr_experience"` |
| `value` | float | Numeric covariate value |
| `participant_id` | string | UUID |

### 4. AnalysisResult
| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `model_type` | string | `"regression"` | `"ridge"` | `"random_forest"` | Enum |
| `feature_importance` | map[string, float] | Importance scores (≥ 0); for OLS/Ridge this is absolute coefficient magnitude | Sum ≈ 1 for RF |
| `statistical_significance` | map[string, float] | Corrected p‑values (0‑1) | Required |
| `cross_validation_metrics` | map[string, float] | `r2_mean`, `r2_std`, `rmse_mean` | Required |
| `vif_scores` | map[string, float] | VIF per predictor (≥ 1) | Required |
| `covariate_importance` | map[string, float] | Importance of any optional covariates included in the models | Optional |
| `power_analysis` | object | `detectable_f2`, `power`, `n_complete`, `sc001_pass`, `power_pass` (from T016) | Required |
| `correlation_checks` | object | Pearson & partial correlations for lead‑time independence (methodology‑41f9ceb3) | Required |
| `warnings` | array[string] | Runtime warnings (e.g., high VIF, low variance, lead‑time omitted) | Optional |

## Data Flow
1. **Raw Acquisition** → `data/raw/` (CSV/Parquet).  
2. **Download Status** → `data/raw/download_status.json` (contains `instrument_valid`, `variables_present`, `use_synthetic`).  
3. **Synthetic Generation** → `data/raw/synthetic_data.csv`.  
4. **Pre‑processing** → `data/processed/analysis_ready.csv` (cleaned, standardized; conforms to `contracts/dataset.schema.yaml`).  
5. **VIF Report** → `data/processed/vif_report.json` (includes `vif_pass`).  
6. **Power Analysis Config** → `data/processed/modeling_config.json` (includes `effective_n`, `detectable_f2`, `power`, `sc001_pass`, `power_pass`).  
7. **Model Metrics** → `data/processed/model_metrics.json` (conforms to `contracts/analysis_output.schema.yaml`).  
8. **Visualization Report** → `data/processed/visualization_report.json` (average reviewer rating).  
9. **Figures** → `data/processed/figures/` (PNG).  

## Constraints & Validations
- **Missing Values**: Rows with any missing motion or agency fields are dropped (US‑1).  
- **Collinearity**: If any VIF ≥ 5, the offending predictor is excluded from OLS; Ridge still runs; `vif_pass` recorded.  
- **Outcome Variance**: If `np.var(aggregated_score) < 1e-3`, a warning is logged.  
- **Instrument Validity**: Only datasets where `validity_flag == true` are allowed for primary analysis (FR‑009).  
- **Sample‑size Gate**: `modeling_config.json` must contain `"sc001_pass": true` (≥ 100 complete observations); otherwise a warning is emitted but processing continues.  
- **Power Gate**: `modeling_config.json` must contain `"power_pass": true` (power ≥ 0.80); otherwise a warning is emitted.  

All artifacts are version‑hashed and listed in `state/projects/PROJ-531-the-impact-of-visual-motion-on-perceived.yaml` per the constitution.
